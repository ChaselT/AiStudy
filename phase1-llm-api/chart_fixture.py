"""ex09 任务 3A 的测试素材：折线图 + 配套 ground truth。

设计意图：让"模型读图准不准"这件事**可量化**。
网上找的图表读不出精确值，没法算准确率；这里图是**从下面的数据渲染出来的**，
所以 ground truth 与图像天然一致，不会对不上——这是把素材和答案放同一个文件的原因。

生成两张图（同一份数据，唯一变量是有没有数字标签）：
    data/chart_labeled.png    每个点都标了数值 → 考 OCR + 系列归属
    data/chart_unlabeled.png  不标数值，但所有值都落在网格线上 → 考坐标估读

三条线故意设计了多次交叉，且有两处**取值完全相同**（点与标签都重叠）：
    第 5 月：产品A = 产品B = 80
    第 6 月：产品A = 产品C = 90
这两处考的是"模型会不会把两条线搞混"——单看标签只能看到一个数字，
必须顺着线的颜色和走向才能判断出是两个点。评分时单独标记这两格。

用法：
    uv run --with matplotlib chart_fixture.py     # 生成图片到 data/
    from chart_fixture import CHART_DATA          # 在实验里取 ground truth 比对
"""

from __future__ import annotations

import pathlib

MONTHS: list[int] = list(range(1, 13))

# —— ground truth：图里的每一个数字都出自这里 ——
CHART_DATA: dict[str, list[int]] = {
    "产品A": [20, 30, 50, 60, 80, 90, 100, 110, 120, 140, 150, 160],
    "产品B": [90, 100, 100, 90, 80, 70, 60, 50, 40, 30, 30, 20],
    "产品C": [50, 70, 40, 80, 60, 90, 40, 90, 60, 100, 50, 110],
}

OUT_DIR = pathlib.Path(__file__).parent / "data"


def render(labeled: bool, out_path: pathlib.Path) -> None:
    # matplotlib 只在生成素材时临时用（uv run --with matplotlib），未进 pyproject
    import matplotlib  # type: ignore[import-not-found]
    from matplotlib import font_manager  # type: ignore[import-not-found]

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # type: ignore[import-not-found]

    font_manager.fontManager.addfont("C:/Windows/Fonts/msyh.ttc")
    plt.rcParams["font.family"] = "Microsoft YaHei"
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)

    for name, values in CHART_DATA.items():
        ax.plot(MONTHS, values, marker="o", linewidth=2.5, markersize=8, label=name)
        if labeled:
            for x, y in zip(MONTHS, values, strict=True):
                ax.annotate(
                    str(y),
                    (x, y),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    fontsize=11,
                )

    ax.set_title("2026 年三款产品月度销量", fontsize=20, pad=18)
    ax.set_xlabel("月份", fontsize=14)
    ax.set_ylabel("销量（台）", fontsize=14)
    ax.set_xticks(MONTHS)
    ax.set_yticks(range(0, 181, 20))
    ax.set_yticks(range(0, 181, 10), minor=True)
    ax.set_ylim(0, 180)
    ax.grid(which="major", alpha=0.45)
    ax.grid(which="minor", alpha=0.2, linestyle=":")
    ax.legend(fontsize=14, loc="upper left")

    out_path.parent.mkdir(exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    for labeled, name in ((True, "chart_labeled.png"), (False, "chart_unlabeled.png")):
        path = OUT_DIR / name
        render(labeled, path)
        print(f"已生成 {path}  ({path.stat().st_size / 1024:.0f} KB)")

    print("\nground truth：")
    header = "月份  " + "".join(f"{m:>6}" for m in MONTHS)
    print(header)
    for name, values in CHART_DATA.items():
        print(f"{name}  " + "".join(f"{v:>6}" for v in values))


if __name__ == "__main__":
    main()
