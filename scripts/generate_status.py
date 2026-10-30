#!/usr/bin/env python3
"""從 ticket 紀錄與 GitHub issue 狀態重建 docs/progress/STATUS.md。

本機執行：python3 scripts/generate_status.py
有 GITHUB_TOKEN 時帶上，沒有則匿名查詢（repo 公開）。
"""

import json
import os
import re
import sys
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

PROGRESS_DIR = Path(__file__).resolve().parent.parent / "docs" / "progress"
ISSUE_URL = "https://api.github.com/repos/jeterchan226/miao-fruit-shop/issues/{number}"
REQUEST_TIMEOUT_SECONDS = 10
RECENT_TICKETS = 3
STATUS_DONE = "完成"
VALID_STATUSES = {STATUS_DONE, "進行中", "阻塞"}
EMPTY_CONTENT = {"", "無", "無。"}

HEADER = """# 開發進度快照

由 `scripts/generate_status.py` 自動產生，勿手改；格式與規則見 [README.md](README.md)。自 2026-10-30 起記錄；更早的 ticket 見 git log 與 `docs/superpowers/`。
"""


class TicketFormatError(Exception):
    pass


class IssueLookupError(Exception):
    pass


@dataclass(frozen=True)
class DeferredItem:
    text: str
    issue: int | None


@dataclass(frozen=True)
class Ticket:
    filename: str
    number: int
    title: str
    status: str
    change: str
    updated: str
    deferred: list[DeferredItem]
    system_status: list[str]
    deploy_todos: list[str]


def parse_ticket(filename: str, text: str) -> Ticket:
    heading = _require(filename, "標題", r"^# #(\d+)[ \t]+(.+?)\s*$", text)
    status = _require(filename, "狀態", r"^- 狀態：(\S+)\s*$", text).group(1)
    if status not in VALID_STATUSES:
        raise TicketFormatError(f"{filename}: 狀態不合法：{status}")
    change = _require(filename, "OpenSpec change", r"^- OpenSpec change：`([^`]+)`", text).group(1)
    updated = _require(filename, "最後更新", r"^- 最後更新：(\d{4}-\d{2}-\d{2})\s*$", text).group(1)
    return Ticket(
        filename=filename,
        number=int(heading.group(1)),
        title=heading.group(2),
        status=status,
        change=change,
        updated=updated,
        deferred=[_parse_deferred(line) for line in _section_items(text, "留待之後")],
        system_status=_section_items(text, "系統現況"),
        deploy_todos=_section_items(text, "部署待辦"),
    )


def _require(filename: str, field: str, pattern: str, text: str) -> re.Match[str]:
    match = re.search(pattern, text, re.MULTILINE)
    if match is None:
        raise TicketFormatError(f"{filename}: 缺少{field}")
    return match


def _section_items(text: str, name: str) -> list[str]:
    match = re.search(rf"^## {name}[ \t]*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if match is None:
        return []
    items = re.findall(r"^-[ \t]+(.*?)[ \t]*$", match.group(1), re.MULTILINE)
    return [item for item in items if item not in EMPTY_CONTENT]


def _parse_deferred(line: str) -> DeferredItem:
    match = re.search(r"：#(\d+)。?$", line)
    if match is None:
        return DeferredItem(text=line, issue=None)
    return DeferredItem(text=line[: match.start()], issue=int(match.group(1)))


def render_status(tickets: Iterable[Ticket], closed_issues: set[int]) -> str:
    done = sorted((t for t in tickets if t.status == STATUS_DONE), key=lambda t: t.number)
    sections = [
        ("部署待辦", _render_deploy_todos(done)),
        ("系統現況", _render_system_status(done)),
        ("已完成", _render_completed(done)),
        ("留待之後", _render_deferred(done, closed_issues)),
    ]
    body = "\n".join(f"## {name}\n\n{content or '無。'}\n" for name, content in sections)
    return f"{HEADER}\n{body}"


def _render_deploy_todos(tickets: list[Ticket]) -> str:
    return "\n".join(f"- #{t.number}：{item}" for t in tickets for item in t.deploy_todos)


def _render_system_status(tickets: list[Ticket]) -> str:
    with_content = [t for t in tickets if t.system_status]
    recent = sorted(with_content, key=lambda t: (t.updated, t.number), reverse=True)
    return "\n\n".join(
        f"**#{t.number}**：{' '.join(t.system_status)}" for t in recent[:RECENT_TICKETS]
    )


def _render_completed(tickets: list[Ticket]) -> str:
    if not tickets:
        return ""
    rows = [
        f"| {t.number} | {_cell(t.title)} | `{t.change}` | {t.updated} "
        f"| [紀錄](tickets/{t.filename}) |"
        for t in tickets
    ]
    return "\n".join(
        ["| # | 標題 | OpenSpec change | 完成日 | 紀錄 |", "|---|---|---|---|---|", *rows]
    )


def _render_deferred(tickets: list[Ticket], closed_issues: set[int]) -> str:
    rows = [
        f"| {_cell(item.text)} | #{t.number} | {'—' if item.issue is None else f'#{item.issue}'} |"
        for t in tickets
        for item in t.deferred
        if item.issue not in closed_issues
    ]
    if not rows:
        return ""
    return "\n".join(["| 項目 | 來源 ticket | 追蹤 issue |", "|---|---|---|", *rows])


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def fetch_is_closed(number: int) -> bool:
    request = urllib.request.Request(
        ISSUE_URL.format(number=number),
        headers={"Accept": "application/vnd.github+json"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.load(response)["state"] == "closed"
    except (OSError, ValueError, KeyError) as error:
        raise IssueLookupError(f"#{number}: {error}") from error


def main(
    progress_dir: Path = PROGRESS_DIR,
    is_closed: Callable[[int], bool] = fetch_is_closed,
) -> int:
    try:
        tickets = [
            parse_ticket(path.name, path.read_text(encoding="utf-8"))
            for path in sorted((progress_dir / "tickets").glob("*.md"))
        ]
        tracked = {
            item.issue
            for ticket in tickets
            if ticket.status == STATUS_DONE
            for item in ticket.deferred
            if item.issue is not None
        }
        closed_issues = {number for number in sorted(tracked) if is_closed(number)}
    except (TicketFormatError, IssueLookupError) as error:
        print(f"無法產生進度快照：{error}", file=sys.stderr)
        return 1
    (progress_dir / "STATUS.md").write_text(render_status(tickets, closed_issues), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
