Nintendo Games Library (NGL) V2.3.1

This is the phone-ready PWA release.

Key changes from V2.1:
- Covers remain hosted/online by default instead of being stored in the PWA cache.
- Optional full offline cover download (~121 MB) remains available in Settings.
- Stable phone-side storage key so future app/database updates preserve rankings and edits.
- New games from a published games.json are automatically added to Unranked.
- Per-cover content versioning prevents old cover art from sticking after replacements.
- NGL Admin for adding games and replacing covers on the laptop.
- PWA manifest has a stable app ID and new NGL icon.
- GitHub Pages deployment guide included.

Local testing:
- start_ngl_windows.bat = app
- start_ngl_admin_windows.bat = laptop library manager

Read DEPLOY_AND_UPDATE.md for phone installation and future update workflow.


V2.3.1 branding update
- New official NGL artwork used for the PWA/home-screen icon.
- Branded splash screen with Nintendo Games Library / NGL and the subtitle:
  "Your personal Nintendo collection, backlog and tier ranking".
- New branded Home hero and header icon.
- Highest-score/currently-playing cards now have fixed widths and two-line clamped titles so long names cannot change spacing.


V2.3.1 local-cache fix
- Local testing now opens at http://localhost:8783/?v=2.3.1
- Service workers are disabled/unregistered during local HTTP testing.
- The PWA service worker still activates normally once hosted over HTTPS.
- CSS, JavaScript and manifest resources are versioned to prevent stale browser files.
