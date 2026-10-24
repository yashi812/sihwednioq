#!/usr/bin/env python3
"""Build WindDesk's two-part narrated demo from reproducible PNG scenes and WAV narration."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
W, H = 1280, 720
INK = "#10242f"
INK2 = "#183540"
INK3 = "#24424b"
TEAL = "#67c7b5"
TEAL2 = "#419b89"
LIME = "#c9e674"
SAND = "#d6c9a9"
PAPER = "#f4f6f3"
MUTED = "#9aafaa"
WHITE = "#f5f8f5"
GRID = "#ffffff12"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def font(size: int, weight: str = "regular", mono: bool = False) -> ImageFont.FreeTypeFont:
    path = MONO_BOLD if mono and weight == "bold" else MONO if mono else SANS_BOLD if weight == "bold" else SANS
    return ImageFont.truetype(path, size)


def canvas() -> Image.Image:
    image = Image.new("RGB", (W, H), INK)
    gradient = ImageDraw.Draw(image)
    for y in range(H):
        t = y / H
        top = (16, 36, 47)
        bottom = (21, 48, 58)
        color = tuple(int(a * (1 - t) + b * t) for a, b in zip(top, bottom))
        gradient.line((0, y, W, y), fill=color)
    draw = ImageDraw.Draw(image, "RGBA")
    for x in range(40, W, 48):
        draw.line((x, 0, x, H), fill=(180, 220, 205, 8), width=1)
    for y in range(42, H, 48):
        draw.line((0, y, W, y), fill=(180, 220, 205, 7), width=1)
    draw.ellipse((W - 320, -230, W + 130, 220), outline=(103, 199, 181, 26), width=1)
    draw.ellipse((W - 280, -190, W + 90, 180), outline=(103, 199, 181, 16), width=1)
    return image


def header(draw: ImageDraw.ImageDraw, number: str, section: str) -> None:
    draw.rounded_rectangle((54, 34, 82, 62), radius=8, fill="#214b50", outline="#35786f", width=1)
    draw.arc((60, 40, 78, 54), start=190, end=345, fill=TEAL, width=2)
    draw.line((61, 52, 76, 52), fill=TEAL, width=2)
    draw.text((94, 35), "winddesk", font=font(19, "bold"), fill=WHITE)
    draw.text((224, 44), "FORECAST INTELLIGENCE", font=font(9, mono=True), fill=MUTED)
    draw.line((54, 81, W - 54, 81), fill="#ffffff24", width=1)
    draw.text((W - 365, 45), f"{number}   /   {section.upper()}", font=font(10, mono=True), fill=TEAL)


def wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, max_width: int,
            fnt: ImageFont.FreeTypeFont, fill: str, line_gap: int = 8) -> int:
    x, y = xy
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textbbox((0, 0), trial, font=fnt)[2] <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += int(fnt.size) + line_gap
    return y


def heading(image: Image.Image, eyebrow: str, title: str, subtitle: str | None = None) -> int:
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((57, 107, 64, 124), radius=3, fill=TEAL)
    d.text((76, 108), eyebrow.upper(), font=font(10, mono=True), fill=TEAL)
    d.text((56, 145), title, font=font(31, "bold"), fill=WHITE)
    if subtitle:
        wrapped(d, (58, 194), subtitle, 1164, font(14), MUTED, 6)
    return 222


def crop_card(image: Image.Image, source_image: Image.Image, crop: tuple[int, int, int, int], box: tuple[int, int, int, int], radius: int = 9) -> None:
    x, y, w, h = box
    source = source_image.crop(crop).convert("RGB")
    source = ImageOps.fit(source, (w, h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    shadow = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((8, 8, w + 8, h + 8), radius=radius + 2, fill=(0, 0, 0, 105))
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    image.paste(shadow, (x - 8, y - 2), shadow)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    image.paste(source, (x, y), mask)
    ImageDraw.Draw(image).rounded_rectangle((x, y, x + w - 1, y + h - 1), radius=radius, outline="#ffffff54", width=1)


def text_panel(image: Image.Image, label: str, title: str, body: str, y: int = 246, width: int = 300) -> None:
    d = ImageDraw.Draw(image)
    d.text((58, y), label.upper(), font=font(9, mono=True), fill=TEAL)
    d.text((58, y + 28), title, font=font(24, "bold"), fill=WHITE)
    wrapped(d, (58, y + 70), body, width, font(13), MUTED, 7)


def pill(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, value: str, color: str = TEAL) -> None:
    draw.rounded_rectangle((x, y, x + 220, y + 79), radius=8, fill="#1a3741", outline="#ffffff25", width=1)
    draw.text((x + 13, y + 11), text.upper(), font=font(8, mono=True), fill=MUTED)
    draw.text((x + 13, y + 34), value, font=font(20, "bold"), fill=color)


def scene_01(screen: Image.Image) -> Image.Image:
    im = canvas(); d = ImageDraw.Draw(im); header(d, "01", "Client pilot")
    d.text((58, 112), "A clearer view of", font=font(31, "bold"), fill=WHITE)
    d.text((58, 151), "wind forecast risk.", font=font(31, "bold"), fill=TEAL)
    wrapped(d, (60, 207), "Decision-time forecast. Measured outturn. One traceable view.", 340, font(14), MUTED, 7)
    pill(d, 58, 318, "Monthly MAE", "2,122.8 MW")
    pill(d, 58, 412, "Matched hourly points", "744 / 744", LIME)
    d.text((60, 535), "JANUARY 2026  ·  GB NATIONAL WIND", font=font(9, mono=True), fill="#9cb4ad")
    crop_card(im, screen, (250, 180, 1270, 800), (414, 112, 810, 493), 9)
    return im


def scene_02(screen: Image.Image) -> Image.Image:
    im = canvas(); d = ImageDraw.Draw(im); header(d, "02", "Decision cutoff")
    heading(im, "01 / DECISION CONTEXT", "Pin the forecast to a decision time", "Choose the delivery day and local cutoff; keep the Elexon publication timestamp visible.")
    crop_card(im, screen, (250, 187, 1414, 270), (66, 254, 1148, 100), 7)
    d = ImageDraw.Draw(im)
    points = [(127, 444, "DELIVERY DAY", "15 Jan"), (411, 444, "FORECAST PUBLISHED", "14 Jan · 09:30 GMT"), (815, 444, "PILOT CUTOFF", "14 Jan · 11:00 GMT")]
    for x, y, label, value in points:
        d.ellipse((x, y, x + 11, y + 11), fill=TEAL if x != 815 else SAND)
        d.text((x + 22, y - 2), label, font=font(9, mono=True), fill=MUTED)
        d.text((x + 22, y + 25), value, font=font(16, "bold"), fill=WHITE)
    d.line((139, 450, 997, 450), fill="#68b8a85c", width=2)
    d.rounded_rectangle((67, 548, 1213, 618), radius=7, fill="#193640", outline="#ffffff22")
    d.text((88, 565), "VINTAGE RULE", font=font(9, mono=True), fill=TEAL)
    d.text((245, 561), "Score only the Elexon vintage published at or before the configured cutoff.", font=font(15), fill=WHITE)
    return im


def scene_03(screen: Image.Image) -> Image.Image:
    im = canvas(); d = ImageDraw.Draw(im); header(d, "03", "Hourly comparison")
    heading(im, "01 / DELIVERY PROFILE", "Follow the shape, not just the score", "Forecast and actual stay distinct across the full twenty-four hour delivery profile.")
    crop_card(im, screen, (250, 399, 1022, 789), (105, 260, 1070, 360), 8)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((105, 640, 1175, 684), radius=5, fill="#193640", outline="#ffffff20")
    d.text((123, 654), "TEAL", font=font(9, mono=True), fill=TEAL)
    d.text((186, 652), "WINDFOR forecast", font=font(12), fill=WHITE)
    d.text((429, 654), "SAND", font=font(9, mono=True), fill=SAND)
    d.text((492, 652), "FUELHH actual", font=font(12), fill=WHITE)
    d.text((954, 654), "24 / 24 HOURS SCORED", font=font(9, mono=True), fill=LIME)
    return im


def scene_04(screen: Image.Image) -> Image.Image:
    im = canvas(); d = ImageDraw.Draw(im); header(d, "04", "January view")
    heading(im, "01 / DAILY ERROR PROFILE", "Compare performance across the month", "Each bar is the daily mean absolute error in megawatts; select a day to inspect its profile.")
    crop_card(im, screen, (250, 792, 1417, 1028), (95, 258, 1090, 220), 8)
    d = ImageDraw.Draw(im)
    pill(d, 95, 518, "Matched hours", "744", TEAL)
    pill(d, 330, 518, "Delivery days", "31", LIME)
    pill(d, 565, 518, "Unmatched hours", "0", SAND)
    d.text((95, 633), "The daily chart is an inspection aid — not a market price or purchase-volume signal.", font=font(12), fill=MUTED)
    return im


def scene_05(screen: Image.Image) -> Image.Image:
    im = canvas(); d = ImageDraw.Draw(im); header(d, "05", "Pilot evidence")
    heading(im, "01 / MONTHLY SCORECARD", "Quantify the miss — and show the sample", "Monthly metrics use matched hourly forecast and actual observations only.")
    crop_card(im, screen, (250, 1032, 1417, 1497), (68, 253, 1144, 394), 8)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((68, 664, 1212, 695), radius=4, fill="#16353f")
    d.text((83, 672), "BIAS = FORECAST − ACTUAL", font=font(9, mono=True), fill=TEAL)
    d.text((416, 671), "Positive bias means over-forecast on average.", font=font(11), fill=WHITE)
    return im


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = TEAL) -> None:
    x1, y1 = start; x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=color, width=3)
    if x2 >= x1:
        draw.polygon([(x2, y2), (x2 - 12, y2 - 7), (x2 - 12, y2 + 7)], fill=color)
    else:
        draw.polygon([(x2, y2), (x2 + 12, y2 - 7), (x2 + 12, y2 + 7)], fill=color)


def box(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], title: str, subtitle: str, accent: str = TEAL) -> None:
    x1, y1, x2, y2 = rect
    draw.rounded_rectangle(rect, radius=11, fill="#1a3742", outline="#ffffff32", width=1)
    draw.rounded_rectangle((x1 + 17, y1 + 16, x1 + 24, y1 + 47), radius=3, fill=accent)
    draw.text((x1 + 38, y1 + 16), title, font=font(17, "bold"), fill=WHITE)
    wrapped(draw, (x1 + 38, y1 + 51), subtitle, x2 - x1 - 56, font(10), MUTED, 4)


def scene_06() -> Image.Image:
    im = canvas(); d = ImageDraw.Draw(im); header(d, "06", "Technical lead")
    heading(im, "02 / TECHNICAL HANDOFF", "A small, auditable path from source to score", "Same-origin API. Elexon-only observations. Deterministic hourly analysis.")
    box(d, (72, 283, 340, 400), "React + TypeScript", "Filters · charts · table · CSV", TEAL)
    box(d, (455, 283, 723, 400), "FastAPI", "Cutoff · cache · validation · JSON", LIME)
    box(d, (858, 207, 1168, 327), "Elexon BMRS", "WINDFOR historical wind forecast", SAND)
    box(d, (858, 365, 1168, 485), "Elexon BMRS", "FUELHH actuals · fuelType WIND", SAND)
    box(d, (455, 485, 723, 602), "Analysis module", "Exact join · MAE · RMSE · bias", TEAL)
    arrow(d, (340, 342), (455, 342), TEAL)
    arrow(d, (723, 313), (858, 267), LIME)
    arrow(d, (723, 365), (858, 424), LIME)
    d.line((858, 267, 800, 267, 800, 520, 735, 520), fill=SAND, width=3)
    d.polygon([(723, 520), (735, 513), (735, 527)], fill=SAND)
    d.line((858, 425, 818, 425, 818, 552, 735, 552), fill=SAND, width=3)
    d.polygon([(723, 552), (735, 545), (735, 559)], fill=SAND)
    arrow(d, (455, 535), (340, 378), TEAL)
    d.rounded_rectangle((74, 631, 1168, 680), radius=6, fill="#193640", outline="#ffffff20")
    d.text((91, 648), "READ-ONLY PILOT", font=font(9, mono=True), fill=TEAL)
    d.text((264, 644), "No database · no synthetic fallback · no browser-to-Elexon calls", font=font(14), fill=WHITE)
    return im


def scene_07() -> Image.Image:
    im = canvas(); d = ImageDraw.Draw(im); header(d, "07", "Vintage retrieval")
    heading(im, "02 / DATA HANDLING", "Select what was available by cutoff", "The configured time applies to the preceding day in Europe/London; the API response time is retained.")
    xs = [95, 368, 641, 914]
    steps = [
        ("01", "DELIVERY DATE", "January 2026"),
        ("02", "LOCAL CUTOFF", "Previous day · 11:00"),
        ("03", "ELEXON RESPONSE", "publishTime retained"),
        ("04", "VINTAGE CHECK", "Reject after cutoff"),
    ]
    for i, (x, item) in enumerate(zip(xs, steps)):
        n, title, desc = item
        d.rounded_rectangle((x, 293, x + 225, 426), radius=9, fill="#1a3742", outline="#ffffff31")
        d.text((x + 16, 311), n, font=font(10, mono=True), fill=TEAL)
        d.text((x + 16, 344), title, font=font(11, "bold", mono=True), fill=WHITE)
        d.text((x + 16, 376), desc, font=font(11), fill=MUTED)
        if i < len(xs) - 1:
            arrow(d, (x + 230, 359), (xs[i + 1] - 10, 359), TEAL)
    d.rounded_rectangle((95, 476, 1139, 565), radius=8, fill="#183942", outline="#ffffff22")
    d.text((115, 497), "CACHE", font=font(9, mono=True), fill=LIME)
    d.text((233, 493), "15-minute in-memory responses · bounded retries · explicit upstream errors", font=font(14), fill=WHITE)
    d.text((115, 529), "Missing forecasts remain unscored; no values are generated or interpolated.", font=font(11), fill=MUTED)
    return im


def scene_08() -> Image.Image:
    im = canvas(); d = ImageDraw.Draw(im); header(d, "08", "Score definitions")
    heading(im, "02 / ANALYTICAL METHOD", "Match first. Score only complete pairs.", "A fair comparison preserves the half-hour actual resolution and shows coverage with every monthly score.")
    d.rounded_rectangle((67, 261, 731, 599), radius=9, fill="#142d38", outline="#ffffff28")
    d.text((91, 283), "backend/app/analysis.py", font=font(11, mono=True), fill=TEAL)
    code = [
        ("01", "errors = [forecast - actual for each matched hour]"),
        ("02", "mae  = mean(abs(error) for error in errors)"),
        ("03", "rmse = sqrt(mean(error * error for error in errors))"),
        ("04", "bias = mean(errors)"),
    ]
    yy = 337
    for no, line in code:
        d.text((92, yy), no, font=font(11, mono=True), fill="#69827e")
        wrapped(d, (134, yy - 1), line, 560, font(13, mono=True), WHITE, 5)
        yy += 54
    pill(d, 789, 275, "Monthly MAE", "2,122.8 MW", TEAL)
    pill(d, 789, 368, "Monthly RMSE", "2,616.7 MW", LIME)
    pill(d, 789, 461, "Mean bias", "+1,840.3 MW", SAND)
    d.text((790, 565), "744 / 744 MATCHED", font=font(10, mono=True), fill=TEAL)
    d.text((790, 588), "31 January delivery days", font=font(11), fill=MUTED)
    return im


def scene_09() -> Image.Image:
    im = canvas(); d = ImageDraw.Draw(im); header(d, "09", "Code and checks")
    heading(im, "02 / REPOSITORY WALKTHROUGH", "Separated modules keep the pilot reviewable", "The data client, analytics and user interface have clear responsibilities.")
    d.rounded_rectangle((75, 265, 638, 625), radius=9, fill="#142d38", outline="#ffffff27")
    tree = [
        ("winddesk/", TEAL),
        ("├── frontend/", WHITE),
        ("│   └── src/App.tsx", MUTED),
        ("├── backend/app/", WHITE),
        ("│   ├── elexon.py", MUTED),
        ("│   ├── analysis.py", MUTED),
        ("│   └── main.py", MUTED),
        ("├── backend/tests/", WHITE),
        ("├── Dockerfile", MUTED),
        ("└── README.md", MUTED),
    ]
    y = 288
    for line, color in tree:
        d.text((99, y), line, font=font(16 if line == "winddesk/" else 13, mono=True), fill=color)
        y += 31
    d.rounded_rectangle((686, 265, 1198, 625), radius=9, fill="#1a3742", outline="#ffffff27")
    d.rounded_rectangle((713, 292, 775, 351), radius=12, fill="#214b50")
    d.text((729, 303), "4", font=font(29, "bold"), fill=LIME)
    d.text((791, 303), "DETERMINISTIC TESTS", font=font(10, mono=True), fill=TEAL)
    items = ["Half-hour to hourly averaging", "Incomplete-pair handling", "Forecast-minus-actual sign", "Scoring coverage and missing values"]
    y = 389
    for item in items:
        d.ellipse((718, y + 5, 726, y + 13), fill=LIME)
        d.text((741, y), item, font=font(12), fill=WHITE)
        y += 43
    d.text((714, 576), "4 passed  ·  TypeScript build successful", font=font(10, mono=True), fill=MUTED)
    return im


def scene_10() -> Image.Image:
    im = canvas(); d = ImageDraw.Draw(im); header(d, "10", "Build and handoff")
    heading(im, "02 / RUN AND RELEASE", "One container. A simple local start.", "Vite builds the dashboard; FastAPI serves the API and compiled static files in production.")
    d.rounded_rectangle((70, 269, 763, 625), radius=9, fill="#142d38", outline="#ffffff29")
    d.text((95, 291), "LOCAL DEVELOPMENT", font=font(10, mono=True), fill=TEAL)
    commands = [
        "$ python3 -m venv backend/.venv",
        "$ python -m pip install -r backend/requirements.txt",
        "$ pnpm install && pnpm dev",
        "$ docker compose up --build",
    ]
    yy = 346
    for i, line in enumerate(commands):
        d.rounded_rectangle((92, yy - 4, 732, yy + 38), radius=5, fill="#1b3944" if i != 3 else "#244c50")
        d.text((110, yy + 6), line, font=font(12, mono=True), fill=WHITE)
        yy += 61
    d.rounded_rectangle((802, 269, 1198, 625), radius=9, fill="#1a3742", outline="#ffffff29")
    d.text((829, 293), "DEPLOYMENT SHAPE", font=font(9, mono=True), fill=TEAL)
    d.text((829, 338), "Heroku container", font=font(21, "bold"), fill=WHITE)
    d.text((829, 372), "web process", font=font(21, "bold"), fill=WHITE)
    d.line((829, 424, 1169, 424), fill="#ffffff30")
    d.text((829, 450), "PORT-aware listener", font=font(12), fill=MUTED)
    d.text((829, 480), "Unauthenticated /health", font=font(12), fill=MUTED)
    d.text((829, 510), "No database required", font=font(12), fill=MUTED)
    d.rounded_rectangle((829, 557, 1170, 594), radius=5, fill="#214b50")
    d.text((850, 567), "TRACEABLE  ·  READ-ONLY  ·  REVIEWABLE", font=font(8, mono=True), fill=LIME)
    return im


def build_scenes(screenshot: Path, scene_dir: Path) -> None:
    scene_dir.mkdir(parents=True, exist_ok=True)
    screen = Image.open(screenshot).convert("RGB")
    frames = [scene_01(screen), scene_02(screen), scene_03(screen), scene_04(screen), scene_05(screen),
              scene_06(), scene_07(), scene_08(), scene_09(), scene_10()]
    for index, frame in enumerate(frames, start=1):
        path = scene_dir / f"scene-{index:02d}.png"
        frame.save(path, optimize=True)
        print(f"Rendered {path}")


def duration(path: Path) -> float:
    value = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True).strip()
    return float(value)


def encode_scene(image: Path, wav: Path, output: Path) -> None:
    seconds = duration(wav)
    fade_out = max(0.3, seconds - 0.28)
    vf = (
        "zoompan=z='min(zoom+0.00012,1.035)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        "d=1:s=1280x720:fps=30,"
        f"fade=t=in:st=0:d=0.3,fade=t=out:st={fade_out:.2f}:d=0.26,format=yuv420p"
    )
    af = f"afade=t=in:st=0:d=0.08,afade=t=out:st={max(0.0,seconds-0.18):.2f}:d=0.16"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-framerate", "30", "-i", str(image), "-i", str(wav),
        "-vf", vf, "-af", af, "-t", f"{seconds:.3f}", "-shortest",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", str(output)
    ], check=True)
    print(f"Encoded {output.name} ({seconds:.2f}s)")


def concat_clips(clips: list[Path], output: Path) -> None:
    listing = output.with_suffix(".concat.txt")
    listing.write_text("\n".join(f"file '{clip.as_posix()}'" for clip in clips) + "\n", encoding="utf-8")
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
        "-c", "copy", "-movflags", "+faststart", str(output)
    ], check=True)
    listing.unlink(missing_ok=True)
    print(f"Assembled {output} ({duration(output):.2f}s)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", type=Path, default=ROOT / "docs/demo/dashboard-jan15.png")
    parser.add_argument("--audio", type=Path, default=Path("/home/ubuntu/winddesk-deliverables/audio"))
    parser.add_argument("--output", type=Path, default=Path("/home/ubuntu/winddesk-deliverables"))
    parser.add_argument("--frames-only", action="store_true")
    args = parser.parse_args()
    frames = args.output / "scenes"
    build_scenes(args.screenshot, frames)
    if args.frames_only:
        return
    clips: list[Path] = []
    for idx in range(1, 11):
        clip = args.output / f"scene-{idx:02d}.mp4"
        encode_scene(frames / f"scene-{idx:02d}.png", args.audio / f"scene-{idx:02d}.wav", clip)
        clips.append(clip)
    first = args.output / "part-1-client-pilot.mp4"
    second = args.output / "part-2-technical-walkthrough.mp4"
    combined = args.output / "winddesk-demo.mp4"
    concat_clips(clips[:5], first)
    concat_clips(clips[5:], second)
    concat_clips([first, second], combined)
    print("Final durations:", f"part 1 {duration(first):.2f}s, part 2 {duration(second):.2f}s, total {duration(combined):.2f}s")


if __name__ == "__main__":
    main()
