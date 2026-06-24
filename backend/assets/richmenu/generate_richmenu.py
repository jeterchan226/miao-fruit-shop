"""產生妙媽媽果園 LINE Rich Menu 圖片（2500x843，一排三欄）。

可重現：執行本腳本即重新產出 richmenu-compact.png。
用法：
    cd backend && uv run --with pillow python assets/richmenu/generate_richmenu.py

色票與版面對應 docs/superpowers/specs/2026-06-23-line-rich-menu-design.md，
三欄邊界與 Rich Menu 點擊區一致：A 0–833、C 833–1666、F 1666–2500。
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# 畫布與品牌色
W, H = 2500, 843
CREAM = (251, 243, 224)       # #FBF3E0 底色
CREAM_DEEP = (232, 210, 158)  # #E8D29E 分隔線
BROWN = (107, 78, 50)         # #6B4E32 標籤文字
ORANGE = (232, 155, 60)       # #E89B3C 主橘
ICON_BG = (245, 229, 198)     # 圖示底圈（淺橘）

# 字型（macOS 系統字型）
LABEL_FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
EMOJI_FONT_PATH = "/System/Library/Fonts/Apple Color Emoji.ttc"
EMOJI_STRIKE = 160  # Apple Color Emoji 可用點陣尺寸（本機有效值：96、160）

# 三欄點擊區邊界（與 build_rich_menu_request 的 bounds 一致）
COL_EDGES = [0, 833, 1666, 2500]
ITEMS = [("🍐", "立即訂購"), ("💰", "匯款回報"), ("📋", "購買須知")]

ICON_CY = 330   # 圖示中心 y
ICON_R = 150    # 圖示底圈半徑
ICON_SIZE = 200  # 圖示繪製尺寸
LABEL_CY = 605  # 標籤中心 y

OUT_PATH = Path(__file__).with_name("richmenu-compact.png")


def _render_emoji(char: str, font: ImageFont.FreeTypeFont, size: int) -> Image.Image:
    """以彩色點陣繪製 emoji 後縮放到目標尺寸。"""
    tmp = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((90, 90), char, font=font, anchor="mm", embedded_color=True)
    return tmp.resize((size, size), Image.LANCZOS)


def main() -> None:
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    # 頂部橘色細條
    draw.rectangle([0, 0, W, 14], fill=ORANGE)

    # 欄間分隔線
    for x in COL_EDGES[1:-1]:
        draw.line([(x, 130), (x, H - 110)], fill=CREAM_DEEP, width=4)

    label_font = ImageFont.truetype(LABEL_FONT_PATH, 96)
    emoji_font = ImageFont.truetype(EMOJI_FONT_PATH, EMOJI_STRIKE)

    centers = [(COL_EDGES[i] + COL_EDGES[i + 1]) // 2 for i in range(3)]
    for (emoji_char, label), cx in zip(ITEMS, centers, strict=True):
        draw.ellipse(
            [cx - ICON_R, ICON_CY - ICON_R, cx + ICON_R, ICON_CY + ICON_R],
            fill=ICON_BG,
        )
        icon = _render_emoji(emoji_char, emoji_font, ICON_SIZE)
        img.paste(icon, (cx - ICON_SIZE // 2, ICON_CY - ICON_SIZE // 2), icon)
        draw.text((cx, LABEL_CY), label, font=label_font, fill=BROWN, anchor="mm")

    img.save(OUT_PATH, "PNG")
    print(f"已產生 {OUT_PATH} ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
