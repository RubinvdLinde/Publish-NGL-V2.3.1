NGL - SteamGridDB cover-only update (232-243)
=============================================

1. GitHub Desktop -> Repository -> Show in Explorer.
2. Extract this ZIP and copy the 3 updater files to the NGL folder
   (next to index.html, data/ and covers/). This README is optional.
3. Double-click replace_ngl_covers (Windows Batch File).
4. If prompted, install Pillow (for image previews and conversion).
5. Paste your SteamGridDB API key in the command window and press Enter.
   The key is invisible while typing/pasting, is never written to disk,
   and is never sent to image servers. Do not put your key in GitHub.
   Retrieve/generate it at https://www.steamgriddb.com/profile/preferences/api
   if needed. A blank key allows manual cover selection.
6. Review the current cover and up to 3 alternative portrait covers per game.
   Recommended first alternatives are selected by default. Use Next/Previous
   and choose the cover you like; keep the current cover if none is suitable.
   If necessary, choose an existing saved portrait image (JPG, PNG, WebP).
   Click Apply selected and confirm only when satisfied with all choices.
7. In GitHub Desktop select data/games.json and the changed cover files only.
   Summary: Standardise 12 new game covers
   Commit to main -> Push origin. Reopen NGL after GitHub Pages updates.

Artwork: SteamGridDB static vertical grids, preferably 600x900, is the primary
source. Official Steam vertical artwork is a labelled fallback for a few
verified Steam titles, if SteamGridDB cannot supply artwork. No random title
matches, no AI-generated artwork, no automatic replacement without approval.
Not all games are guaranteed to have suitable SteamGridDB art.

The updater uses the exact 12 uploaded filenames, outputs 600x900 images in
the same image formats, and changes only coverVersion in the existing game
records. It does not add games or touch tier-order.json. Existing titles,
statuses, scores, notes and times remain unchanged. A backup is stored outside
of the public repository, under LocalAppData\NGL\steamgrid-cover-update-2026-11.
The API key is never written to disk. The script files need not be committed.

If your filenames differ, or if any error appears, do not commit yet. Send the
error to ChatGPT. No replacements are written until Apply selected is confirmed.
