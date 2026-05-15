import os
import uuid

from fastapi import UploadFile

from app.services.errors import InvalidInputError

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_image_upload(file: UploadFile) -> str:
    """Persist an uploaded image to ``/uploads`` and return the public URL.

    Raises :class:`InvalidInputError` for non-image content types.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise InvalidInputError("Only image uploads are allowed.")
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    target_path = os.path.join(UPLOAD_DIR, filename)
    contents = await file.read()
    with open(target_path, "wb") as buffer:
        buffer.write(contents)
    return f"/uploads/{filename}"
