"""NGL cover-only update, game IDs 232-243. Requires Python 3 and Pillow."""
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import webbrowser
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, urlopen
from urllib.error import HTTPError

from PIL import Image, ImageOps, ImageTk

ROOT = Path(__file__).resolve().parent
CACHE = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'NGL' / 'steamgrid-cover-update-2026-11'
API = 'https://www.steamgriddb.com/api/v2'
KEY_PAGE = 'https://www.steamgriddb.com/profile/preferences/api'
# ID, title aliases for lookup, release year when important, verified SGDB ID (if known), verified Steam app ID (if known).
TARGETS = [
    (232, 'Hollow Knight: Silksong', ['Hollow Knight: Silksong'], None, 1043, None),
    (233, 'The Legend of Zelda: Ocarina of Time', ['The Legend of Zelda: Ocarina of Time'], 2026, 5532594, None),
    (234, 'Star Fox', ['Star Fox'], 2026, None, None),
    (235, 'inKONBINI: One Store. Many Stories', ['inKonbini', 'inKONBINI: One Store. Many Stories'], None, 5448124, 2723430),
    (236, 'OU', ['OU'], 2023, None, None),
    (237, 'Selfloss', ['Selfloss'], None, None, 1086620),
    (238, 'Bahamut and the Waqwaq Tree', ['Bahamut and the Waqwaq Tree'], None, None, 2525300),
    (239, "Moomintroll: Winter's Warmth", ["Moomintroll: Winter's Warmth", 'Moomintroll'], None, None, 3256150),
    (240, 'Cloudpunk', ['Cloudpunk'], None, 23218, None),
    (241, 'The Wild at Heart', ['The Wild at Heart'], None, 5102884, 1093290),
    (242, 'Orbitals', ['Orbitals'], 2026, None, None),
    (243, 'Nocturnal', ['Nocturnal', 'Nocturnal: Enhanced Edition'], 2023, None, 1634080),
]
# Exact cover paths were checked against the user's uploaded twelve-cover ZIP.
EXPECTED = json.loads((ROOT / 'ngl_cover_targets.json').read_text(encoding='utf-8'))

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def norm(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower())


def year_of(entry):
    try:
        v = entry.get('release_date')
        if isinstance(v, str) and not v.isdigit():
            return int(v[:4])
        v = int(v)
        if v <= 0:
            return None
        return datetime.fromtimestamp(v, tz=timezone.utc).year
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def api_get(path, key, params=None):
    if not key:
        raise RuntimeError('No API key entered; manual mode.')
    url = API + path + ('?' + urlencode(params) if params else '')
    req = Request(url, headers={'Authorization': 'Bearer ' + key, 'User-Agent': 'NGL-Cover-Update/1.0', 'Accept': 'application/json'})
    # Never forward the API token to an image server or redirected host.
    with build_opener(NoRedirect()).open(req, timeout=25) as response:
        payload = json.loads(response.read(12 * 1024 * 1024))
    if not payload.get('success'):
        raise RuntimeError('SteamGridDB API returned an error.')
    return payload.get('data')


def image_load(data):
    with Image.open(io.BytesIO(data)) as im:
        if getattr(im, 'is_animated', False):
            raise ValueError('Animated image is not suitable.')
        im.load()
        im = ImageOps.exif_transpose(im)
        if im.width < 200 or im.height < 300:
            raise ValueError('Image is too small.')
        # Only portrait art close to the existing library ratio. No square product photos.
        if not 0.55 <= im.width / im.height <= 0.77:
            raise ValueError('Select vertical cover artwork (approximately 2:3), not a box/product photo.')
        if im.mode == 'RGBA' or 'transparency' in im.info:
            bg = Image.new('RGBA', im.size, '#121821')
            bg.alpha_composite(im.convert('RGBA'))
            im = bg.convert('RGB')
        else:
            im = im.convert('RGB')
        return ImageOps.fit(im, (600, 900), method=Image.Resampling.LANCZOS)


