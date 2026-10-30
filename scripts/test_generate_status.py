import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import generate_status
from generate_status import TicketFormatError, parse_ticket, render_status


def record(
    number=46,
    title="訂單品項快照",
    status="完成",
    updated="2026-10-30",
    sections="",
):
    return f"""# #{number} {title}

- 狀態：{status}
- OpenSpec change：`change-{number}`（archive 後：`openspec/changes/archive/2026-10-30-change-{number}/`）
- Branch：`claude/branch`
- 最後更新：{updated}

## 做了什麼
- 使用者看得到的變更。

{sections}
"""


def ticket(number=46, **kwargs):
    return parse_ticket(f"{number}-change-{number}.md", record(number, **kwargs))


def section(text, name):
    after_heading = text.split(f"## {name}\n", 1)[1]
    return after_heading.split("\n## ", 1)[0]


class ParseTicketTest(unittest.TestCase):
    def test_reads_header_fields(self):
        parsed = ticket(46, title="訂單品項快照", updated="2026-10-29")

        self.assertEqual(parsed.number, 46)
        self.assertEqual(parsed.title, "訂單品項快照")
        self.assertEqual(parsed.status, "完成")
        self.assertEqual(parsed.change, "change-46")
        self.assertEqual(parsed.updated, "2026-10-29")
        self.assertEqual(parsed.filename, "46-change-46.md")

    def test_missing_required_field_names_the_file(self):
        full = record()
        cases = {
            "標題": full.replace("# #46 訂單品項快照\n", ""),
            "狀態": full.replace("- 狀態：完成\n", ""),
            "OpenSpec change": full.replace("- OpenSpec change：`change-46`", "- 其他：`x`"),
            "最後更新": full.replace("- 最後更新：2026-10-30\n", ""),
        }
        for field, text in cases.items():
            with self.subTest(field=field):
                with self.assertRaises(TicketFormatError) as caught:
                    parse_ticket("46-broken.md", text)
                self.assertIn("46-broken.md", str(caught.exception))
                self.assertIn(field, str(caught.exception))

    def test_title_must_be_on_its_own_line(self):
        text = record().replace("# #46 訂單品項快照\n", "# #46\n")

        with self.assertRaises(TicketFormatError) as caught:
            parse_ticket("46-broken.md", text)
        self.assertIn("標題", str(caught.exception))

    def test_only_top_level_bullets_are_items(self):
        parsed = ticket(
            sections="""## 留待之後
- 第一項
  續行說明
  - 子項目
<!-- 註解 -->
- 第二項
""",
        )

        self.assertEqual([item.text for item in parsed.deferred], ["第一項", "第二項"])

    def test_only_line_end_marker_is_a_tracking_issue(self):
        parsed = ticket(
            sections="""## 留待之後
- 錯誤訊息改用快照名稱（可併入 #45）：#83
- 句尾有句點：#84。
- 確認 PR #76 的 log
- 依 #45 再決定
""",
        )

        self.assertEqual(
            [(item.text, item.issue) for item in parsed.deferred],
            [
                ("錯誤訊息改用快照名稱（可併入 #45）", 83),
                ("句尾有句點", 84),
                ("確認 PR #76 的 log", None),
                ("依 #45 再決定", None),
            ],
        )

    def test_placeholder_lines_are_not_content(self):
        for placeholder in ("- ", "-", "- 無", "- 無。", "無", ""):
            with self.subTest(placeholder=placeholder):
                parsed = ticket(
                    sections=f"""## 留待之後
{placeholder}

## 系統現況
{placeholder}

## 部署待辦
{placeholder}
""",
                )
                self.assertEqual(parsed.deferred, [])
                self.assertEqual(parsed.system_status, [])
                self.assertEqual(parsed.deploy_todos, [])


class RenderCompletedTest(unittest.TestCase):
    def test_lists_done_tickets_by_number(self):
        text = render_status([ticket(67, title="常數"), ticket(31, title="Node")], set())

        rows = section(text, "已完成").strip().splitlines()[2:]
        self.assertEqual(
            rows,
            [
                "| 31 | Node | `change-31` | 2026-10-30 | [紀錄](tickets/31-change-31.md) |",
                "| 67 | 常數 | `change-67` | 2026-10-30 | [紀錄](tickets/67-change-67.md) |",
            ],
        )

    def test_unfinished_tickets_appear_nowhere(self):
        for status in ("進行中", "阻塞"):
            with self.subTest(status=status):
                text = render_status(
                    [
                        ticket(
                            90,
                            title="未完成標題",
                            status=status,
                            sections="""## 留待之後
- 未完成的留待項目

## 系統現況
- 未完成的現況

## 部署待辦
- 未完成的部署
""",
                        )
                    ],
                    set(),
                )
                self.assertNotIn("未完成", text)
                self.assertNotIn("#90", text)

    def test_table_cell_pipe_is_escaped(self):
        text = render_status(
            [ticket(sections="## 留待之後\n- 比較 a | b 兩種寫法\n")],
            set(),
        )

        self.assertIn("比較 a \\| b 兩種寫法", section(text, "留待之後"))


class RenderDeferredTest(unittest.TestCase):
    sections = """## 留待之後
- 已解決的項目：#83
- 待處理的項目：#84
- 確認 PR #76 的 log
"""

    def test_closed_tracking_issue_is_hidden(self):
        text = render_status([ticket(sections=self.sections)], {83})

        deferred = section(text, "留待之後")
        self.assertNotIn("已解決的項目", deferred)
        self.assertIn("| 待處理的項目 | #46 | #84 |", deferred)

    def test_untracked_item_stays_with_placeholder(self):
        text = render_status([ticket(sections=self.sections)], {76, 83, 84})

        deferred = section(text, "留待之後")
        self.assertIn("| 確認 PR #76 的 log | #46 | — |", deferred)

    def test_sorted_by_source_ticket_keeping_record_order(self):
        text = render_status(
            [
                ticket(67, sections="## 留待之後\n- 後\n"),
                ticket(31, sections="## 留待之後\n- 甲\n- 乙\n"),
            ],
            set(),
        )

        rows = section(text, "留待之後").strip().splitlines()[2:]
        self.assertEqual(rows, ["| 甲 | #31 | — |", "| 乙 | #31 | — |", "| 後 | #67 | — |"])


