import hashlib

from PIL import Image, ImageDraw
import pytest

from mdx_printkit.errors import AssetError
from mdx_printkit.gif import extract_frames


@pytest.mark.parametrize("maximum", [1, 4, 6, 12])
def test_distinct_time_ordered_frames(tmp_path, animated_gif, maximum):
    result = extract_frames(animated_gif, tmp_path / "frames", maximum)
    assert len(result.paths) == min(maximum, 9)
    assert result.indices == sorted(result.indices)
    digests = []
    for path in result.paths:
        with Image.open(path) as frame:
            digests.append(hashlib.sha256(frame.tobytes()).hexdigest())
    assert len(set(digests)) == len(digests)
    if maximum == 1:
        assert result.indices == [2]  # The long third frame spans the elapsed-time midpoint.
    else:
        assert result.indices[0] == 0
        assert result.indices[-1] == 9


def test_static_gif(tmp_path):
    path = tmp_path / "static.gif"
    Image.new("RGB", (20, 20), "red").save(path)
    result = extract_frames(path, tmp_path / "frames")
    assert len(result.paths) == 1 and not result.animated


def test_transparency_disposal_and_compositing(tmp_path):
    path = tmp_path / "transparent.gif"
    frames = []
    for index in range(4):
        frame = Image.new("RGBA", (60, 20), (0, 0, 0, 0))
        ImageDraw.Draw(frame).rectangle((index * 12, 4, index * 12 + 8, 12), fill=(255, 0, 0, 255))
        frames.append(frame)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=100,
                   transparency=0, disposal=2, optimize=False)
    result = extract_frames(path, tmp_path / "out")
    for index, output in zip(result.indices, result.paths):
        with Image.open(output) as image:
            assert image.getpixel((index * 12 + 3, 7)) == (255, 0, 0, 255)
            assert image.getpixel((59, 19))[3] == 0
            if index:
                assert image.getpixel((3, 7))[3] == 0


def test_gif_decode_bound(tmp_path, animated_gif, monkeypatch):
    monkeypatch.setattr("mdx_printkit.gif.MAX_FRAMES", 2)
    with pytest.raises(AssetError, match="limit"):
        extract_frames(animated_gif, tmp_path / "out")
