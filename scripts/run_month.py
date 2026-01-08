"""
Monthly Runner
--------------
Runs all parsers and diff engine for a given month.

Phase: 1 (DB-less)
"""

import subprocess
from pathlib import Path
import sys


# =========================
# CONFIG
# =========================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

PARSERS_DIR = SCRIPTS_DIR / "parsers"

USER_PARSER = PARSERS_DIR / "user_list_parser.py"
ASSET_PARSER = PARSERS_DIR / "asset_list_parser.py"
DIFF_ENGINE = SCRIPTS_DIR / "diff_engine.py"


# =========================
# HELPERS
# =========================

def find_file(directory: Path, keywords: list):
    for file in directory.iterdir():
        if file.is_file():
            name = file.name.lower()
            if all(k in name for k in keywords):
                return file
    return None


def run_command(cmd: list):
    """
    Always use the same Python executable that launched this script
    (critical for macOS and virtualenvs)
    """
    cmd[0] = sys.executable
    print("▶", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"❌ Command failed: {' '.join(cmd)}")


# =========================
# MAIN
# =========================

def run_month(month: str):
    raw_dir = DATA_DIR / "raw" / month
    normalized_dir = DATA_DIR / "normalized"
    diffs_dir = DATA_DIR / "diffs"

    if not raw_dir.exists():
        sys.exit(f"❌ Raw data folder not found: {raw_dir}")

    normalized_dir.mkdir(parents=True, exist_ok=True)
    diffs_dir.mkdir(parents=True, exist_ok=True)

    # Infer previous month
    year, mon = map(int, month.split("-"))
    prev_month = f"{year}-{mon-1:02d}" if mon > 1 else f"{year-1}-12"

    # =========================
    # Discover Input Files
    # =========================

    user_file = (
        find_file(raw_dir, ["user", "list"]) or
        find_file(raw_dir, ["user"])
    )

    asset_file = (
        find_file(raw_dir, ["asset", "list"]) or
        find_file(raw_dir, ["asset"])
    )

    if not user_file:
        sys.exit("❌ User list file not found")
    if not asset_file:
        sys.exit("❌ Asset list file not found")

    print(f"📄 User list : {user_file.name}")
    print(f"📄 Asset list: {asset_file.name}")

    # =========================
    # Output Paths
    # =========================

    curr_users = normalized_dir / f"{month}-users.json"
    curr_assets = normalized_dir / f"{month}-assets.json"

    prev_users = normalized_dir / f"{prev_month}-users.json"
    prev_assets = normalized_dir / f"{prev_month}-assets.json"

    diff_output = diffs_dir / f"{month}-diff.json"

    # =========================
    # Run User Parser
    # =========================

    run_command([
        sys.executable, str(USER_PARSER),
        "--input", str(user_file),
        "--month", month,
        "--previous", str(prev_users),
        "--output", str(curr_users)
    ])

    # =========================
    # Run Asset Parser
    # =========================

    run_command([
        sys.executable, str(ASSET_PARSER),
        "--input", str(asset_file),
        "--month", month,
        "--previous", str(prev_assets),
        "--output", str(curr_assets)
    ])

    # =========================
    # Run Diff Engine (if possible)
    # =========================

    if prev_users.exists() and prev_assets.exists():
        run_command([
            sys.executable, str(DIFF_ENGINE),
            "--prev-users", str(prev_users),
            "--curr-users", str(curr_users),
            "--prev-assets", str(prev_assets),
            "--curr-assets", str(curr_assets),
            "--from-month", prev_month,
            "--to-month", month,
            "--output", str(diff_output)
        ])
    else:
        print("ℹ️ Previous month not found — diff skipped")

    print("\n✅ Monthly run completed successfully")
    print(f"📂 Normalized output: {normalized_dir}")
    print(f"📂 Diff output      : {diffs_dir}")


# =========================
# CLI
# =========================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run monthly cybersecurity pipeline")
    parser.add_argument("--month", required=True, help="Month in YYYY-MM format")

    args = parser.parse_args()

    run_month(args.month)






# """
# Monthly Runner
# --------------
# Runs all parsers and diff engine for a given month.

# Phase: 1 (DB-less)
# """

# import subprocess
# from pathlib import Path
# import sys


