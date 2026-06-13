import argparse
import asyncio
import getpass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.admin_user import AdminUser
from app.repositories import admin_repo

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


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-admin", help="建立後台管理員")
    create.add_argument("--username", required=True)
    args = parser.parse_args()
    if args.command == "create-admin":
        asyncio.run(_run_create_admin(args.username))


if __name__ == "__main__":
    main()
