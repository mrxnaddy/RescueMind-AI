import os

SKIP_DIRS = {"venv", ".venv", "__pycache__", ".git", "node_modules", ".idea", ".vscode", ".pytest_cache"}
SKIP_FILES = {".env", "project_dump.txt", "dump_project.py"}  # .env mein secrets hote hain, isliye skip
EXTENSIONS = {".py", ".txt", ".md", ".yml", ".yaml", ".json", ".example", ".ini", ".toml", ".sql"}

root = "."
tree_lines, file_blocks = [], []

for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
    level = dirpath.count(os.sep)
    tree_lines.append(f"{'  ' * level}{os.path.basename(dirpath) or '.'}/")
    for name in sorted(filenames):
        if name in SKIP_FILES:
            continue
        tree_lines.append(f"{'  ' * (level + 1)}{name}")
        path = os.path.join(dirpath, name)
        ext = os.path.splitext(name)[1]
        if ext in EXTENSIONS or name == ".env.example":
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                content = f"<could not read: {e}>"
            file_blocks.append(f"\n===== {path} =====\n{content}")

with open("project_dump.txt", "w", encoding="utf-8") as out:
    out.write("PROJECT TREE\n" + "\n".join(tree_lines) + "\n")
    out.write("\nFILE CONTENTS\n" + "\n".join(file_blocks))

print("Done: project_dump.txt ban gayi")