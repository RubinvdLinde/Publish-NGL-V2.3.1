NGL ADMIN UPDATE 2.4
====================

This is an ADMIN-ONLY patch for your existing NGL V2.3.1 folder/repository.

FILES TO REPLACE
----------------
1. admin.html
2. admin_server.py

You do NOT need to replace:
- covers/
- data/
- app.js
- index.html
- styles.css
- branding/
- icons/
- any other NGL file

HOW TO INSTALL
--------------
1. Close NGL Admin if it is currently open.
2. Open your local GitHub repository folder (the folder that contains index.html).
3. Copy admin.html and admin_server.py from this ZIP into that folder.
4. Windows will ask whether to replace the existing files. Choose Replace.
5. Start the existing start_ngl_admin_windows.bat file.
6. NGL Admin will open as before at http://localhost:8772/admin.html

NEW IN ADMIN 2.4
----------------
- Search and select any existing game.
- Edit title.
- Edit platform.
- Edit Physical / Digital / Unknown.
- Edit status:
    Not Played
    Have Played
    Finished
    Stopped
- Edit Meta score.
- Edit My score.
- Edit Main + Extra.
- Edit Completionist.
- Edit Time Played.
- Edit Notes.
- Optionally replace the cover from the same Edit form.
- Existing tier and tier ordering are preserved.

PUBLISHING A CHANGE
-------------------
After you edit an existing game, GitHub Desktop will normally show data/games.json as changed.
Commit it and click Push origin. GitHub Pages then publishes the updated master data.

IMPORTANT
---------
The normal NGL app keeps personal changes locally per device.
If a phone/browser already has a local override for the same game, that local value can still
take priority over the newly published master value. This is intentional in the current NGL design.
