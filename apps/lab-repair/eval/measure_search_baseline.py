# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Đường cơ sở cho bộ 20 câu hỏi tìm kiếm (queries.json): xếp hạng từ khóa TF-IDF, bỏ dấu, không vector.

Chạy từ gốc repo (cần data/sop/*.md của APP-03):

    python3 apps/lab-repair/eval/measure_search_baseline.py [--sop-dir data/sop]

Chỉ dùng thư viện chuẩn. Mục đích: cho CORE-08 (FTS + zvec) một mốc để so sánh trên cùng bộ câu hỏi, không phải
bộ máy tìm kiếm của sản phẩm.
"""

import argparse
import json
import math
import pathlib
import re
import sys
import unicodedata


def fold(text):
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9]+", fold(text)) if len(t) > 1]


def main():
    here = pathlib.Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sop-dir", default="data/sop")
    ap.add_argument("--queries", default=str(here / "queries.json"))
    args = ap.parse_args()
    docs = {p.stem: tokens(p.read_text(encoding="utf-8")) for p in sorted(pathlib.Path(args.sop_dir).glob("*.md"))}
    if not docs:
        sys.exit(f"Không có tệp .md trong {args.sop_dir}")
    n_docs = len(docs)
    df = {}
    for toks in docs.values():
        for t in set(toks):
            df[t] = df.get(t, 0) + 1

    def score(q, toks):
        return sum((1 + math.log(toks.count(t))) * math.log(1 + n_docs / df[t]) for t in set(q) if t in df and t in toks)

    queries = json.loads(pathlib.Path(args.queries).read_text(encoding="utf-8"))
    top1 = top3 = pos = 0
    print(f"{n_docs} tài liệu, {len(queries)} câu hỏi\n")
    print("| # | Câu hỏi | Mong đợi | Top-1 (điểm) | Hạng đúng |")
    print("|---|---|---|---|---|")
    for q in queries:
        qt = tokens(q["query"])
        ranked = sorted(((score(qt, toks), d) for d, toks in docs.items()), reverse=True)
        best_s, best_d = ranked[0]
        exp = q["expected_sop"]
        if exp is None:
            print(f"| {q['id']} | {q['query']} | (không có) | {best_d if best_s else '—'} ({best_s:.2f}) | — |")
            continue
        pos += 1
        rank = next((i for i, (s, d) in enumerate(ranked, 1) if d == exp), None)
        top1 += rank == 1
        top3 += rank is not None and rank <= 3
        print(f"| {q['id']} | {q['query']} | {exp} | {best_d} ({best_s:.2f}) | {rank} |")
    print(f"\nTop-1: {top1}/{pos} = {100 * top1 / pos:.1f}%   Top-3: {top3}/{pos} = {100 * top3 / pos:.1f}%")


if __name__ == "__main__":
    main()
