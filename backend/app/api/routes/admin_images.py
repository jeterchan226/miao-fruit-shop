from typing import Annotated

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


@router.get("/specs/{spec_id}/images", response_model=list[AdminImageRead])
async def list_spec_images(spec_id: int, session: SessionDep) -> list[AdminImageRead]:
    return await image_service.list_spec_images(session, spec_id)


@router.post("/specs/{spec_id}/images", response_model=AdminImageRead, status_code=201)
async def register_spec_image(
    spec_id: int, data: ImageRegister, session: SessionDep
) -> AdminImageRead:
    return await image_service.register_spec_image(session, spec_id, data)


@router.patch("/specs/{spec_id}/images/reorder", response_model=list[AdminImageRead])
async def reorder_spec_images(
    spec_id: int, req: ImageReorderRequest, session: SessionDep
) -> list[AdminImageRead]:
    return await image_service.reorder_spec_images(session, spec_id, req)
