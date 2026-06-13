from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_session
from app.schemas.product import (
    AdminProductRead,
    AdminSpecRead,
    ProductUpdate,
    SpecCreate,
    SpecUpdate,
)
from app.services import product_service

router = APIRouter(
    prefix="/api/admin",
    tags=["admin-products"],
    dependencies=[Depends(get_current_admin)],
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/products", response_model=list[AdminProductRead])
async def list_products(session: SessionDep) -> list[AdminProductRead]:
    return await product_service.list_admin_products(session)


@router.patch("/products/{product_id}", response_model=AdminProductRead)
async def update_product(
    product_id: int, data: ProductUpdate, session: SessionDep
) -> AdminProductRead:
    return await product_service.update_product(session, product_id, data)


@router.post(
    "/products/{product_id}/specs", response_model=AdminSpecRead, status_code=201
)
async def create_spec(
    product_id: int, data: SpecCreate, session: SessionDep
) -> AdminSpecRead:
    return await product_service.create_spec(session, product_id, data)


@router.patch("/specs/{spec_id}", response_model=AdminSpecRead)
async def update_spec(
    spec_id: int, data: SpecUpdate, session: SessionDep
) -> AdminSpecRead:
    return await product_service.update_spec(session, spec_id, data)


@router.delete("/specs/{spec_id}", status_code=204)
async def delete_spec(spec_id: int, session: SessionDep) -> None:
    await product_service.soft_delete_spec(session, spec_id)
