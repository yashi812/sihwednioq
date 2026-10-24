#!/usr/bin/env python3
"""Build readable English SRT captions from timestamped speech-to-text JSON."""
from __future__ import annotations

import argparse
import json
import re
import textwrap
from pathlib import Path
from typing import Any


def normalize(text: str) -> str:
    """Use the product and Elexon dataset spellings in the spoken captions."""
    text = re.sub(r"\bWind\s+Desk\b", "WindDesk", text, flags=re.IGNORECASE)
    text = re.sub(r"\bWind\s+Four\b", "WINDFOR", text, flags=re.IGNORECASE)
    text = re.sub(r"\bFuel\s+HH\b", "FUELHH", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def wrap_chunks(text: str, width: int, max_lines: int) -> list[str]:
    lines = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)
    if not lines:
        return []
    return ["\n".join(lines[i:i + max_lines]) for i in range(0, len(lines), max_lines)]


def stamp(seconds: float) -> str:
    total_ms = max(0, round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"


def cues_for(path: Path, offset: float, width: int, max_lines: int) -> list[tuple[float, float, str]]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    raw_segments = data.get("segments", [])
    segments: list[dict[str, Any]] = []
    for raw in raw_segments:
        if segments:
            previous = segments[-1]
            gap = float(raw.get("start", 0.0)) - float(previous.get("end", 0.0))
            previous_text = str(previous.get("text", "")).rstrip()
            has_sentence_end = re.search(r"[.!?][\"'’”\)\]]?$", previous_text) is not None
            if gap <= 0.20 and not has_sentence_end:
                previous["text"] = f"{previous_text} {raw.get('text', '')}".strip()
                previous["end"] = max(float(previous.get("end", 0.0)), float(raw.get("end", 0.0)))
                continue
        segments.append(dict(raw))
    cues: list[tuple[float, float, str]] = []
    for segment in segments:
        text = normalize(str(segment.get("text", "")))
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", start))
        if not text or end <= start:
            continue
        chunks = wrap_chunks(text, width, max_lines)
        if not chunks:
            continue
        weights = [max(1, len(chunk.replace("\n", " ").split())) for chunk in chunks]
        total_weight = sum(weights)
        cursor = start
        duration = end - start
        for chunk, weight in zip(chunks, weights):
            next_cursor = cursor + duration * weight / total_weight
            cues.append((cursor + offset, next_cursor + offset, chunk))
            cursor = next_cursor
    merged: list[tuple[float, float, str]] = []
    for cue_start, cue_end, cue_text in cues:
        if merged and cue_end - cue_start < 1.2:
            previous_start, previous_end, previous_text = merged[-1]
            previous_flat = previous_text.replace("\n", " ").rstrip()
            has_sentence_end = re.search(r"[.!?][\"'’”\)\]]?$", previous_flat) is not None
            if cue_start - previous_end <= 0.12 and not has_sentence_end:
                combined = f"{previous_flat} {cue_text.replace(chr(10), ' ')}".strip()
                chunks = wrap_chunks(combined, width, max_lines)
                if len(chunks) == 1:
                    merged[-1] = (previous_start, max(previous_end, cue_end), chunks[0])
                    continue
        merged.append((cue_start, cue_end, cue_text))
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Timestamped speech-to-text JSON file(s), in playback order")
    parser.add_argument("--output", required=True, type=Path, help="Destination SRT file")
    parser.add_argument("--offsets", nargs="*", type=float, help="Offset in seconds for each input; defaults to zero")
    parser.add_argument("--width", type=int, default=52, help="Maximum characters per caption line")
    parser.add_argument("--max-lines", type=int, default=2, help="Maximum lines per cue")
    args = parser.parse_args()

    offsets = args.offsets or [0.0] * len(args.inputs)
    if len(offsets) != len(args.inputs):
        parser.error("provide exactly one --offsets value per input transcript")
    if args.width < 20 or args.max_lines < 1:
        parser.error("--width must be at least 20 and --max-lines at least 1")

    cues: list[tuple[float, float, str]] = []
    for path, offset in zip(args.inputs, offsets):
        cues.extend(cues_for(path, offset, args.width, args.max_lines))

    blocks = []
    for number, (start, end, text) in enumerate(cues, start=1):
        blocks.append(f"{number}\n{stamp(start)} --> {stamp(end)}\n{text}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    print(f"Wrote {len(cues)} cues to {args.output}")


if __name__ == "__main__":
    main()
