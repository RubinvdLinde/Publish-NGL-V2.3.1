NGL COVER DOWNLOAD FIX (12 games)
=================================
Replace the old updater files with these files in your EXISTING local NGL repository.
Run apply_ngl_new_games.bat again. The original failed run did not change games.json or tier-order.json.
This version uses a replacement cover source for inKONBINI and OU. The other ten URLs and all game data remain unchanged.
If a source fails, choose B to open the product/source page, save the correct front-cover image to Downloads, then return to the console and press Enter to select it. S skips the unavailable cover and leaves the library untouched. Successful images are cached outside the GitHub repository for future retries. Backups are saved outside the repository too.
Only after SUCCESS, commit data/games.json, data/tier-order.json and the added covers in GitHub Desktop, then Push origin. Do not publish updater files or logs.

NGL - 12 NEW GAMES UPDATE (27 NOV 2026)
========================================

WHAT THIS DOES
--------------
Adds these 12 games to your CURRENT NGL master library without replacing existing game data:

1. Hollow Knight: Silksong - Nintendo Switch 2 Edition
2. The Legend of Zelda: Ocarina of Time
3. Star Fox
4. inKONBINI: One Store. Many Stories
5. OU
6. Selfloss
7. Bahamut and the Waqwaq Tree
8. Moomintroll: Winter's Warmth
9. Cloudpunk
10. The Wild at Heart
11. Orbitals
12. Nocturnal

All are added as:
- Physical
- Not Played
- Unranked
- User score blank
- Time Played blank

The updater also downloads the cover images and adds the games to tier-order.json under U (Unranked).

HOW TO USE
----------
1. Extract the contents of this ZIP DIRECTLY into your local GitHub NGL repository folder.
   This is the folder that already contains index.html, data\ and covers\.
2. Double-click apply_ngl_new_games.bat.
3. Wait for SUCCESS.
4. Open GitHub Desktop.
5. Summary: Add 12 new games
6. Commit to main.
7. Push origin.
8. After GitHub Pages republishes, reopen NGL on your phone.

The updater creates backups before changing games.json and tier-order.json.
It does NOT overwrite existing games and will skip a title/platform combination that already exists.

DATA USED
---------
Hollow Knight: Silksong (Switch 2): Meta 91 | Main+Extra 47h | Completionist 65.5h
Ocarina of Time (Switch 2): Meta 95 | Main+Extra 24h | Completionist 27.5h
Star Fox (Switch 2): Meta 81 | Main+Extra 7h | Completionist 28.5h
inKONBINI (Switch): Meta tbd | Main+Extra 8h | Completionist 13h
OU (Switch): Meta tbd | Main+Extra 3.5h | Completionist 4h
Selfloss (Switch): Meta tbd | Main+Extra 7.5h | Completionist 8h
Bahamut and the Waqwaq Tree (Switch): Meta tbd | Main+Extra tbd | Completionist 4.5h
Moomintroll: Winter's Warmth (Switch): Meta 78 | Main+Extra 7h | Completionist 11h
Cloudpunk (Switch): Meta 54 | Main+Extra 11.5h | Completionist 15h
The Wild at Heart (Switch): Meta 76 | Main+Extra 14h | Completionist 18.5h

For games without enough platform-specific Metacritic reviews, Meta is intentionally left blank/tbd rather than substituting a single review score.

Orbitals (Switch 2): Meta 82 | Main+Extra 6h | Completionist 6.5h
Orbitals is added as Physical / Not Played / Unranked.

Nocturnal (Switch): Meta tbd | Main+Extra 2.5h | Completionist 3h
The published 81 Metascore is for PC; a Switch-specific aggregate was not verified.
Nocturnal cover: standard Red Art Games physical cover (ESRB), since the exact purchased edition was not specified.
Sources: https://www.dekudeals.com/items/nocturnal ; https://gg.deals/franchise/nocturnal/nintendo/
Cover images are downloaded when the updater runs on your laptop. Network access and remote image availability are required.
In GitHub Desktop, commit data/games.json, data/tier-order.json and the new cover files; leave .bak files and updater/log files unselected if you do not want them published.