def get_image(url):
    if urlsplit(url).scheme != 'https':
        raise ValueError('Only HTTPS images are accepted.')
    f = CACHE / ('asset-' + hashlib.sha256(url.encode()).hexdigest()[:24] + '.img')
    if f.exists():
        try:
            data = f.read_bytes()
            return image_load(data)
        except Exception:
            f.unlink(missing_ok=True)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'image/*'})
    with urlopen(req, timeout=20) as response:
        data = response.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024:
        raise ValueError('Image too large.')
    im = image_load(data)
    f.write_bytes(data)
    return im


def resolve_game(target, key):
    gid, title, aliases, required_year, fixed_id, appid = target
    if fixed_id:
        return fixed_id
    # Verified Steam IDs avoid ambiguous title searches for PC releases.
    if appid:
        try:
            match = api_get('/games/steam/' + str(appid), key)
            if isinstance(match, dict) and match.get('id'):
                return int(match['id'])
        except HTTPError as exc:
            if exc.code in (401, 403, 429):
                raise
        except Exception:
            pass
    all_matches = {}
    for query in aliases:
        for result in api_get('/search/autocomplete/' + quote(query, safe=''), key) or []:
            if result.get('id') and norm(result.get('name', '')) in {norm(x) for x in aliases}:
                all_matches[result['id']] = result
    matches = list(all_matches.values())
    if required_year is not None:
        # In particular never silently choose an older Star Fox or a different Nocturnal.
        matches = [m for m in matches if year_of(m) == required_year]
    if len(matches) != 1:
        print('      No unique exact match. Leaving this title for manual review.')
        for m in matches:
            print('      Candidate:', m.get('name'), year_of(m), 'https://www.steamgriddb.com/game/' + str(m['id']))
        return None
    return int(matches[0]['id'])


def get_candidates(target, key):
    gid, title, aliases, required_year, fixed_id, appid = target
    game_id = None
    candidates = []
    problem = ''
    if key:
        try:
            game_id = resolve_game(target, key)
            if game_id:
                grids = api_get('/grids/game/' + str(game_id), key, {'dimensions': '600x900', 'types': 'static', 'nsfw': 'false', 'humor': 'false'}) or []
                if not grids:
                    grids = api_get('/grids/game/' + str(game_id), key, {'dimensions': '660x930,342x482', 'types': 'static', 'nsfw': 'false', 'humor': 'false'}) or []
                # Prefer titled artwork, exact 600x900 and community rating.
                grids = [g for g in grids if g.get('url') and not g.get('nsfw') and not g.get('humor') and not g.get('epilepsy') and g.get('style') != 'blurred' and 0.55 <= (g.get('width') or 0) / max(g.get('height') or 1, 1) <= 0.77]
                grids.sort(key=lambda g: (g.get('style') != 'no_logo', (g.get('width'), g.get('height')) == (600, 900), g.get('score') or 0), reverse=True)
                for grid in grids[:12]:
                    try:
                        im = get_image(grid['url'])
                        author = (grid.get('author') or {}).get('name', '') if isinstance(grid.get('author'), dict) else str(grid.get('author') or '')
                        candidates.append({'image': im, 'label': 'SteamGridDB' + (' / ' + author if author else ''), 'source': grid['url']})
                        if len(candidates) >= 3:
                            break
                    except Exception as exc:
                        print('      Artwork unavailable:', str(exc))
            if not candidates:
                problem = 'No suitable SteamGridDB image found.'
        except HTTPError as exc:
            problem = 'SteamGridDB HTTP ' + str(exc.code)
            if exc.code in (401, 403, 429):
                print('      ' + problem)
                raise
        except Exception as exc:
            problem = str(exc)
    else:
        problem = 'Manual mode: no API key.'
    # Only when SGDB did not provide art, try official Steam library artwork for confirmed app IDs.
    # This alternative is explicitly labelled and requires visual approval too.
    if not candidates and appid:
        for host in ('https://cdn.cloudflare.steamstatic.com/steam/apps/', 'https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/'):
            url = host + str(appid) + '/library_600x900.jpg'
            try:
                candidates.append({'image': get_image(url), 'label': 'Official Steam art (fallback)', 'source': url})
                break
            except Exception:
                continue
    return candidates, game_id or fixed_id, problem


