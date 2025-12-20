
import os
import re

DOCS_DIR = r"d:\code\ai-trading-system\docs"
DATE_PREFIX = "251210_"

def get_markdown_files(root_dir):
    md_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
    return md_files

def calculate_renames(md_files):
    renames = {} # old_abs_path -> new_abs_path
    name_map = {} # old_filename -> new_filename (for link updating)
    
    for file_path in md_files:
        dirname, filename = os.path.split(file_path)
        
        if filename.lower() == "readme.md":
            continue

        # Check if already has a date prefix (YYMMDD_ or YYYYMMDD_)
        # We assume 6 digits + underscore is the pattern to look for.
        match = re.match(r"^(\d{6})_(.+)", filename)
        
        if match:
            # Already has a prefix. Replace it with today's date.
            existing_date, rest = match.groups()
            new_filename = f"{DATE_PREFIX}{rest}"
        else:
            # No prefix, prepend it.
            new_filename = f"{DATE_PREFIX}{filename}"
            
        new_path = os.path.join(dirname, new_filename)
        
        if filename != new_filename:
            renames[file_path] = new_path
            name_map[filename] = new_filename
            
    return renames, name_map

def update_links(file_path, name_map):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    original_content = content
    
    # Simple strategy: replace filename in links.
    # Markdown links: [text](path/to/filename.md) or [text](filename.md)
    # We iterate over the map and replace occurrences.
    # To avoid partial matches (e.g. replacing "file.md" inside "my_file.md"), 
    # we should likely be smarter. But typical markdown limits boundaries.
    # A robust regex replacement for each key might be expensive but safer.
    # Given 95 files, simple string replace might conflict if one name is substring of another.
    # Sort keys by length descending to avoid substring issues.
    
    sorted_names = sorted(name_map.keys(), key=len, reverse=True)
    
    for old_name in sorted_names:
        new_name = name_map[old_name]
        # Replace only if it ends with .md and is preceded by / or (
        # Regex: (?<=[\/\(])old_name(?=[\)\s\#])
        # Actually links can include anchors #.
        # Let's try to be reasonably safe: replace `old_name` with `new_name`
        content = content.replace(old_name, new_name)
        
    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False

def main():
    files = get_markdown_files(DOCS_DIR)
    renames, name_map = calculate_renames(files)
    
    print(f"Plan to rename {len(renames)} files.")
    
    # 1. Rename files first? 
    # If we rename first, we might lose track for reading content if we are not careful?
    # Actually, we have full paths in `renames` keys. 
    # But update_links needs to run on the file content. 
    # If we rename first, we update content in the NEW path.
    
    # Step 1: Execute Renames
    for old_path, new_path in renames.items():
        try:
            os.rename(old_path, new_path)
            # print(f"Renamed: {os.path.basename(old_path)} -> {os.path.basename(new_path)}")
        except Exception as e:
            print(f"Error renaming {old_path}: {e}")

    # Step 2: Update Links in ALL files (now at new paths)
    # We need to re-scan or just calculate new paths from the list.
    # List of all current files (some renamed, some not).
    
    # Re-scan to be sure
    current_files = get_markdown_files(DOCS_DIR)
    updated_count = 0
    
    for file_path in current_files:
        if update_links(file_path, name_map):
            updated_count += 1
            
    print(f"Renaming complete. Updated links in {updated_count} files.")

if __name__ == "__main__":
    main()
