from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json, hashlib, re, shutil, sys, tempfile, os, webbrowser
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "games.json"
TIERS = ROOT / "data" / "tier-order.json"
COVERS = ROOT / "covers"
PAYLOAD = ROOT / "update_payload.json"
LOG = ROOT / "NGL_NEW_GAMES_UPDATE_LOG.txt"


def safe_name(s):
    s = re.sub(r'[<>:"/\\|?*]+', '', s)
    return re.sub(r'\s+', ' ', s).strip()[:160]


# A persistent per-user cache outside the public GitHub repository.
CACHE = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "NGL" / "new-games-cover-cache-2026-11"


def image_ext(data):
    # Do not trust URL extensions or Content-Type alone.
    if len(data) < 1000:
        raise ValueError("Image is too small")
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9"):
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data[4:8] == b"ftyp" and data[8:12] in (b"avif", b"avis"):
        return ".avif"
    raise ValueError("Not a supported image (JPG, PNG, WebP, AVIF)")


def download(url, dest, referer=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36",
        "Accept": "image/webp,image/png,image/jpeg,image/*;q=0.8,*/*;q=0.5"
    }
    if referer:
        headers["Referer"] = referer
    else:
        u = urlsplit(url)
        headers["Referer"] = f"{u.scheme}://{u.netloc}/"
    with urlopen(Request(url, headers=headers), timeout=25) as r:
        data = r.read(25 * 1024 * 1024 + 1)
    if len(data) > 25 * 1024 * 1024:
        raise ValueError("Image is too large")
    image_ext(data)
    dest.write_bytes(data)
    return data