def load_library(root):
    data = root / 'data' / 'games.json'
    original = data.read_bytes()
    games = json.loads(original.decode('utf-8-sig'))
    if not isinstance(games, list):
        raise ValueError('Unexpected games.json format; no files changed.')
    by_id = {str(g.get('id')): g for g in games}
    if len(by_id) != len(games):
        raise ValueError('Duplicate game IDs; no files changed.')
    items = []
    for target in TARGETS:
        gid = target[0]
        game = by_id.get(str(gid))
        if not game:
            raise ValueError('Missing game #' + str(gid) + '. Run the 12-game addition first.')
        name = game.get('cover')
        expected = EXPECTED[str(gid)]
        if name != expected or Path(name).name != name:
            raise ValueError('Cover path for #' + str(gid) + ' differs from your uploaded ZIP. No files changed. Contact ChatGPT with the error.')
        path = root / 'covers' / name
        if not path.is_file():
            raise ValueError('Missing cover: ' + name)
        items.append({'target': target, 'game': game, 'path': path, 'old_hash': hashlib.sha256(path.read_bytes()).hexdigest(), 'candidates': [], 'choice': None, 'page': None, 'problem': ''})
    return data, original, games, items


def output_bytes(im, suffix):
    buf = io.BytesIO()
    suffix = suffix.lower()
    if suffix == '.png':
        im.save(buf, format='PNG', optimize=True)
    elif suffix in ('.jpg', '.jpeg'):
        im.save(buf, format='JPEG', quality=94, optimize=True)
    elif suffix == '.webp':
        im.save(buf, format='WEBP', quality=94, method=4)
    else:
        raise ValueError('Unsupported existing cover extension: ' + suffix)
    return buf.getvalue()


