from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.product_image import ProductImage
from app.repositories import image_repo, product_repo
from app.schemas.image import (
    AdminImageRead,
    ImageRegister,
    ImageReorderRequest,
    SignedUrlRequest,
    SignedUrlResponse,
)
from app.services.gcs_service import gcs_service


def request_sign(product_id: int, req: SignedUrlRequest) -> SignedUrlResponse:
    if not gcs_service.enabled:
        raise AppError("GCS 未設定，無法上傳圖片")
    result = gcs_service.sign_upload(product_id, req.filename, req.content_type)
    return SignedUrlResponse(**result)


async def list_images(session: AsyncSession, product_id: int) -> list[AdminImageRead]:
    imgs = await image_repo.list_by_product(session, product_id)
    return [AdminImageRead.model_validate(i) for i in imgs]


async def register_image(
    session: AsyncSession, product_id: int, data: ImageRegister
) -> AdminImageRead:
    product = await product_repo.get_by_id(session, product_id)
    if product is None:
        raise NotFoundError("找不到商品")
    img = ProductImage(product_id=product_id, url=data.url, sort_order=data.sort_order)
    await image_repo.add(session, img)
    await session.commit()
    await session.refresh(img)
    return AdminImageRead.model_validate(img)


async def delete_image(session: AsyncSession, image_id: int) -> None:
    img = await image_repo.get_by_id(session, image_id)
    if img is None:
        raise NotFoundError("找不到圖片")
    url = img.url
    await image_repo.delete(session, img)
    await session.commit()
    if gcs_service.enabled:
        gcs_service.delete_object(url)


async def reorder_images(
    session: AsyncSession, product_id: int, req: ImageReorderRequest
) -> list[AdminImageRead]:
    for item in req.items:
        img = await image_repo.get_by_id(session, item.id)
        if img is not None and img.product_id == product_id:
            img.sort_order = item.sort_order
    await session.commit()
    return await list_images(session, product_id)
