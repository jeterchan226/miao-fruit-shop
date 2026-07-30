from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_session
from app.schemas.image import (
    AdminImageRead,
    ImageRegister,
    ImageReorderRequest,
    SignedUrlRequest,
    SignedUrlResponse,
)
from app.services import image_service

router = APIRouter(
    prefix="/api/admin",
    tags=["admin-images"],
    dependencies=[Depends(get_current_admin)],
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
ImageGroup = Literal["two_pack", "single"]


def _is_two_pack(group: ImageGroup) -> bool:
    return group == "two_pack"


@router.post("/uploads/sign", response_model=SignedUrlResponse)
async def sign_upload(req: SignedUrlRequest, session: SessionDep) -> SignedUrlResponse:
    return image_service.request_sign(product_id=0, req=req)


@router.get("/products/{product_id}/images", response_model=list[AdminImageRead])
async def list_images(product_id: int, session: SessionDep) -> list[AdminImageRead]:
    return await image_service.list_images(session, product_id)


@router.post(
    "/products/{product_id}/images", response_model=AdminImageRead, status_code=201
)
async def register_image(
    product_id: int, data: ImageRegister, session: SessionDep
) -> AdminImageRead:
    return await image_service.register_image(session, product_id, data)


@router.delete("/images/{image_id}", status_code=204)
async def delete_image(image_id: int, session: SessionDep) -> None:
    await image_service.delete_image(session, image_id)


@router.patch("/products/{product_id}/images/reorder", response_model=list[AdminImageRead])
async def reorder_images(
    product_id: int, req: ImageReorderRequest, session: SessionDep
) -> list[AdminImageRead]:
    return await image_service.reorder_images(session, product_id, req)


@router.get(
    "/products/{product_id}/images/group/{group}", response_model=list[AdminImageRead]
)
async def list_group_images(
    product_id: int, group: ImageGroup, session: SessionDep
) -> list[AdminImageRead]:
    return await image_service.list_group_images(session, product_id, _is_two_pack(group))


@router.post(
    "/products/{product_id}/images/group/{group}",
    response_model=AdminImageRead,
    status_code=201,
)
async def register_group_image(
    product_id: int, group: ImageGroup, data: ImageRegister, session: SessionDep
) -> AdminImageRead:
    return await image_service.register_group_image(
        session, product_id, _is_two_pack(group), data
    )


@router.patch(
    "/products/{product_id}/images/group/{group}/reorder",
    response_model=list[AdminImageRead],
)
async def reorder_group_images(
    product_id: int, group: ImageGroup, req: ImageReorderRequest, session: SessionDep
) -> list[AdminImageRead]:
    return await image_service.reorder_group_images(
        session, product_id, _is_two_pack(group), req
    )
