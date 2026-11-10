import os
import uuid

from fastapi import UploadFile

from app.services.errors import InvalidInputError

# backend/uploads. app.main serves this same directory at /uploads, so both
# must come from here. They used to compute it separately and disagreed.
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

# Leading bytes of each format we accept, mapped to the extension we save it
# under. The browser's content type and the original filename are both chosen
# by the uploader, so neither decides what lands in a publicly served folder:
# trusting them let "page.html" sent as image/png be served back as HTML.
_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
)


def _detect_extension(head: bytes) -> str | None:
    for signature, ext in _SIGNATURES:
        if head.startswith(signature):
            return ext
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    return None


async def save_image_upload(file: UploadFile) -> str:
    """Persist an uploaded image to ``/uploads`` and return the public URL.

    Raises :class:`InvalidInputError` unless the bytes really are a PNG, JPEG,
    GIF or WebP under the size limit.
    """
    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise InvalidInputError("Image is larger than 5 MB.")
    ext = _detect_extension(contents[:16])
    if ext is None:
        raise InvalidInputError("Only PNG, JPEG, GIF or WebP images are allowed.")
    filename = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as buffer:
        buffer.write(contents)
    return f"/uploads/{filename}"