def commit_changes(data, original, games, items):
    selected = [item for item in items if item.get('choice') is not None]
    if not selected:
        return None, []
    if data.read_bytes() != original:
        raise ValueError('games.json changed during review. Please restart the updater; nothing was overwritten.')
    for item in selected:
        if hashlib.sha256(item['path'].read_bytes()).hexdigest() != item['old_hash']:
            raise ValueError('A cover changed during review. Please restart the updater; nothing was overwritten.')
    # Prepare and validate all image bytes before modifying any live files.
    encoded = [(item, output_bytes(item['choice']['image'], item['path'].suffix)) for item in selected]
    backup = Path(tempfile.mkdtemp(prefix='cover-backup-', dir=CACHE))
    (backup / 'covers').mkdir()
    (backup / 'games.json').write_bytes(original)
    for item, _ in encoded:
        shutil.copy2(item['path'], backup / 'covers' / item['path'].name)
    changed = []
    def atomic_write(path, content):
        fd, tmp = tempfile.mkstemp(prefix='.ngl-cover-', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(content)
            os.replace(tmp, path)
        finally:
            Path(tmp).unlink(missing_ok=True)
    try:
        for item, content in encoded:
            atomic_write(item['path'], content)
            item['game']['coverVersion'] = hashlib.sha1(content).hexdigest()[:10]
            changed.append(item['game']['title'])
        atomic_write(data, json.dumps(games, ensure_ascii=False, indent=2).encode('utf-8'))
        report = [{'id': item['game']['id'], 'title': item['game']['title'], 'file': item['path'].name, 'source': item['choice']['source']} for item, _ in encoded]
        (backup / 'replacement-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        for item, _ in encoded:
            shutil.copy2(backup / 'covers' / item['path'].name, item['path'])
        shutil.copy2(backup / 'games.json', data)
        raise
    return backup, changed


def review(items):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    win = tk.Tk()
    win.title('NGL - Review new covers')
    win.geometry('920x690')
    win.minsize(800, 590)
    win.configure(bg='#131821')
    style = ttk.Style(win)
    style.theme_use('clam')
    style.configure('TButton', font=('Segoe UI', 10), padding=7)
    state = {'i': 0, 'approved': False, 'photos': []}
    for item in items:
        item['choice'] = item['candidates'][0] if item['candidates'] else None
    headline = tk.Label(win, bg='#131821', fg='white', font=('Segoe UI', 19, 'bold'), wraplength=850)
    headline.pack(pady=(16, 4))
    sub = tk.Label(win, bg='#131821', fg='#c4cbd8', font=('Segoe UI', 10), wraplength=860)
    sub.pack(pady=(0, 10))
    panel = tk.Frame(win, bg='#131821')
    panel.pack(fill='both', expand=True, padx=12, pady=5)
    selection = tk.Label(win, bg='#131821', fg='#a7e0b0', font=('Segoe UI', 11, 'bold'), wraplength=840)
    selection.pack(pady=6)
    nav = tk.Frame(win, bg='#131821')
    nav.pack(fill='x', padx=18, pady=8)
    footer = tk.Frame(win, bg='#131821')
    footer.pack(fill='x', padx=18, pady=(0, 15))
    def current():
        return items[state['i']]
    def pick(candidate):
        current()['choice'] = candidate
        render()
    def manual():
        filename = filedialog.askopenfilename(parent=win, title='Select vertical artwork', filetypes=[('Images', '*.png *.jpg *.jpeg *.webp'), ('All files', '*.*')])
        if not filename:
            return
        try:
            im = image_load(Path(filename).read_bytes())
            item = current()
            candidate = {'image': im, 'label': 'Manual selection', 'source': 'Local image: ' + Path(filename).name}
            item['candidates'] = item['candidates'][:2] + [candidate]
            pick(candidate)
        except Exception as exc:
            messagebox.showerror('Cannot use image', str(exc), parent=win)
    def open_page():
        item = current()
        webbrowser.open(item['page'] or 'https://www.steamgriddb.com/')
    def move(delta):
        state['i'] = max(0, min(len(items) - 1, state['i'] + delta))
        render()
    def apply():
        count = sum(item['choice'] is not None for item in items)
        if not count:
            messagebox.showinfo('Nothing selected', 'All existing covers will be kept.', parent=win)
            return
        if messagebox.askyesno('Apply selected covers', f'Replace {count} of {len(items)} covers? All other game data will be preserved.', parent=win):
            state['approved'] = True
            win.destroy()
    def render():
        item = current()
        for widget in panel.winfo_children():
            widget.destroy()
        state['photos'].clear()
        headline.config(text=f"{state['i']+1}/{len(items)}  |  {item['game']['title']}")
        sub.config(text='Choose artwork without console borders or shop backgrounds. ' + (item['problem'] if not item['candidates'] else ''))
        try:
            with Image.open(item['path']) as old:
                old = old.convert('RGB')
                old.thumbnail((174, 261))
        except Exception:
            old = Image.new('RGB', (174, 261), '#272d39')
        choices = [(None, old, 'Current cover')] + [(c, c['image'], c['label']) for c in item['candidates']]
        for k, (choice, im, label) in enumerate(choices):
            chosen = item['choice'] is choice
            frame = tk.Frame(panel, bg='#232d3b' if chosen else '#1a202a', highlightbackground='#72c786' if chosen else '#394352', highlightthickness=2 if chosen else 1)
            frame.grid(row=0, column=k, sticky='nsew', padx=4)
            panel.columnconfigure(k, weight=1)
            pic = im.copy()
            pic.thumbnail((174, 261))
            photo = ImageTk.PhotoImage(pic)
            state['photos'].append(photo)
            holder = tk.Frame(frame, width=178, height=265, bg='#0c1119')
            holder.pack(padx=6, pady=9)
            holder.pack_propagate(False)
            tk.Label(holder, image=photo, bg='#0c1119').pack(expand=True)
            tk.Label(frame, text=label, bg=frame['bg'], fg='white', wraplength=180, font=('Segoe UI', 9), height=2).pack(pady=2)
            ttk.Button(frame, text=('Keep current' if choice is None else f'Use cover {k}') + ('  [selected]' if chosen else ''), command=lambda c=choice: pick(c)).pack(pady=8, padx=4)
        chosen = item['choice']
        selection.config(text='Selected: ' + (chosen['label'] if chosen else 'Keep current cover'))
        prev.config(state='normal' if state['i'] else 'disabled')
        nxt.config(state='normal' if state['i'] < len(items)-1 else 'disabled')
        apply_btn.config(text=f"Apply selected ({sum(x['choice'] is not None for x in items)})")
    prev = ttk.Button(nav, text='< Previous', command=lambda: move(-1)); prev.pack(side='left')
    nxt = ttk.Button(nav, text='Next >', command=lambda: move(1)); nxt.pack(side='right')
    ttk.Button(nav, text='Choose saved image...', command=manual).pack(side='left', padx=12)
    ttk.Button(nav, text='Open SteamGridDB', command=open_page).pack(side='left')
    ttk.Button(footer, text='Cancel (no changes)', command=win.destroy).pack(side='left')
    apply_btn = ttk.Button(footer, text='Apply selected', command=apply); apply_btn.pack(side='right')
    render()
    win.mainloop()
    return state['approved']


def main():
    print('NGL - SteamGridDB cover replacement (12 existing games)')
    print('No games, scores, statuses or rankings will be added or deleted.\n')
    CACHE.mkdir(parents=True, exist_ok=True)
    data, original, games, items = load_library(ROOT)
    print('Confirmed all 12 original filenames in your NGL repository.')
    key = os.environ.get('STEAMGRIDDB_API_KEY', '').strip()
    if not key:
        print('\nUse the SteamGridDB API key from your original cover downloader.')
        print('If you need it, sign in at: ' + KEY_PAGE)
        print('Paste the API key below (it stays invisible), then press Enter.')
        print('Leave blank to select saved covers manually. Never put the key in GitHub.')
        key = getpass('API key: ').strip()
    print('\nFinding vertical artwork. This may take a little while...')
    for i, item in enumerate(items, 1):
        target = item['target']
        print(f"[{i}/12] {item['game']['title']}", flush=True)
        try:
            options, match, problem = get_candidates(target, key)
        except HTTPError as exc:
            # Do not keep submitting a bad key or hammer the API after rate limiting.
            print(f'      SteamGridDB returned HTTP {exc.code}. Check your API key / try again later.')
            print('      Switching to manual review for remaining titles.')
            key = ''
            options, match, problem = get_candidates(target, '')
        item['candidates'] = options
        item['page'] = 'https://www.steamgriddb.com/game/' + str(match) + '/grids' if match else None
        item['problem'] = problem
        print(f'      {len(options)} candidate(s).', flush=True)
        time.sleep(0.15)
    print('\nA review window will open. Check each game, then click Apply selected. Cancel leaves everything unchanged.')
    if not review(items):
        print('Cancelled. No library files changed.')
        return
    backup, changed = commit_changes(data, original, games, items)
    if not changed:
        print('No changes selected.')
        return
    print(f'\nSUCCESS: {len(changed)} covers replaced. Existing filenames kept.')
    for title in changed:
        print(' - ' + title)
    print('Backup outside your repository:', backup)
    print('Open GitHub Desktop. Commit data/games.json and the changed covers only, then Push origin.')
    print('Keep tier-order.json unchanged. The updated coverVersion values help NGL refresh its image cache.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('\nERROR:', str(exc))
        sys.exit(1)
