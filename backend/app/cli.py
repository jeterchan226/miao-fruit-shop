import argparse
import asyncio
import getpass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.admin_user import AdminUser
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import admin_repo, product_repo
from app.services import line_service

MIN_PASSWORD_LEN = 8


async def create_admin(
    session: AsyncSession, username: str, password: str
) -> AdminUser:
    if len(password) < MIN_PASSWORD_LEN:
        raise ValueError(f"密碼長度至少 {MIN_PASSWORD_LEN} 字元")
    if await admin_repo.get_by_username(session, username) is not None:
        raise ValueError(f"管理員 '{username}' 已存在")
    admin = AdminUser(
        username=username, hashed_password=hash_password(password), is_active=True
    )
    await admin_repo.add(session, admin)
    await session.commit()
    return admin


SEED_SLUG = "kanro"


async def seed_product(session: AsyncSession) -> Product:
    if await product_repo.get_by_slug(session, SEED_SLUG) is not None:
        raise ValueError("商品 '甘露梨' 已存在")
    product = Product(
        slug=SEED_SLUG,
        name="甘露梨",
        description="園區珍稀品種,產量稀少,蜜香濃郁、入口即化,識貨的老客戶才點。",
        image="assets/product_5.jpg",
        season="10 月上旬 – 10 月中旬",
        tag="珍稀",
        tag_color="red",
    )
    product.specs = [
        ProductSpec(
            label="2 粒精緻禮盒", qty_text="2 顆 · 約 1.6 台斤", price=880,
            stock_qty=20, note="蜜糖之味", sort_order=1,
        ),
        ProductSpec(
            label="5 台斤家庭箱", qty_text="6–8 顆 · 5 台斤", price=1880,
            stock_qty=3, low_stock_threshold=3, note="剩 3 箱", sort_order=2,
        ),
        ProductSpec(
            label="10 台斤大箱", qty_text="12–16 顆 · 10 台斤", price=3580,
            stock_qty=20, note="老客戶限定", sort_order=3,
        ),
    ]
    session.add(product)
    await session.commit()
    return product


async def _run_seed_product() -> None:
    async with AsyncSessionLocal() as session:
        try:
            product = await seed_product(session)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    print(f"已建立商品:{product.name}(規格 {len(product.specs)} 個)")


def _prompt_password() -> str:
    pw = getpass.getpass("密碼: ")
    if pw != getpass.getpass("再次輸入密碼: "):
        raise SystemExit("兩次密碼不一致")
    return pw


async def _run_create_admin(username: str) -> None:
    password = _prompt_password()
    async with AsyncSessionLocal() as session:
        try:
            admin = await create_admin(session, username, password)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    print(f"已建立管理員:{admin.username}")


def _run_setup_richmenu(image: str, liff_id: str) -> None:
    if not liff_id:
        raise SystemExit("缺少 LIFF ID（請用 --liff-id 或設定 LINE_LIFF_ID）")
    if not settings.line_channel_access_token:
        raise SystemExit("缺少 LINE_CHANNEL_ACCESS_TOKEN")
    rich_menu_id = line_service.setup_rich_menu(image, liff_id)
    print(f"已建立並套用 Rich Menu：{rich_menu_id}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-admin", help="建立後台管理員")
    create.add_argument("--username", required=True)
    sub.add_parser("seed-product", help="建立初始商品(甘露梨)")
    richmenu = sub.add_parser("setup-richmenu", help="建立並套用 Rich Menu")
    richmenu.add_argument("--image", required=True, help="Rich Menu 圖片路徑（2500x843 PNG）")
    richmenu.add_argument("--liff-id", default=None, help="LIFF App ID（預設取 LINE_LIFF_ID）")
    args = parser.parse_args()
    if args.command == "create-admin":
        asyncio.run(_run_create_admin(args.username))
    elif args.command == "seed-product":
        asyncio.run(_run_seed_product())
    elif args.command == "setup-richmenu":
        _run_setup_richmenu(args.image, args.liff_id or settings.line_liff_id)


if __name__ == "__main__":
    main()
