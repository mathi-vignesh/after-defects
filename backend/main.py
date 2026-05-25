from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import logging

from patcher import get_downgrade_options, patch_aep, PatchError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AE Downgrader API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 512 * 1024 * 1024


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    _validate_extension(file.filename)
    data = await file.read()
    _validate_size(data)
    try:
        result = get_downgrade_options(data)
    except PatchError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return result


@app.post("/downgrade")
async def downgrade(
    file: UploadFile = File(...),
    target_version_int: int = Form(...),   # frontend sends target byte as int
):
    _validate_extension(file.filename)
    data = await file.read()
    _validate_size(data)

    try:
        patched_bytes, info = patch_aep(data, target_version_int)
    except PatchError as e:
        raise HTTPException(status_code=422, detail=str(e))

    ext    = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "aep"
    base   = file.filename.rsplit(".", 1)[0]  if "." in file.filename else file.filename
    target = info["target_version_short"].replace(" ", "_")
    output = f"{base}_downgraded_to_{target}.{ext}"

    logger.info("Downgraded %s  %s → %s  (%d bytes)",
                file.filename, info["source_version_name"],
                info["target_version_name"], len(patched_bytes))

    return Response(
        content=patched_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{output}"',
            "X-Source-Version":    info["source_version_name"],
            "X-Target-Version":    info["target_version_name"],
            "X-Warnings":          " | ".join(info["warnings"]),
        },
    )


def _validate_extension(filename: str):
    if not filename:
        raise HTTPException(400, "No filename provided.")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("aep", "ffx"):
        raise HTTPException(400, f"Unsupported file type '.{ext}'. Only .aep and .ffx accepted.")


def _validate_size(data: bytes):
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(413, f"File too large. Max {MAX_FILE_SIZE // 1024 // 1024} MB.")
    if len(data) < 40:
        raise HTTPException(400, "File too small to be a valid AEP/FFX.")
