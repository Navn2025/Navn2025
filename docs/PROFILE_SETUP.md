# Standalone profile setup

This repository powers the README on **https://github.com/Navn2025**.
It contains profile assets and Python generators. It does not require Node.js,
React, Vite, a web server, or the original ASCII Portrait editor.

## Publish

The repository has an `origin` remote pointing to
`https://github.com/Navn2025/Navn2025.git`. From this repository:

```powershell
git push -u origin main
```

The destination repository must be public. GitHub shows the root README of a
repository whose name matches your username. Check the **Actions** tab after
pushing; the initial upload triggers **Refresh profile contributions**.

## Daily refresh

`.github/workflows/update-profile.yml` updates the contribution calendar, stats,
streaks, language donut and activity chart daily at 00:47 UTC / 06:17 IST. GitHub
may delay scheduled runs. The workflow can also be started manually in Actions.
It uses the automatic `GITHUB_TOKEN` with `contents: write`, so no personal access
token or manually configured secret is required. If repository or organization
policy blocks write access, enable workflow write permissions in repository
Settings → Actions → General.

The workflow preserves the last good committed assets if fetching or parsing
fails. GitHub can disable schedules after 60 days of repository inactivity;
re-enable the workflow in Actions if needed. GitHub's image cache may delay new art.

## Edit your profile

- Edit `README.md` for the bio and Markdown layout.
- Edit `profile/config.json` for roles, banner, terminal details and chart settings.
- Portrait input is `profile/source-photo-soft-background.png`, selected by
  `photo_source`. The untouched original is `profile/source-photo.png`.
- `profile/portrait-cutout.png` supplies only an alpha silhouette for styling
  wall cells as faint dots. The person pixels come from the selected source photo.
- The portrait has 12% padding. `portrait_padding` controls it.
- Role badges and animations are generated from the same `roles` array.
- SVG logos and their licenses are vendored in `profile/icons`.

After changing generated artwork, increment `asset_version` in the config and
update the corresponding image query strings in README.md to refresh caches.

## Generate locally

With Python 3.12 or newer:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r scripts\requirements-profile.txt
.venv\Scripts\python.exe scripts\generate_profile.py
.venv\Scripts\python.exe scripts\update_contributions.py
.venv\Scripts\python.exe scripts\update_insights.py
.venv\Scripts\python.exe -m unittest discover -s scripts -p 'test_*.py'
```

Commit and push the changes to update the profile. On macOS/Linux use
`.venv/bin/python` instead of `.venv\Scripts\python.exe`.

To create a delivery ZIP:

```powershell
.venv\Scripts\python.exe scripts\package_profile.py
```

Generated files are in `public/profile`. Brand source URLs and licenses are in
`profile/icons`; portrait and editing provenance is in `docs/PROFILE_BUILD_NOTES.md`.
