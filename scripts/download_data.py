"""Download the 2024 HMDA national loan-level CSV (FFIEC) into data/raw/ and write a manifest."""
import hashlib, json, os, zipfile
from datetime import date
from pathlib import Path
import requests

PAGE_URL = "https://ffiec.cfpb.gov/data-publication/one-year-national-loan-level-dataset/2024"
ZIP_URL = os.environ.get("HMDA_ZIP_URL",
                         "https://files.ffiec.cfpb.gov/static-data/one-year/2024/2024_public_lar_one_year_csv.zip")

def get_project_root() -> Path:
    if "HMDA_ROOT" in os.environ:
        return Path(os.environ["HMDA_ROOT"]).resolve()
    try:
        f = Path(__file__).resolve()
        if f.is_file() and f.name == "download_data.py":
            return f.parents[1]
    except Exception:
        pass
    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "scripts" / "download_data.py").exists() or (candidate / ".gitignore").exists():
            return candidate
    return cwd

ROOT = get_project_root()
RAW_DIR = ROOT / "data" / "raw"

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    target_csv = RAW_DIR / "2024_public_lar_one_year_csv.csv"
    zpath = RAW_DIR / Path(ZIP_URL).name

    # 1. Check if the CSV is already in data/raw/
    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        # Check if CSV is in project root from a previous manual download
        root_csv = ROOT / "2024_public_lar_one_year_csv.csv"
        if root_csv.exists():
            print(f"Found existing CSV in project root: {root_csv.name}")
            print(f"Moving to {target_csv} to avoid redundant download...")
            import shutil
            shutil.move(str(root_csv), str(target_csv))
        else:
            # Download the zip if not already present
            if not zpath.exists():
                print(f"Downloading {ZIP_URL}...")
                with requests.get(ZIP_URL, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(zpath, "wb") as f:
                        for chunk in r.iter_content(1 << 20):
                            f.write(chunk)
                print(f"Downloaded zip: {zpath.name} ({zpath.stat().st_size:,} bytes)")

            print(f"Extracting {zpath.name} into {RAW_DIR}...")
            with zipfile.ZipFile(zpath) as z:
                z.extractall(RAW_DIR)

            # Clean up zip after extraction if requested (saves ~1-4 GB)
            keep_zip = os.environ.get("HMDA_KEEP_ZIP", "0") == "1"
            if not keep_zip and zpath.exists():
                print(f"Removing {zpath.name} to free disk space...")
                zpath.unlink(missing_ok=True)

        csv_files = sorted(RAW_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV file found in {RAW_DIR}")

    csv = csv_files[0]
    print(f"Found raw CSV: {csv.name} ({csv.stat().st_size:,} bytes)")
    print("Computing SHA-256 (this may take a few seconds)...")
    manifest = {
        "source_page": PAGE_URL,
        "source_url": ZIP_URL,
        "downloaded": str(date.today()),
        "file": csv.name,
        "size_bytes": csv.stat().st_size,
        "sha256": sha256_of(csv)
    }

    manifest_path = ROOT / "data" / "DOWNLOAD_MANIFEST.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest written to: {manifest_path}")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()