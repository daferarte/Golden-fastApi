# app/api/v1/uploads.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import re
from fastapi import Depends
from app.api import deps

router = APIRouter(prefix="/files", tags=["files"])

# __file__ = back/app/api/v1/uploads.py
# parents[0]=v1, [1]=api, [2]=app, [3]=back  -> queremos 'back'
BACK_DIR = Path(__file__).resolve().parents[3]
MEDIA_ROOT = BACK_DIR / "media"
FOTOS_DIR = MEDIA_ROOT / "fotos"
FOTOS_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload-foto")
async def upload_foto(documento: str = Form(...), file: UploadFile = File(...)):
    # Validar doc y tipo
    safe_doc = re.sub(r"[^a-zA-Z0-9_\-]", "", documento)
    if not safe_doc:
        raise HTTPException(status_code=400, detail="Documento inválido.")
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Solo JPG o PNG.")

    ext = ".jpg" if file.content_type == "image/jpeg" else ".png"
    dest_path = FOTOS_DIR / f"{safe_doc}{ext}"

    try:
        with dest_path.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo guardar la foto: {e}")

    # Ruta pública que usará el front para mostrar la imagen
    ruta = f"/media/fotos/{safe_doc}{ext}"
    return {"ruta": ruta}