def manual_cover(item):
    print(f"\nCould not download the cover for: {item['title']}")
    if item.get("cover_page"):
        print("Product/official page: " + item["cover_page"])
    if item.get("alternative_page"):
        print("Alternative page: " + item["alternative_page"])
    print("Save the correct front cover in your browser (JPG/PNG/WebP).")
    print("The other successful downloads are cached; you can safely retry later.")
    while True:
        answer = input("[B] Open cover source in browser | [Enter] Select a saved image | [S] Skip for now: ").strip().lower()
        if answer == "s":
            return None
        if answer == "b":
            webbrowser.open(item.get("cover_page") or item["cover_url"])
            continue
        if answer:
            continue
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            try:
                filename = filedialog.askopenfilename(title="Select cover for " + item["title"], filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.avif"), ("All files", "*.*")])
            finally:
                root.destroy()
        except Exception:
            filename = input("Enter the full path to the saved image (or press Enter to skip): ").strip().strip('"')
        if not filename:
            return None
        try:
            data = Path(filename).read_bytes()
            image_ext(data)
            return data
        except Exception as e:
            print("Cannot use this file:", e)


def get_cover(item):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256((item["title"] + "|" + item["platformCode"] + "|" + item["cover_url"]).encode()).hexdigest()[:24]
    cached = CACHE / (key + ".image")
    if cached.exists():
        try:
            data = cached.read_bytes()
            image_ext(data)
            print("      Using cached image")
            return cached, data
        except Exception:
            cached.unlink(missing_ok=True)
    try:
        data = download(item["cover_url"], cached, item.get("cover_page"))
    except Exception as e:
        print("      Download failed:", e)
        data = manual_cover(item)
        if data is None:
            raise RuntimeError(str(e))
        cached.write_bytes(data)
    return cached, data


def num_id(g):
    try:
        return int(g.get("id", 0))
    except Exception:
        return 0


def main():
    print("NGL - Add 12 new games (cover fix)")
    print("======================")

    missing = [str(p.relative_to(ROOT)) for p in (DATA, TIERS, COVERS) if not p.exists()]
    if missing:
        print("\nERROR: This update is not inside your NGL repository folder.")
        print("Missing:", ", ".join(missing))
        print("\nExtract this ZIP into the same folder that contains index.html, data and covers.")
        input("Press Enter to close...")
        return 1

    games = json.loads(DATA.read_text(encoding="utf-8"))
    tiers = json.loads(TIERS.read_text(encoding="utf-8"))
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))

    existing = {(str(g.get("title", "")).strip().casefold(), str(g.get("platformCode", ""))) for g in games}
    new_defs = [x for x in payload if (x["title"].strip().casefold(), x["platformCode"]) not in existing]

    if not new_defs:
        print("\nAll 12 games are already present. Nothing to change.")
        input("Press Enter to close...")
        return 0

    print(f"\n{len(new_defs)} new game(s) will be added. Existing games will not be overwritten.")
    print("Downloading cover images first...")

    tmp = Path(tempfile.mkdtemp(prefix="ngl_new_covers_"))
    downloaded = []
    failures = []
    try:
        for i, item in enumerate(new_defs, 1):
            print(f"  [{i}/{len(new_defs)}] {item['title']}")
            try:
                dest, data = get_cover(item)
                downloaded.append((item, dest, data))
            except Exception as e:
                failures.append((item, str(e)))

        if failures:
            print("\nNo library files were changed because one or more covers could not be downloaded.")
            print("Rerun the updater and select a saved cover for the following games. Successful downloads will be reused:")
            for item, err in failures:
                print(f"\n- {item['title']}\n  {item['cover_url']}\n  Error: {err}")
            input("\nPress Enter to close...")
            return 2

        # Backups before modifying anything.
        backup = Path(tempfile.mkdtemp(prefix="library-backup-", dir=CACHE))
        shutil.copy2(DATA, backup / "games.json")
        shutil.copy2(TIERS, backup / "tier-order.json")
        print("Backup saved outside the repository:", backup)

        next_id = max([num_id(g) for g in games] or [0]) + 1
        added = []
        tiers.setdefault("U", [])

        for item, src, data in downloaded:
            gid = str(next_id)
            ext = image_ext(data)
            filename = f"{next_id:03d} - {safe_name(item['title'])} [{item['platformCode']}]{ext}"
            target = COVERS / filename
            shutil.copy2(src, target)
            version = hashlib.sha1(data).hexdigest()[:10]

            game = {
                "id": gid,
                "title": item["title"],
                "platformCode": item["platformCode"],
                "platform": item["platform"],
                "metaScore": item.get("metaScore"),
                "score": None,
                "format": "Physical",
                "status": "unplayed",
                "sourceStatus": "Not Played",
                "cover": filename,
                "coverVersion": version,
                "tier": "U",
                "tierPosition": None,
                "mainExtra": item.get("mainExtra"),
                "completionist": item.get("completionist"),
                "timePlayed": None,
                "notes": ""
            }
            games.append(game)
            tiers["U"].append(gid)
            added.append(game)
            next_id += 1

        DATA.write_text(json.dumps(games, ensure_ascii=False, indent=2), encoding="utf-8")
        TIERS.write_text(json.dumps(tiers, ensure_ascii=False, indent=2), encoding="utf-8")

        lines = ["NGL new games update", "", "Added:"]
        for g in added:
            lines.append(f"#{g['id']} | {g['platformCode']} | {g['title']} | Meta {g['metaScore'] if g['metaScore'] is not None else 'tbd'} | Main+Extra {g['mainExtra'] if g['mainExtra'] is not None else 'tbd'} | Completionist {g['completionist'] if g['completionist'] is not None else 'tbd'}")
        lines += ["", "All games: Physical / Not Played / Unranked.", "Existing library entries were preserved."]
        LOG.write_text("\n".join(lines), encoding="utf-8")

        print("\nSUCCESS. Added:")
        for g in added:
            meta = g['metaScore'] if g['metaScore'] is not None else 'tbd'
            print(f"  #{g['id']} {g['title']} [{g['platformCode']}] - Meta {meta}")
        print("\nNext: open GitHub Desktop -> Summary: Add 12 new games -> Commit to main -> Push origin.")
        input("\nPress Enter to close...")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
