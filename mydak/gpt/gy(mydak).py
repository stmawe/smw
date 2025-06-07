import os
from pathlib import Path

source_dir = Path(".")
target_dir = Path("./gpt")  # relative to current directory

# Ensure the target directory exists
target_dir.mkdir(parents=True, exist_ok=True)

for file in source_dir.glob("*.py"):
    if not file.name.startswith("_"):
        # Create the new filename with (app) inserted before .py
        new_name = file.stem + "(mydak).py"
        target_file = target_dir / new_name

        # Read the source and write to the new target file
        with file.open("r", encoding="utf-8") as f_src, target_file.open("w", encoding="utf-8") as f_dst:
            f_dst.write(f_src.read())

print(f"Copied all matching .py files to {target_dir}")
