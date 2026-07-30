from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.product import Product
from app.repositories import product_repo
from app.schemas.image import ImageRegister, ImageReorderItem, ImageReorderRequest, SignedUrlRequest
from app.services import image_service


async def _seed(session: AsyncSession) -> Product:
    p = Product(slug="kanro", name="甘露梨", description="d", season="s")
    return await product_repo.add(session, p)


@patch("app.services.image_service.gcs_service")
def test_request_sign_returns_signed_url(mock_gcs):
    mock_gcs.enabled = True
    mock_gcs.sign_upload.return_value = {
        "signed_url": "https://signed", "public_url": "https://public/img.jpg"
    }
    result = image_service.request_sign(
        product_id=1, req=SignedUrlRequest(filename="img.jpg", content_type="image/jpeg")
    )
    assert result.signed_url == "https://signed"
    assert result.public_url == "https://public/img.jpg"


@patch("app.services.image_service.gcs_service")
def test_request_sign_raises_when_gcs_disabled(mock_gcs):
    from app.core.exceptions import AppError
    mock_gcs.enabled = False
    with pytest.raises(AppError):
        image_service.request_sign(
            product_id=1, req=SignedUrlRequest(filename="img.jpg", content_type="image/jpeg")
        )


async def test_register_image_saves_to_db(db_session: AsyncSession):
    p = await _seed(db_session)
    img = await image_service.register_image(
        db_session, p.id, ImageRegister(url="https://gcs/img.jpg", sort_order=0)
    )
    assert img.id is not None
    assert img.url == "https://gcs/img.jpg"


async def test_register_image_missing_product_raises(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await image_service.register_image(
            db_session, 999999, ImageRegister(url="https://gcs/img.jpg")
        )


@patch("app.services.image_service.gcs_service")
async def test_delete_image_removes_db_and_calls_gcs(mock_gcs, db_session: AsyncSession):
    mock_gcs.enabled = True
    p = await _seed(db_session)
    img = await image_service.register_image(
        db_session, p.id, ImageRegister(url="https://storage.googleapis.com/b/img.jpg")
    )
    await image_service.delete_image(db_session, img.id)
    mock_gcs.delete_object.assert_called_once_with(
        "https://storage.googleapis.com/b/img.jpg"
    )


async def test_delete_image_missing_raises(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await image_service.delete_image(db_session, 999999)


async def test_reorder_updates_sort_order(db_session: AsyncSession):
    p = await _seed(db_session)
    img_a = await image_service.register_image(
        db_session, p.id, ImageRegister(url="https://gcs/a.jpg", sort_order=0)
    )
    img_b = await image_service.register_image(
        db_session, p.id, ImageRegister(url="https://gcs/b.jpg", sort_order=1)
    )
    req = ImageReorderRequest(items=[
        ImageReorderItem(id=img_a.id, sort_order=1),
        ImageReorderItem(id=img_b.id, sort_order=0),
    ])
    result = await image_service.reorder_images(db_session, p.id, req)
    urls_in_order = [r.url for r in result]
    assert urls_in_order == ["https://gcs/b.jpg", "https://gcs/a.jpg"]


async def test_register_group_image_saves_with_flag(db_session: AsyncSession):
    p = await _seed(db_session)
    img = await image_service.register_group_image(
        db_session, p.id, True, ImageRegister(url="https://gcs/two.jpg", sort_order=0)
    )
    assert img.url == "https://gcs/two.jpg"


async def test_register_group_image_missing_product_raises(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await image_service.register_group_image(
            db_session, 999999, True, ImageRegister(url="https://gcs/x.jpg")
        )


async def test_list_group_images_filters_by_flag(db_session: AsyncSession):
    p = await _seed(db_session)
    await image_service.register_group_image(
        db_session, p.id, True, ImageRegister(url="two.jpg")
    )
    await image_service.register_group_image(
        db_session, p.id, False, ImageRegister(url="single.jpg")
    )
    two_pack = await image_service.list_group_images(db_session, p.id, True)
    assert [i.url for i in two_pack] == ["two.jpg"]


async def test_reorder_group_images_updates_sort_order(db_session: AsyncSession):
    p = await _seed(db_session)
    img_a = await image_service.register_group_image(
        db_session, p.id, True, ImageRegister(url="a.jpg", sort_order=0)
    )
    img_b = await image_service.register_group_image(
        db_session, p.id, True, ImageRegister(url="b.jpg", sort_order=1)
    )
    req = ImageReorderRequest(items=[
        ImageReorderItem(id=img_a.id, sort_order=1),
        ImageReorderItem(id=img_b.id, sort_order=0),
    ])
    result = await image_service.reorder_group_images(db_session, p.id, True, req)
    assert [r.url for r in result] == ["b.jpg", "a.jpg"]
