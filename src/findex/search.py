from __future__ import annotations

import tracemalloc
from time import perf_counter

from findex.index import OUT_PKL
from findex.models import Index
from findex.store import load_pickle

QUERY = "harry potter"
ENGINE = "merge"  # merge | set
BENCH_REPEATS = 200000


def merge_and(a: list[int], b: list[int]) -> list[int]:
    i = j = 0
    out: list[int] = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return out


def merge_or(a: list[int], b: list[int]) -> list[int]:
    i = j = 0
    out: list[int] = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            out.append(a[i])
            i += 1
        else:
            out.append(b[j])
            j += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out


def merge_not(a: list[int], b: list[int]) -> list[int]:
    i = j = 0
    out: list[int] = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
            j += 1
        elif a[i] < b[j]:
            out.append(a[i])
            i += 1
        else:
            j += 1
    out.extend(a[i:])
    return out


def set_and(a: list[int], b: list[int]) -> list[int]:
    return sorted(set(a) & set(b))


def set_or(a: list[int], b: list[int]) -> list[int]:
    return sorted(set(a) | set(b))


def set_not(a: list[int], b: list[int]) -> list[int]:
    return sorted(set(a) - set(b))


_OPS = {
    "merge": {"AND": merge_and, "OR": merge_or, "NOT": merge_not},
    "set": {"AND": set_and, "OR": set_or, "NOT": set_not},
}


def _ids(index: Index, term: str) -> list[int]:
    return [p.doc_id for p in index.postings.get(term, ())]


def search(index: Index, query: str, engine: str) -> list[int]:
    # "term term" is AND; OR / NOT bind the next term; left to right
    universe = sorted(index.doc_meta)
    acc: list[int] | None = None
    op = "AND"
    fn = _OPS[engine]
    for raw in query.split():
        word = raw.upper()
        if word in ("AND", "OR", "NOT"):
            op = word
            continue
        docs = _ids(index, raw.lower())
        if acc is None:
            acc = fn["NOT"](universe, docs) if op == "NOT" else docs
        else:
            acc = fn[op](acc, docs)
        op = "AND"
    return [] if acc is None else acc


def _freq(index: Index, term: str) -> int:
    return sum(p.tf for p in index.postings[term])


def bench(index: Index) -> None:
    if len(index.postings) < 2:
        print("bench skipped")
        return
    ranked = sorted(index.postings, key=lambda t: (_freq(index, t), t))
    pairs = (("rare", ranked[:2]), ("common", ranked[-2:]))
    for label, (left, right) in pairs:
        query = f"{left} {right}"
        for engine in ("merge", "set"):
            t0 = perf_counter()
            for _ in range(BENCH_REPEATS):
                search(index, query, engine)
            avg = (perf_counter() - t0) / BENCH_REPEATS
            print(
                f"{label} {left!r} tf={_freq(index, left)} "
                f"{right!r} tf={_freq(index, right)} {engine} {avg:.8f}s"
            )


def main() -> None:
    tracemalloc.start()
    t0 = perf_counter()
    index = load_pickle(OUT_PKL)
    hits = search(index, QUERY, ENGINE)
    elapsed = perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"\n{QUERY} ({ENGINE})")
    for doc_id in hits:
        print(f"  {doc_id}\t{index.doc_meta[doc_id].title}")
    print(f"search time={elapsed:.4f}s peak={peak / 1024:.1f}KiB")


if __name__ == "__main__":
    main()