# # =========================
# # CONFIG
# # =========================

# PROJECT_ROOT = Path(__file__).resolve().parent.parent
# DATA_DIR = PROJECT_ROOT / "data"
# SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# PARSERS_DIR = SCRIPTS_DIR / "parsers"

# USER_PARSER = PARSERS_DIR / "user_list_parser.py"
# ASSET_PARSER = PARSERS_DIR / "asset_list_parser.py"
# DIFF_ENGINE = SCRIPTS_DIR / "diff_engine.py"


# # =========================
# # HELPERS
# # =========================

# def find_file(directory: Path, keywords: list):
#     for file in directory.iterdir():
#         if file.is_file():
#             name = file.name.lower()
#             if all(k in name for k in keywords):
#                 return file
#     return None


# def run_command(cmd: list):
#     print("▶", " ".join(cmd))
#     result = subprocess.run(cmd)
#     if result.returncode != 0:
#         sys.exit(f"❌ Command failed: {' '.join(cmd)}")


# # =========================
# # MAIN
# # =========================

# def run_month(month: str):
#     raw_dir = DATA_DIR / "raw" / month
#     normalized_dir = DATA_DIR / "normalized"
#     diffs_dir = DATA_DIR / "diffs"

#     if not raw_dir.exists():
#         sys.exit(f"❌ Raw data folder not found: {raw_dir}")

#     normalized_dir.mkdir(parents=True, exist_ok=True)
#     diffs_dir.mkdir(parents=True, exist_ok=True)

#     # Infer previous month
#     year, mon = map(int, month.split("-"))
#     prev_month = f"{year}-{mon-1:02d}" if mon > 1 else f"{year-1}-12"

#     # =========================
#     # Discover Input Files
#     # =========================

#     user_file = (
#         find_file(raw_dir, ["user", "list"]) or
#         find_file(raw_dir, ["user"])
#     )

#     asset_file = (
#         find_file(raw_dir, ["asset", "list"]) or
#         find_file(raw_dir, ["asset"])
#     )

#     if not user_file:
#         sys.exit("❌ User list file not found")
#     if not asset_file:
#         sys.exit("❌ Asset list file not found")

#     print(f"📄 User list : {user_file.name}")
#     print(f"📄 Asset list: {asset_file.name}")

#     # =========================
#     # Output Paths
#     # =========================

#     curr_users = normalized_dir / f"{month}-users.json"
#     curr_assets = normalized_dir / f"{month}-assets.json"

#     prev_users = normalized_dir / f"{prev_month}-users.json"
#     prev_assets = normalized_dir / f"{prev_month}-assets.json"

#     diff_output = diffs_dir / f"{month}-diff.json"

#     # =========================
#     # Run Parsers
#     # =========================

#     run_command([
#         "python", str(USER_PARSER),
#         "--input", str(user_file),
#         "--month", month,
#         "--previous", str(prev_users),
#         "--output", str(curr_users)
#     ])

#     run_command([
#         "python", str(ASSET_PARSER),
#         "--input", str(asset_file),
#         "--month", month,
#         "--previous", str(prev_assets),
#         "--output", str(curr_assets)
#     ])

#     # =========================
#     # Run Diff Engine (if previous exists)
#     # =========================

#     if prev_users.exists() and prev_assets.exists():
#         run_command([
#             "python", str(DIFF_ENGINE),
#             "--prev-users", str(prev_users),
#             "--curr-users", str(curr_users),
#             "--prev-assets", str(prev_assets),
#             "--curr-assets", str(curr_assets),
#             "--from-month", prev_month,
#             "--to-month", month,
#             "--output", str(diff_output)
#         ])
#     else:
#         print("ℹ️ Previous month not found — diff skipped")

#     print("\n✅ Monthly run completed successfully")
#     print(f"📂 Normalized: {normalized_dir}")
#     print(f"📂 Diffs     : {diffs_dir}")


# # =========================
# # CLI
# # =========================

# if __name__ == "__main__":
#     import argparse

#     parser = argparse.ArgumentParser(description="Run monthly cybersecurity pipeline")
#     parser.add_argument("--month", required=True, help="Month in YYYY-MM format")

#     args = parser.parse_args()

#     run_month(args.month)
