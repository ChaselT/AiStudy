"""博客封面生成器 —— 一条命令出三个尺寸。

用法（在 blog 目录下）：
    uv run --with pillow python make_cover.py \
        --line1 "我把 Claude 当教练" \
        --line2 "而不是代码生成器" \
        --sub   "一个 Java 工程师的转 AI 第一周" \
        --meta  "6 天 · 17 节课 · 46 个练习 · 阶段测试 92 分" \
        --out   cover_01

产出三个文件（微信有 64KB 硬限制，其余平台用高清版）：
    <out>.jpg          900x500   <64KB   微信公众号
    <out>_16x9.jpg     1200x675          掘金 / 知乎
    <out>_square.jpg   1080x1080         备用（方形信息流）
"""

import argparse
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (15, 23, 42)  # 深蓝底
ACCENT = (56, 189, 248)  # 亮青点缀
WHITE = (241, 245, 249)
GREY = (148, 163, 184)
LINE = (51, 65, 85)
FONT_PATH = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑


def draw_cover(
    w: int,
    h: int,
    out: Path,
    line1: str,
    line2: str,
    sub: str,
    meta: str,
    scale: float,
    max_kb: float | None = None,
) -> None:
    """画一张封面；给了 max_kb 就逐档降质量直到达标（微信 64KB 限制用）。"""
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    f_big = ImageFont.truetype(FONT_PATH, int(64 * scale), index=0)
    f_mid = ImageFont.truetype(FONT_PATH, int(30 * scale), index=0)
    f_sm = ImageFont.truetype(FONT_PATH, int(24 * scale), index=0)

    d.rectangle([0, 0, int(12 * scale), h], fill=ACCENT)  # 左侧亮色竖条

    x = int(70 * scale)
    top = (h - int(300 * scale)) // 2  # 垂直居中
    d.text((x, top), line1, font=f_big, fill=WHITE)
    d.text((x, top + int(80 * scale)), line2, font=f_big, fill=ACCENT)
    d.text((x + 2, top + int(180 * scale)), sub, font=f_mid, fill=GREY)
    d.line(
        [(x + 2, top + int(240 * scale)), (x + int(430 * scale), top + int(240 * scale))],
        fill=LINE,
        width=max(2, int(2 * scale)),
    )
    d.text((x + 2, top + int(270 * scale)), meta, font=f_sm, fill=GREY)

    for quality in (95, 88, 80, 72, 65):
        img.save(out, "JPEG", quality=quality, optimize=True)
        kb = os.path.getsize(out) / 1024
        if max_kb is None or kb < max_kb:
            break
    print(f"{out.name:<26} {w}x{h:<6} {os.path.getsize(out) / 1024:>6.1f} KB")


def main() -> None:
    p = argparse.ArgumentParser(description="生成博客封面（微信/掘金/知乎三尺寸）")
    p.add_argument("--line1", required=True, help="主标题第一行（白色）")
    p.add_argument("--line2", required=True, help="主标题第二行（亮青强调）")
    p.add_argument("--sub", default="", help="副标题")
    p.add_argument("--meta", default="", help="底部数据行")
    p.add_argument("--out", default="cover", help="输出文件名前缀（不含扩展名）")
    args = p.parse_args()

    base = Path(args.out)
    common = dict(line1=args.line1, line2=args.line2, sub=args.sub, meta=args.meta)

    # 微信：64KB 硬限制，必须压到 60KB 以内留余量
    draw_cover(900, 500, base.with_suffix(".jpg"), scale=1.0, max_kb=60, **common)
    # 掘金 / 知乎：16:9 高清
    draw_cover(1200, 675, base.with_name(base.name + "_16x9").with_suffix(".jpg"), scale=1.33, **common)
    # 备用：方形
    draw_cover(1080, 1080, base.with_name(base.name + "_square").with_suffix(".jpg"), scale=1.4, **common)


if __name__ == "__main__":
    main()
