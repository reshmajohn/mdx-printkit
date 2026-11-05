"""Time-based sampling of Pillow's fully composited GIF frames."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import hashlib
from pathlib import Path

from PIL import Image, ImageOps

from .errors import AssetError

MAX_FRAMES = 500
MAX_DECODED_PIXELS = 250_000_000


@dataclass(frozen=True)
class Storyboard:
    paths: list[Path]
    indices: list[int]
    animated: bool


def extract_frames(path: Path, destination: Path, maximum: int = 4) -> Storyboard:
    if not 1 <= maximum <= 12:
        raise ValueError("GIF frame count must be between 1 and 12")
    destination.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(path) as gif:
            hashes, starts = [], []
            elapsed = 0
            for index in range(MAX_FRAMES + 1):
                try:
                    gif.seek(index)
                except EOFError:
                    break
                if index >= MAX_FRAMES or (index + 1) * gif.width * gif.height > MAX_DECODED_PIXELS:
                    raise AssetError("GIF exceeds the 500-frame / 250-million decoded-pixel limit")
                # Pillow seek applies the GIF disposal method and prior frame compositing.
                rgba = gif.convert("RGBA")
                hashes.append(hashlib.sha256(rgba.tobytes()).digest())
                starts.append(elapsed)
                duration = max(10, int(gif.info.get("duration", 100) or 100))
                elapsed += duration

            times = [elapsed / 2] if maximum == 1 else [
                (elapsed - 1) * i / (maximum - 1) for i in range(maximum)
            ]
            if maximum > 1:
                # Reserve the final visual state before deduplicating interior samples.
                times = [times[0], times[-1], *times[1:-1]]
            selected: list[int] = []
            seen = set()
            for moment in times:
                index = bisect_right(starts, moment) - 1
                if hashes[index] not in seen:
                    selected.append(index)
                    seen.add(hashes[index])
            # Repeated states at sample times must not hide other distinct visual states.
            while len(selected) < min(maximum, len(set(hashes))):
                candidates = [i for i, digest in enumerate(hashes) if digest not in seen]
                index = max(candidates, key=lambda i: min(abs(starts[i] - starts[j]) for j in selected))
                selected.append(index)
                seen.add(hashes[index])
            selected.sort()
            paths = []
            for number, index in enumerate(selected):
                gif.seek(index)
                frame = gif.convert("RGBA")
                frame.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                output = destination / f"frame-{number + 1}.png"
                frame.save(output)
                paths.append(output)
            return Storyboard(paths, selected, len(hashes) > 1)
    except AssetError:
        raise
    except (OSError, ValueError, EOFError) as exc:
        raise AssetError(f"cannot decode GIF: {exc}") from exc


def normalize_image(path: Path, destination: Path) -> None:
    try:
        with Image.open(path) as image:
            image.seek(0)
            image = ImageOps.exif_transpose(image)
            image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
            image.convert("RGBA").save(destination, format="PNG")
    except (OSError, ValueError, EOFError) as exc:
        raise AssetError(f"cannot decode image: {exc}") from exc
