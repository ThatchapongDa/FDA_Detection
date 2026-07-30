import os
import re

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove version tags like [v8], [v7.19], [v6.7], [v7.1], etc.
    # regex matches: [vX.X] or [vX] or [vX.X.X]
    new_content = re.sub(r'\[v\d+(\.\d+)*\]\s*', '', content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Cleaned version tags in: {filepath}")

def main():
    root_dirs = ['backend/app', 'frontend/src']
    
    for root_dir in root_dirs:
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py') or file.endswith('.js'):
                    clean_file(os.path.join(root, file))

if __name__ == '__main__':
    main()
