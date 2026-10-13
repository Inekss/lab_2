from __future__ import annotations

from findex.index import main as build_index
from findex.index import memory_study, positions_cost
from findex.search import bench
from findex.search import main as search_index


def main() -> None:
    index = build_index()
    positions_cost()
    memory_study()
    bench(index)
    search_index()


if __name__ == "__main__":
    main()
