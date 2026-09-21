# NGL V2.3 — phone install and future updates

## Architecture
- GitHub Pages hosts the app, game database and cover files.
- Your phone does NOT pre-download all covers. Covers load from the site when needed.
- Scores, notes, status and tier ranking are saved locally on your phone.
- Optional Settings > Download all covers makes the whole library available offline (~121 MB).
- New games are managed on the laptop with NGL Admin.

## First deployment
1. Install GitHub Desktop and sign in.
2. Create a new repository named `ngl` and choose a local folder.
3. Copy the CONTENTS of this `ngl_v2_2` folder into that repository folder so `index.html` is at the repository root.
4. In GitHub Desktop, commit all files and Publish repository.
5. On github.com open the repository > Settings > Pages.
6. Under Build and deployment choose `Deploy from a branch`.
7. Select branch `main` and folder `/(root)`, then Save.
8. Wait for GitHub Pages to show the site URL.
9. Open the URL on the Samsung phone in Chrome.
10. Use the NGL Install button when shown, or Chrome menu > Add to Home screen / Install app.

## Adding a game later
1. On the laptop, open the local repository folder.
2. Double-click `start_ngl_admin_windows.bat`.
3. Fill in Add a game and select the cover.
4. NGL Admin updates `data/games.json`, `data/tier-order.json` and adds the cover to `covers/`.
5. Open GitHub Desktop. Commit the changed files and click Push origin.
6. GitHub Pages updates automatically.
7. Refresh/reopen NGL on the phone. The new game appears in Unranked. Existing phone rankings and edits remain intact.

## Replacing a cover later
Use the Replace an existing cover section in NGL Admin, then commit/push in GitHub Desktop. A per-cover version hash makes the phone fetch the new image rather than a stale cached cover.

## Backups
Use Settings > Export backup on the phone regularly. This backup contains your phone-side scores/status edits/notes/tier ranking.


## V2.3 branding
The branding/ngl-logo.png file and icons/ files are now part of the published app. When updating via GitHub Pages, commit these files together with the rest of the V2.3 update.
