# Publish your GitHub profile

This is a standalone profile repository, separate from the ASCII Portrait web app.
It includes your latest README, animated artwork, SVG social badges, source images,
and the workflow that refreshes GitHub stats and contributions daily.

The remote is already set to `https://github.com/Navn2025/Navn2025.git`.
The profile repository must be public and named **Navn2025**.

From PowerShell:

```powershell
cd C:\Users\navne\Desktop\ascii\Navn2025
git push -u origin main
```

Sign in to GitHub if Git prompts you. Alternatively, open this folder in GitHub
Desktop, choose the existing local repository, and push the `main` branch.

After pushing, open your repository's **Actions** tab and check **Refresh profile
contributions**. It also has a **Run workflow** button. Daily updates are scheduled
for 06:17 IST. The workflow uses GitHub's built-in token; no custom secret is needed.

Do not upload only README.md: its images and daily refresh depend on the included
`public/profile`, `profile`, `scripts`, and `.github/workflows` directories.

See `docs/PROFILE_SETUP.md` for editing and regeneration instructions.
