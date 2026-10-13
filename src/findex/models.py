from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StatsResult:
    n_docs: int
    n_tokens: int
    vocab_size: int
    top50: list[tuple[str, int]]
    elapsed_s: float
    peak_kib: float


@dataclass(frozen=True)
class PostingPlain:
    doc_id: int
    tf: int
    positions: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class Posting:
    doc_id: int
    tf: int
    positions: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class DocMeta:
    path: str
    title: str


@dataclass(frozen=True, slots=True)
class Index:
    postings: dict[str, list[Posting]]
    doc_lengths: dict[int, int]
    doc_meta: dict[int, DocMeta]
