# app/api/v1/uploads.py (o dentro de cliente.py)
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import re

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../back
MEDIA_ROOT = BASE_DIR / "media"
FOTOS_DIR = MEDIA_ROOT / "fotos"
FOTOS_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload-foto")
async def upload_foto(documento: str = Form(...), file: UploadFile = File(...)):
    # Validar doc y tipo
    safe_doc = re.sub(r"[^a-zA-Z0-9_\-]", "", documento)
    if not safe_doc:
        raise HTTPException(400, "Documento inválido.")
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(400, "Solo JPG o PNG.")

    ext = ".jpg" if file.content_type == "image/jpeg" else ".png"
    dest_path = FOTOS_DIR / f"{safe_doc}{ext}"

    # Guardar en disco por chunks
    try:
        with dest_path.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        raise HTTPException(500, f"No se pudo guardar la foto: {e}")

    # Ruta/URL que podrá usar el front
    ruta = f"/media/fotos/{safe_doc}{ext}"
    return {"ruta": ruta}
