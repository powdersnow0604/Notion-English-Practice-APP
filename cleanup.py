import os
import shutil

def cleanup():
    """Remove build and distribution directories created by setup.py"""
    # Directories to remove
    dirs_to_remove = [
        'build',
        'dist',
        'logs',
        '*.egg-info'
    ]
    
    # Files to remove
    files_to_remove = [
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.Python',
        '*.so',
        '*.egg',
        '*.egg-info',
        'eggs',
        'parts',
        'bin',
        'var',
        'sdist',
        'develop-eggs',
        'installed.cfg',
        'lib',
        'lib64',
        'MANIFEST',
        '*.spec'
    ]
    
    # Remove directories
    for pattern in dirs_to_remove:
        for item in os.listdir('.'):
            if item.startswith(pattern.replace('*', '')):
                path = os.path.join('.', item)
                if os.path.isdir(path):
                    print(f"Removing directory: {path}")
                    shutil.rmtree(path)
    
    # Remove files
    for pattern in files_to_remove:
        for item in os.listdir('.'):
            if item.endswith(pattern.replace('*', '')):
                path = os.path.join('.', item)
                if os.path.isfile(path):
                    print(f"Removing file: {path}")
                    os.remove(path)
    
    print("Cleanup completed!")

if __name__ == "__main__":
    cleanup() 