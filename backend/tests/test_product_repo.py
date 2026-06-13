from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories import product_repo


async def _make_product(session, slug="kanro", active=True):
    p = Product(
        slug=slug, name="甘露梨", description="d", image="img", season="s",
        is_active=active,
    )
    return await product_repo.add(session, p)


async def test_add_and_get_by_slug_and_id(db_session: AsyncSession):
    p = await _make_product(db_session)
    assert p.id is not None
    assert (await product_repo.get_by_slug(db_session, "kanro")).id == p.id
    assert (await product_repo.get_by_id(db_session, p.id)).slug == "kanro"


async def test_list_active_excludes_inactive(db_session: AsyncSession):
    await _make_product(db_session, slug="active1", active=True)
    await _make_product(db_session, slug="hidden1", active=False)
    slugs = {p.slug for p in await product_repo.list_active(db_session)}
    assert "active1" in slugs
    assert "hidden1" not in slugs


async def test_get_by_slug_missing_returns_none(db_session: AsyncSession):
    assert await product_repo.get_by_slug(db_session, "ghost") is None
