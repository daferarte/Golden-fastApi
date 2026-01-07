# app/api/v1/tts.py
from typing import Optional
import io
import shutil
import subprocess
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import (
    StreamingResponse,
    JSONResponse,
    PlainTextResponse,
    HTMLResponse,
)

from fastapi import Depends
from app.api import deps

router = APIRouter()


# Detectar binarios disponibles (macOS: 'espeak', Linux: 'espeak-ng')
ESPEAK_CMD = shutil.which("espeak-ng") or shutil.which("espeak")
FFMPEG_CMD = shutil.which("ffmpeg")


def _ensure_tools(fmt: str):
    if not ESPEAK_CMD:
        raise HTTPException(status_code=500, detail="No se encontró 'espeak' ni 'espeak-ng' en PATH")
    if fmt == "mp3" and not FFMPEG_CMD:
        raise HTTPException(status_code=500, detail="No se encontró 'ffmpeg' en PATH")


def _synthesize_wav_bytes(text: str, lang: str, pitch: int, rate: int) -> bytes:
    """
    Genera audio WAV en memoria usando espeak/espeak-ng.
    macOS: 'espeak --stdout'
    Linux: 'espeak-ng --stdout' (o fallback '-w /dev/stdout')
    """
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Missing text")

    # Intento 1: --stdout
    try:
        return subprocess.check_output(
            [ESPEAK_CMD, f"-v{lang}", f"-p{pitch}", f"-s{rate}", "--stdout", text],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        # Fallback (algunas builds de espeak-ng)
        try:
            return subprocess.check_output(
                [ESPEAK_CMD, f"-v{lang}", f"-p{pitch}", f"-s{rate}", "-w", "/dev/stdout", text],
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e2:
            raise HTTPException(
                status_code=500,
                detail=f"espeak/espeak-ng error: {e2.output.decode(errors='ignore')}"
            )


def _wav_to_mp3_bytes(wav_bytes: bytes) -> bytes:
    """
    Convierte WAV→MP3 con ffmpeg por pipe. Forzamos '-f mp3' para salida en pipe:1.
    """
    try:
        proc = subprocess.Popen(
            [
                FFMPEG_CMD,
                "-loglevel", "error",  # menos ruido
                "-f", "wav",           # entrada es WAV desde stdin
                "-i", "pipe:0",
                "-ac", "1",            # mono
                "-ar", "22050",        # 22.05 kHz (típico en espeak)
                "-codec:a", "libmp3lame",
                "-b:a", "128k",
                "-f", "mp3",           # 👈 importante al escribir a pipe:1
                "pipe:1",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        mp3_bytes, err = proc.communicate(input=wav_bytes, timeout=30)
        if proc.returncode != 0:
            raise HTTPException(status_code=500, detail=f"ffmpeg error: {err.decode(errors='ignore')}")
        return mp3_bytes
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="No se encontró 'ffmpeg' en PATH")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MP3 conversion error: {e}")


@router.get("/", response_class=PlainTextResponse, tags=["TTS"])
def ping():
    return "TTS listo (espeak/espeak-ng + ffmpeg). Usa /api/v1/tts/say?text=Hola | /api/v1/tts/voices"


@router.get("/voices", tags=["TTS"])
def voices():
    """
    Devuelve la salida cruda de 'espeak --voices' o 'espeak-ng --voices'.
    """
    if not ESPEAK_CMD:
        raise HTTPException(status_code=500, detail="No se encontró 'espeak' ni 'espeak-ng' en PATH")
    try:
        out = subprocess.check_output([ESPEAK_CMD, "--voices"], text=True)
        return JSONResponse({"raw": out})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando voces: {e}")


@router.get("/say", tags=["TTS"])
def say(
    text: str = Query(..., min_length=1, description="Texto a sintetizar"),
    lang: str = Query("es", description="Voz/idioma: ej. es, es-la, en-us"),
    pitch: int = Query(50, ge=0, le=99, description="Tono 0-99"),
    rate: int = Query(175, ge=80, le=300, description="Velocidad palabras/min"),
    fmt: str = Query("mp3", pattern="^(mp3|wav)$", description="Formato de salida"),
):
    """
    Devuelve audio TTS (WAV o MP3) con 'Content-Disposition: inline' para que el navegador lo
    trate como reproducible y no como descarga.
    """
    _ensure_tools(fmt)
    wav_bytes = _synthesize_wav_bytes(text, lang, pitch, rate)

    if fmt == "wav":
        return StreamingResponse(
            io.BytesIO(wav_bytes),
            media_type="audio/wav",
            headers={"Content-Disposition": 'inline; filename="tts.wav"'}
        )

    mp3_bytes = _wav_to_mp3_bytes(wav_bytes)
    return StreamingResponse(
        io.BytesIO(mp3_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'inline; filename="tts.mp3"'}
    )


@router.get("/auto", response_class=HTMLResponse, tags=["TTS"])
def auto(
    text: str,
    lang: str = "es",
    pitch: int = 50,
    rate: int = 175,
    fmt: str = "mp3",
):
    """
    Página mínima que intenta AUTOREPRODUCIR el TTS del texto enviado.
    Si el navegador bloquea autoplay, muestra un botón para iniciar.
    Úsalo así:
      /api/v1/tts/auto?text=Hola%20Daniel&fmt=mp3
    """
    # Construimos la URL al endpoint de audio (/say)
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width,initial-scale=1" />
      <title>TTS Auto</title>
      <style>
        body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 2rem; }}
        #fallback {{ display:none; margin-top: 1rem; }}
        audio {{ display:block; width:100%; margin-top:1rem; }}
      </style>
    </head>
    <body>
      <h3>Reproduciendo TTS…</h3>
      <audio id="player" controls autoplay></audio>
      <div id="fallback">
        <p>Tu navegador bloqueó el autoplay. Pulsa para reproducir:</p>
        <button id="btn">Reproducir</button>
      </div>

      <script>
        const params = new URLSearchParams({{
          text: {text!r},
          lang: {lang!r},
          pitch: String({pitch}),
          rate: String({rate}),
          fmt: {fmt!r}
        }});
        // Consejo: algunos navegadores reproducen mejor si agregas un fragmento temporal
        const src = "/api/v1/tts/say?" + params.toString() + "#t=0.1";
        const player = document.getElementById("player");
        const fallback = document.getElementById("fallback");
        const btn = document.getElementById("btn");

        function tryPlay() {{
          player.src = src;
          // Intento 1: establecer src + autoplay en la etiqueta
          const p = player.play();
          if (p && p.catch) {{
            p.catch(() => {{
              // Intento 2: reproducción programática
              const a = new Audio(src);
              a.autoplay = true;
              a.play().catch(() => {{
                // Fallback visible
                fallback.style.display = "block";
              }});
            }});
          }}
        }}

        document.addEventListener("DOMContentLoaded", tryPlay);
        document.addEventListener("visibilitychange", () => {{
          if (document.visibilityState === "visible" && player.paused) tryPlay();
        }});
        if (btn) btn.addEventListener("click", tryPlay);
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
