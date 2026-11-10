"""Image uploads: only real images, named by us, served from where we save."""

import os

import pytest

from app.services import upload_service
from app.services.errors import InvalidInputError

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 16


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(upload_service, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


async def _upload(client, headers, name, content_type, body):
    return await client.post(
        "/api/admin/uploads",
        headers=headers,
        files={"file": (name, body, content_type)},
    )


@pytest.mark.parametrize("body, ext", [(PNG, ".png"), (JPEG, ".jpg"), (WEBP, ".webp")])
async def test_real_images_are_saved_under_our_extension(
    client, admin_headers, upload_dir, body, ext
):
    response = await _upload(client, admin_headers, "photo.anything", "image/png", body)

    assert response.status_code in (200, 201), response.text
    url = response.json()["url"]
    assert url.startswith("/uploads/") and url.endswith(ext)
    assert (upload_dir / os.path.basename(url)).read_bytes() == body


async def test_html_claiming_to_be_an_image_is_refused(client, admin_headers, upload_dir):
    response = await _upload(
        client, admin_headers, "page.html", "image/png", b"<script>alert(1)</script>"
    )

    assert response.status_code == 400
    assert list(upload_dir.iterdir()) == []


async def test_real_image_with_html_name_is_not_saved_as_html(
    client, admin_headers, upload_dir
):
    response = await _upload(client, admin_headers, "page.html", "text/html", PNG)

    assert response.json()["url"].endswith(".png")


async def test_oversized_upload_is_refused(client, admin_headers, upload_dir, monkeypatch):
    monkeypatch.setattr(upload_service, "MAX_UPLOAD_BYTES", 16)

    response = await _upload(client, admin_headers, "big.png", "image/png", PNG)

    assert response.status_code == 400
    assert list(upload_dir.iterdir()) == []


async def test_upload_requires_admin(client, upload_dir):
    response = await _upload(client, {}, "photo.png", "image/png", PNG)

    assert response.status_code == 401


def test_saved_files_are_in_the_directory_the_app_serves():
    from app.main import app

    mount = next(r for r in app.routes if getattr(r, "path", None) == "/uploads")

    assert os.path.abspath(mount.app.directory) == upload_service.UPLOAD_DIR


async def test_service_rejects_unknown_bytes_directly(upload_dir):
    class Fake:
        async def read(self, _size=-1):
            return b"not an image at all"

    with pytest.raises(InvalidInputError):
        await upload_service.save_image_upload(Fake())
