# import os
# from pathlib import Path

# def print_tree(directory, prefix="", show_files=True, file_extensions=[".py"], exclude_dirs=["logs", "__pycache__", "venv", "benchmark_policy_2", "logs_copy", ".pytest_cache", ".test_logs", "test_logs", "pytest_cache", "evaluation_logs"]):
#     """Print directory tree structure excluding specified directories"""
#     directory = Path(directory)
    
#     # Get all items in directory, excluding specified directories
#     items = []
#     for item in directory.iterdir():
#         if item.is_dir() and item.name in exclude_dirs:
#             continue  # Skip excluded directories
#         items.append(item)
    
#     items = sorted(items, key=lambda x: (x.is_file(), x.name.lower()))
    
#     for i, item in enumerate(items):
#         is_last = i == len(items) - 1
#         current_prefix = "└── " if is_last else "├── "
        
#         if item.is_dir():
#             print(f"{prefix}{current_prefix}{item.name}/")
#             extension = "    " if is_last else "│   "
#             print_tree(item, prefix + extension, show_files, file_extensions, exclude_dirs)
#         elif show_files and item.suffix in file_extensions:
#             print(f"{prefix}{current_prefix}{item.name}")

# if __name__ == "__main__":
#     print("Directory tree (excluding logs folder):")
#     print_tree(".", file_extensions=[".py"], exclude_dirs=["logs", "__pycache__", "venv", "benchmark_policy_2", "logs_copy", ".pytest_cache", ".test_logs", "test_logs", "pytest_cache", "evaluation_logs", "runs"])

import os
from pathlib import Path

def print_tree(directory, prefix="", show_files=True, file_extensions=[".py"], exclude_dirs=["logs", "__pycache__", "venv", "benchmark_policy_2", "logs_copy", ".pytest_cache", ".test_logs", "test_logs", "pytest_cache", "evaluation_logs"]):
    """Print directory tree structure excluding specified directories"""
    directory = Path(directory)
    
    # Get all items in directory, excluding specified directories
    items = []
    for item in directory.iterdir():
        if item.is_dir() and item.name in exclude_dirs:
            continue  # Skip excluded directories
        items.append(item)
    
    items = sorted(items, key=lambda x: (x.is_file(), x.name.lower()))
    
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        
        if item.is_dir():
            print(f"{prefix}{current_prefix}{item.name}/")
            extension = "    " if is_last else "│   "
            print_tree(item, prefix + extension, show_files, file_extensions, exclude_dirs)
        elif show_files and item.suffix in file_extensions:
            print(f"{prefix}{current_prefix}{item.name}")

if __name__ == "__main__":
    target_dir = "run_20250802T161542_33a790"
    print(f"Directory tree for {target_dir}:")
    print_tree(target_dir, file_extensions=[".py", ".txt", ".json", ".log", ".yaml", ".yml"], exclude_dirs=[])