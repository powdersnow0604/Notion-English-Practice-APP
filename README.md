# English Study App

An application for studying English words using Notion database and Gemini AI.

## Building the Executable

To create an executable file for the application, follow these steps:

1. Install the required dependencies (tested with python 3.9):
```bash
pip install -r requirements.txt
```

2. Create a `config.json` file in the root directory with your API keys:
```json
{
    "NOTION_API_KEY": "your_notion_api_key",
    "NOTION_DATABASE_ID": "your_database_id",
    "GEMINI_API_KEY": "your_gemini_api_key"
}
```

3. Run the setup script to create the executable:
```bash
python setup.py
```

4. The executable will be created in the `dist` directory as `EnglishStudyApp.exe`

## Running the Application

1. After building, you'll find two files in the `dist` directory:
   - `EnglishStudyApp.exe`
   - `config.json`

2. Make sure to:
   - Edit the `config.json` file with your actual API keys
   - Keep both files in the same directory
   - Never share the `config.json` file containing your API keys

## Notes

- The application requires an internet connection to access Notion and Gemini APIs
- The executable will work only if `config.json` is in the same directory
- Keep your API keys secure and never share them 