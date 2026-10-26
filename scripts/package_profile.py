"""Package a standalone, ready-to-copy profile repository without the web app."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
paths = [ROOT / "README.md", ROOT / ".gitignore", ROOT / "profile" / "config.json", ROOT / "profile" / "source-photo.png", ROOT / "profile" / "portrait-cutout.png",
         ROOT / "docs" / "PROFILE_SETUP.md", ROOT / "docs" / "PROFILE_BUILD_NOTES.md", ROOT / ".github" / "workflows" / "update-profile.yml"]
paths += list((ROOT / "public" / "profile").glob("*"))
paths += [ROOT / "profile" / "source-photo-soft-background.png", ROOT / "profile" / "background-blur-prompt.txt"]
paths += list((ROOT / "profile" / "icons").glob("*"))
paths += [ROOT / "scripts" / name for name in ["generate_profile.py", "update_contributions.py", "package_profile.py",
          "update_insights.py", "fetch_tech_icons.py", "test_insights.py", "test_portrait.py",
          "test_contributions.py", "requirements-profile.txt", "requirements-contributions.txt"]]
target = ROOT / "artifacts" / "Navn2025-profile.zip"
target.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(target, "w", ZIP_DEFLATED) as archive:
    for path in sorted(paths):
        archive.write(path, path.relative_to(ROOT).as_posix())
print(f"Packaged {len(paths)} files: {target}")
