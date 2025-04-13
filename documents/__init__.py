import os

__base_path__ = os.path.dirname(__file__)
documents_folder = __base_path__  # documents_folder 就是 __base_path__

# Using __base_path__ directly to collect markdown files
__docs__ = [
    os.path.relpath(os.path.join(root, file), start=__base_path__)
    for root, _, files in os.walk(documents_folder)
    for file in files if file.lower().endswith(".md")
]

# Load file contents (README from one level up and other markdown files in documents_folder)
__all_docs__ = {}

# README CONTENTS from upper directory
readme_path = os.path.join(__base_path__, "../README.md")
with open(readme_path, "r", encoding="utf-8") as f:
    __all_docs__[readme_path] = f.read()

# Load markdown file contents from __docs__
for rel_path in __docs__:
    abs_path = os.path.join(__base_path__, rel_path)
    # Optionally, avoid loading README again if it's included in __docs__
    if os.path.normpath(abs_path) == os.path.normpath(readme_path):
        continue
    with open(abs_path, "r", encoding="utf-8") as f:
        __all_docs__[abs_path] = f.read()

def load_master_doc():
    all_text = ""
    for path, content in __all_docs__.items():
        # Generate relative path for the link
        short_path = os.path.relpath(path, start=__base_path__)
        all_text += f"# [DOC] {short_path}\n\n{content}\n\n"
    return all_text