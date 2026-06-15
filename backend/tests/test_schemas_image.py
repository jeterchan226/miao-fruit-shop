import pytest
from pydantic import ValidationError

from app.schemas.image import ImageRegister, ImageReorderItem, SignedUrlRequest


def test_signed_url_request_requires_filename_and_content_type():
    s = SignedUrlRequest(filename="photo.jpg", content_type="image/jpeg")
    assert s.filename == "photo.jpg"


def test_signed_url_request_rejects_unknown_content_type():
    with pytest.raises(ValidationError):
        SignedUrlRequest(filename="photo.pdf", content_type="application/pdf")


def test_image_register_default_sort_order():
    r = ImageRegister(url="https://storage.googleapis.com/bucket/img.jpg")
    assert r.sort_order == 0


def test_reorder_item_has_id_and_sort_order():
    item = ImageReorderItem(id=3, sort_order=1)
    assert item.id == 3
