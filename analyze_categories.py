from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

DATASET_PATH = Path('dataset_TSMC2014_TKY.txt')
OUTPUT_CSV = Path('category_counts.csv')
OUTPUT_CHART = Path('category_poi_counts.svg')


def parse_dataset(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    with path.open('r', encoding='latin-1') as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 4:
                continue
            category_name = parts[3].strip() or 'Unknown'
            counts[category_name] += 1
    return counts


def write_csv(counts: Counter[str], output_path: Path) -> list[tuple[str, int]]:
    ordered = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    with output_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['category_name', 'poi_count'])
        writer.writerows(ordered)
    return ordered


def create_svg_bar_chart(category_counts: list[tuple[str, int]], output_path: Path) -> None:
    if not category_counts:
        output_path.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding='utf-8')
        return

    margin_left = 340
    margin_right = 40
    margin_top = 40
    margin_bottom = 40
    bar_height = 20
    bar_gap = 4

    n = len(category_counts)
    plot_height = n * (bar_height + bar_gap)
    chart_height = margin_top + plot_height + margin_bottom
    chart_width = 1400

    max_count = max(count for _, count in category_counts)
    usable_width = chart_width - margin_left - margin_right

    lines: list[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{chart_width}" height="{chart_height}">')
    lines.append('<style>text { font-family: Arial, sans-serif; font-size: 12px; }</style>')
    lines.append(f'<text x="{chart_width/2}" y="24" text-anchor="middle" font-size="18" font-weight="bold">POI Count per Category</text>')

    for idx, (name, count) in enumerate(reversed(category_counts)):
        y = margin_top + idx * (bar_height + bar_gap)
        bar_width = 0 if max_count == 0 else (count / max_count) * usable_width
        lines.append(
            f'<rect x="{margin_left}" y="{y}" width="{bar_width:.2f}" height="{bar_height}" fill="#4C78A8" />'
        )
        lines.append(
            f'<text x="{margin_left - 8}" y="{y + bar_height * 0.72}" text-anchor="end">{escape_xml(name)}</text>'
        )
        lines.append(
            f'<text x="{margin_left + bar_width + 6:.2f}" y="{y + bar_height * 0.72}">{count}</text>'
        )

    lines.append('</svg>')
    output_path.write_text('\n'.join(lines), encoding='utf-8')


def escape_xml(text: str) -> str:
    return (
        text.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&apos;')
    )


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f'未找到数据集: {DATASET_PATH}')

    counts = parse_dataset(DATASET_PATH)
    ordered_counts = write_csv(counts, OUTPUT_CSV)
    create_svg_bar_chart(ordered_counts, OUTPUT_CHART)

    total_records = sum(counts.values())
    print(f'总记录数: {total_records}')
    print(f'类别总数: {len(ordered_counts)}')
    print('POI 数量最多的前 10 个类别:')
    for name, count in ordered_counts[:10]:
        print(f'- {name}: {count}')
    print(f'已输出统计表: {OUTPUT_CSV}')
    print(f'已输出柱状图: {OUTPUT_CHART}')


if __name__ == '__main__':
    main()
