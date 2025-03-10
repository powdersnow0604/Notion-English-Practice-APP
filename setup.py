import PyInstaller.__main__
import os
import shutil

# Get the absolute path of the current directory
current_dir = os.path.abspath(os.path.dirname(__file__))

# Define the main script path
main_script = os.path.join(current_dir, 'src', 'main.py')

# Define the config file path
config_file = os.path.join(current_dir, 'config.json')

# Define the output directory
output_dir = os.path.join(current_dir, 'dist')

# Create a temporary config file if it doesn't exist
if not os.path.exists(config_file):
    with open(config_file, 'w') as f:
        f.write('''{
    "NOTION_API_KEY": "your_notion_api_key",
    "NOTION_DATABASE_ID": "your_database_id",
    "GEMINI_API_KEY": "your_gemini_api_key"
}''')

# PyInstaller arguments
PyInstaller.__main__.run([
    main_script,  # Main script
    '--name=EnglishStudyApp',  # Name of the executable
    '--onefile',  # Create a single executable file
    '--windowed',  # Don't show console window
    '--add-data', f'{config_file};.',  # Include config.json
    #'--icon=src/icon.ico',  # Add an icon (optional)
    '--clean',  # Clean PyInstaller cache
    '--noconfirm',  # Replace existing build without asking
    f'--distpath={output_dir}',  # Output directory
    '--hidden-import=notion_client',  # Include required hidden imports
    '--hidden-import=google.generativeai',
    '--hidden-import=pandas',
    '--hidden-import=numpy',
])

# Copy config.json to dist directory for easy access
shutil.copy2(config_file, os.path.join(output_dir, 'config.json')) 