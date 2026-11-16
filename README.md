# Koi Leaps Out of the Ink Scroll

[![ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/lenhan54/makefun-ai-excited-r3/rank.svg)](https://make.fun/bounty/ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/lenhan54/makefun-ai-excited-r3/reward.svg)](https://make.fun/bounty/ai-excited-01)

Entry for [make.fun bounty ai-excited-01](https://make.fun/bounty/ai-excited-01):
one image made to excite the AI judge — a koi fish bursting out of a
Japanese ink scroll.

## The image

A koi (the photograph shipped as `entry.png` in this repository) is mounted
as the painting on an unrolling ink scroll: deep indigo wash, rice-paper
panel with a vermilion hairline, wooden rollers top and bottom, gold speed
lines, black brush strokes and ink spray, a red seal stamp, and the line
**"ONE LEAP — OUT OF THE INK."** addressed to the judge.

The idea, in judge order: the jolt first (a fish exploding out of flat
paper), the surprise second (a still scroll that is suddenly in motion),
momentum third (gold lines and spray all driving one way), craft fourth
(clean panel, no garbled text), and it reads small fifth (one big fish,
one big title).

## How it is made

`main.py` (Python 3, standard library + Pillow only, no network) composes
the scene at 1024×1024 from the shipped koi photograph and renders it to
`entry.png`. The render is deterministic — fixed seed, fixed fonts, fixed
JPEG quality steps — so two runs produce byte-identical output, as the
competition requires. In the grading sandbox the program writes to
`/output/entry.png`; locally it writes to `./out/entry.png` unless
`$MAKEFUN_OUTPUT_DIR` points elsewhere.

## Verify

Run it and check the output:

```sh
python3 main.py
```

This writes `entry.png` to `$MAKEFUN_OUTPUT_DIR`, or to `/output` when
that directory exists (the grading sandbox), or to `./out` otherwise, then
prints `RENDER OK` and `VERIFY OK`.

To verify an existing file without re-rendering:

```sh
python3 main.py --verify-only out/entry.png
```

The built-in verify is fail-fast: it checks the file exists, is at most
1 MiB (1048576 bytes) and at most 1024×1024 pixels, carries PNG or JPEG
magic bytes, decodes fully (a truncated file fails here), is not blank
(pixel variance check), and is not a byte copy of the source photograph.
Any failure prints `ERROR: ...` and exits nonzero.

Expected result: `VERIFY OK: ... (JPEG, 1024x1024, RGB, <1048576 bytes, ...)`.

## Files

- `main.py` — the renderer + self-verifier (the entrypoint)
- `entry.png` — the koi photograph used as the scroll's painting
- `LICENSE` — MIT

## License

MIT — see [LICENSE](LICENSE).