class RenderLayoutTest(unittest.TestCase):
    def test_section_order_and_no_next_step_section(self):
        text = render_status([ticket()], set())

        headings = [line for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, ["## 部署待辦", "## 系統現況", "## 已完成", "## 留待之後"])
        self.assertNotIn("下一步建議", text)

    def test_header_marks_file_as_generated(self):
        text = render_status([], set())

        self.assertIn("自動產生", text)
        self.assertIn("勿手改", text)
        self.assertIn("自 2026-10-30 起記錄", text)

    def test_empty_sections_say_none(self):
        text = render_status([], set())

        for name in ("部署待辦", "系統現況", "已完成", "留待之後"):
            with self.subTest(name=name):
                self.assertEqual(section(text, name).strip(), "無。")

    def test_same_input_same_output(self):
        tickets = [ticket(67), ticket(31)]

        self.assertEqual(render_status(tickets, {1}), render_status(list(reversed(tickets)), {1}))


class RenderSystemStatusTest(unittest.TestCase):
    @staticmethod
    def with_status(number, updated, content):
        return ticket(number, updated=updated, sections=f"## 系統現況\n- {content}\n")

    def test_only_three_most_recent(self):
        text = render_status(
            [
                self.with_status(1, "2026-10-01", "最舊"),
                self.with_status(2, "2026-10-02", "第三"),
                self.with_status(3, "2026-10-03", "第二"),
                self.with_status(4, "2026-10-04", "最新"),
            ],
            set(),
        )

        self.assertEqual(
            section(text, "系統現況").strip().splitlines(),
            ["**#4**：最新", "", "**#3**：第二", "", "**#2**：第三"],
        )

    def test_same_day_orders_by_number_descending(self):
        text = render_status(
            [
                self.with_status(31, "2026-10-30", "甲"),
                self.with_status(67, "2026-10-30", "乙"),
            ],
            set(),
        )

        self.assertLess(text.index("**#67**"), text.index("**#31**"))

    def test_ticket_without_content_takes_no_slot(self):
        text = render_status(
            [
                self.with_status(1, "2026-10-01", "最舊"),
                self.with_status(2, "2026-10-02", "第三"),
                self.with_status(3, "2026-10-03", "第二"),
                ticket(4, updated="2026-10-04"),
                ticket(5, updated="2026-10-05", sections="## 系統現況\n- \n"),
            ],
            set(),
        )

        lines = section(text, "系統現況")
        self.assertIn("**#1**：最舊", lines)
        self.assertNotIn("**#4**", lines)
        self.assertNotIn("**#5**", lines)


class RenderDeployTodosTest(unittest.TestCase):
    def test_lists_items_with_source_ticket(self):
        text = render_status(
            [ticket(46, sections="## 部署待辦\n- 先跑 migration\n- 再部署前端\n")],
            set(),
        )

        self.assertEqual(
            section(text, "部署待辦").strip().splitlines(),
            ["- #46：先跑 migration", "- #46：再部署前端"],
        )

    def test_removed_section_disappears(self):
        text = render_status([ticket(46)], set())

        self.assertEqual(section(text, "部署待辦").strip(), "無。")


class MainTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.progress = Path(temp.name)
        (self.progress / "tickets").mkdir()
        self.status = self.progress / "STATUS.md"
        self.status.write_text("舊快照\n", encoding="utf-8")

    def write_ticket(self, name, text):
        (self.progress / "tickets" / name).write_text(text, encoding="utf-8")

    def run_main(self, is_closed):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = generate_status.main(self.progress, is_closed)
        return code, stderr.getvalue()

    def test_writes_snapshot_querying_only_done_tracked_issues(self):
        self.write_ticket("46-a.md", record(46, sections="## 留待之後\n- 已解：#83\n- 待辦：#84\n"))
        self.write_ticket("90-b.md", record(90, status="進行中", sections="## 留待之後\n- 別查：#85\n"))
        queried = []

        def is_closed(number):
            queried.append(number)
            return number == 83

        code, _ = self.run_main(is_closed)

        self.assertEqual(code, 0)
        self.assertEqual(queried, [83, 84])
        written = self.status.read_text(encoding="utf-8")
        self.assertNotIn("已解", written)
        self.assertIn("待辦", written)

    def test_issue_lookup_failure_keeps_snapshot(self):
        self.write_ticket("46-a.md", record(46, sections="## 留待之後\n- 項目：#83\n"))

        def is_closed(number):
            raise generate_status.IssueLookupError(f"#{number}: HTTP 503")

        code, stderr = self.run_main(is_closed)

        self.assertNotEqual(code, 0)
        self.assertIn("#83", stderr)
        self.assertEqual(self.status.read_text(encoding="utf-8"), "舊快照\n")

    def test_malformed_ticket_keeps_snapshot_and_names_file(self):
        self.write_ticket("46-a.md", record(46))
        self.write_ticket("47-broken.md", "沒有標題\n")

        code, stderr = self.run_main(lambda number: False)

        self.assertNotEqual(code, 0)
        self.assertIn("47-broken.md", stderr)
        self.assertEqual(self.status.read_text(encoding="utf-8"), "舊快照\n")


if __name__ == "__main__":
    unittest.main()
