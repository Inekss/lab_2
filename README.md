# findex

Inverted index over `src/resources/*.txt` — **one `.txt` file = one document**.

From `src/`: `python -m findex.index` builds and saves, `python -m findex.search` loads and searches, `python main.py` also prints the measurements below.

## Layout

- `src/findex/documents.py` — `CorpusReader.iter_docs()` (generator, one file at a time)
- `src/findex/models.py` — `Posting`, `DocMeta` (`frozen=True`, `slots=True`)
- `src/findex/index.py` — one pass, `defaultdict` + `Counter`
- `src/findex/search.py` — AND / OR / NOT, merge and set
- `src/findex/store.py` — pickle and json
- `src/main.py` — entry point

## Memory (tracemalloc)

Same corpus: 1 doc, 77600 tokens, 6103 terms. File size and load time are pickle. Load time is the median of 5.

| representation | peak (KiB) | file (bytes) | load (s) |
|----------------|------------|--------------|----------|
| plain dataclass | 2379.3 | 205200 | 0.0052 |
| `slots=True` | 2182.4 | 168548 | 0.0090 |
| `array('I')` pairs | 2802.2 | 315038 | 0.0048 |

**Where the bytes went:** a slotted `Posting` is 56 bytes, fields in the object. A plain instance adds a `__dict__`. `sys.getsizeof` on that dict is 296 bytes because it counts the shared key table; CPython keeps one key table for the class and a small values array per instance, so the build pays about 33 extra bytes per posting — 197 KiB across 6103 terms (2379.3 vs 2182.4). An `array('I')` holding one int is 96 bytes. Each term gets two of them, and every list here has length 1, so the headers are the cost: peak 2802.2 KiB and a 315038-byte pickle. The 4-byte ints show up once a term's list is long enough to spread those two headers across many doc ids.

## merge vs set

Mean of 200000 `search()` calls. `term term` is AND. Both postings lists have length 1.

| pair | query | tf | engine | mean (s) |
|------|-------|----|--------|----------|
| rare | `1473 1637` | 1, 1 | merge | 0.00000086 |
| rare | `1473 1637` | 1, 1 | set | 0.00000104 |
| common | `and the` | 1919, 3628 | merge | 0.00000054 |
| common | `and the` | 1919, 3628 | set | 0.00000054 |

`and` / `the` tie. On the rare pair merge is faster: `set` builds two hash sets for a one-element AND. The lists are the same length, so the gap is that allocation.

## Save / load

Slots index, positions off. Times are the median of 5.

| format | size (bytes) | save (s) | load (s) |
|--------|--------------|----------|----------|
| pickle | 168528 | 0.0095 | 0.0095 |
| json | 151307 | 0.0045 | 0.0072 |

`pickle.load` runs whatever the file asks it to. Load only an index this program wrote.

## Positions

`WITH_POSITIONS` in `src/findex/index.py`. Off by default.

| positions | peak (KiB) | pickle (bytes) |
|-----------|------------|----------------|
| off | 2182.7 | 168528 |
| on | 6428.3 | 433364 |

Peak rises from 2182.7 KiB to 6428.3 KiB. The 77600 token offsets are stored as Python ints on each posting.
