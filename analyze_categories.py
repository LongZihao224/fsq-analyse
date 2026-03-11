from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

DATASET_PATH = Path('dataset_TSMC2014_TKY.txt')
OUTPUT_FINE_CSV = Path('category_counts.csv')
OUTPUT_AGG_CSV = Path('category_group_counts.csv')
OUTPUT_MAPPING_CSV = Path('category_group_mapping.csv')
OUTPUT_CHART = Path('category_group_poi_counts.svg')

# 规则按顺序匹配，命中第一个即归类到对应大类
GROUP_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        '交通出行',
        (
            'station', 'subway', 'metro', 'train', 'bus', 'airport', 'tram', 'ferry',
            'port', 'platform', 'taxi', 'road', 'bridge', 'tunnel', 'highway',
        ),
    ),
    (
        '餐饮美食',
        (
            'restaurant', 'ramen', 'noodle', 'café', 'cafe', 'coffee', 'tea', 'bar',
            'pub', 'bbq', 'sushi', 'izakaya', 'food', 'bakery', 'diner', 'burger',
            'pizza', 'snack', 'dessert', 'steakhouse', 'buffet',
        ),
    ),
    (
        '购物消费',
        (
            'store', 'shop', 'mall', 'market', 'boutique', 'bookstore', 'pharmacy',
            'supermarket', 'department', 'electronics', 'clothing', 'gift', 'outlet',
            'convenience', 'liquor',
        ),
    ),
    (
        '办公与居住',
        (
            'office', 'building', 'home', 'housing', 'residential', 'apartment',
            'coworking', 'factory', 'industrial', 'workshop',
        ),
    ),
    (
        '旅游与休闲',
        (
            'hotel', 'hostel', 'resort', 'park', 'plaza', 'garden', 'museum',
            'theater', 'cinema', 'arcade', 'stadium', 'gym', 'spa', 'pool',
            'scenic', 'beach', 'tourist', 'theme park', 'karaoke',
        ),
    ),
    (
        '教育文化',
        (
            'school', 'university', 'college', 'library', 'classroom', 'campus',
            'student center', 'education',
        ),
    ),
    (
        '医疗健康',
        (
            'hospital', 'clinic', 'medical', 'doctor', 'dentist', 'health', 'drugstore',
        ),
    ),
    (
        '公共服务',
        (
            'government', 'embassy', 'post office', 'police', 'fire station',
            'courthouse', 'city hall', 'community center',
        ),
    ),
    (
        '宗教与纪念',
        (
            'temple', 'shrine', 'church', 'mosque', 'synagogue', 'cemetery', 'memorial',
        ),
    ),
]
DEFAULT_GROUP = '其他'

def _keyword_to_pattern(keyword: str) -> re.Pattern[str]:
    escaped = re.escape(keyword).replace('\ ', r'\s+')
    return re.compile(rf'(?<![a-z]){escaped}(?![a-z])')


COMPILED_GROUP_RULES: list[tuple[str, tuple[re.Pattern[str], ...]]] = [
    (group_name, tuple(_keyword_to_pattern(keyword) for keyword in keywords))
    for group_name, keywords in GROUP_RULES
]


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


def map_to_group(category_name: str) -> str:
    lowered = category_name.lower()
    for group_name, patterns in COMPILED_GROUP_RULES:
        if any(pattern.search(lowered) for pattern in patterns):
            return group_name
    return DEFAULT_GROUP


def write_fine_category_csv(counts: Counter[str], output_path: Path) -> list[tuple[str, int]]:
    ordered = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    with output_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['category_name', 'poi_count'])
        writer.writerows(ordered)
    return ordered


def aggregate_categories(
    fine_counts: list[tuple[str, int]],
) -> tuple[list[tuple[str, int]], dict[str, list[tuple[str, int]]]]:
    group_counter: Counter[str] = Counter()
    group_mapping: dict[str, list[tuple[str, int]]] = defaultdict(list)

    for category_name, count in fine_counts:
        group_name = map_to_group(category_name)
        group_counter[group_name] += count
        group_mapping[group_name].append((category_name, count))

    ordered_groups = sorted(group_counter.items(), key=lambda x: x[1], reverse=True)
    for group_name in group_mapping:
        group_mapping[group_name].sort(key=lambda x: x[1], reverse=True)

    return ordered_groups, dict(group_mapping)


def write_group_csv(group_counts: list[tuple[str, int]], output_path: Path) -> None:
    with output_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['group_name', 'poi_count'])
        writer.writerows(group_counts)


def write_mapping_csv(group_mapping: dict[str, list[tuple[str, int]]], output_path: Path) -> None:
    with output_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['group_name', 'subcategory_name', 'subcategory_poi_count'])
        for group_name in sorted(group_mapping.keys()):
            for sub_name, sub_count in group_mapping[group_name]:
                writer.writerow([group_name, sub_name, sub_count])


def create_svg_bar_chart(group_counts: list[tuple[str, int]], output_path: Path) -> None:
    if not group_counts:
        output_path.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding='utf-8')
        return

    margin_left = 180
    margin_right = 60
    margin_top = 50
    margin_bottom = 50
    bar_height = 34
    bar_gap = 14

    n = len(group_counts)
    plot_height = n * (bar_height + bar_gap)
    chart_height = margin_top + plot_height + margin_bottom
    chart_width = 1100

    max_count = max(count for _, count in group_counts)
    usable_width = chart_width - margin_left - margin_right

    lines: list[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{chart_width}" height="{chart_height}">')
    lines.append('<style>text { font-family: Arial, sans-serif; font-size: 14px; }</style>')
    lines.append('<rect width="100%" height="100%" fill="white" />')
    lines.append(
        f'<text x="{chart_width / 2}" y="30" text-anchor="middle" font-size="20" font-weight="bold">聚合后类别 POI 数量统计</text>'
    )

    for idx, (name, count) in enumerate(reversed(group_counts)):
        y = margin_top + idx * (bar_height + bar_gap)
        bar_width = 0 if max_count == 0 else (count / max_count) * usable_width
        lines.append(f'<rect x="{margin_left}" y="{y}" width="{bar_width:.2f}" height="{bar_height}" fill="#4C78A8" />')
        lines.append(f'<text x="{margin_left - 10}" y="{y + bar_height * 0.68}" text-anchor="end">{escape_xml(name)}</text>')
        lines.append(f'<text x="{margin_left + bar_width + 8:.2f}" y="{y + bar_height * 0.68}">{count}</text>')

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

    fine_counts = write_fine_category_csv(parse_dataset(DATASET_PATH), OUTPUT_FINE_CSV)
    group_counts, group_mapping = aggregate_categories(fine_counts)
    write_group_csv(group_counts, OUTPUT_AGG_CSV)
    write_mapping_csv(group_mapping, OUTPUT_MAPPING_CSV)
    create_svg_bar_chart(group_counts, OUTPUT_CHART)

    print(f'总记录数: {sum(count for _, count in fine_counts)}')
    print(f'细分类别总数: {len(fine_counts)}')
    print(f'聚合后大类总数: {len(group_counts)}')
    print('聚合后 POI 数量（降序）:')
    for name, count in group_counts:
        print(f'- {name}: {count}')
    print(f'已输出细分类统计: {OUTPUT_FINE_CSV}')
    print(f'已输出大类统计: {OUTPUT_AGG_CSV}')
    print(f'已输出聚合关系: {OUTPUT_MAPPING_CSV}')
    print(f'已输出柱状图: {OUTPUT_CHART}')


if __name__ == '__main__':
    main()
