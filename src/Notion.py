import pandas as pd     
from notion_client import Client
from typing import List, Dict, Any
import numpy as np
import json
import os
import logging
from datetime import datetime
import traceback


WORD_COLUMN_NAME = "Word"
MEANING_COLUMN_NAME = "Meaning"
MULTIPLICITY_COLUMN_NAME = "Multiplicity"
CREATED_TIME_COLUMN_NAME = "created_time"


def setup_logger():
    """Setup logging configuration to write to both console and file"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create a timestamp for the log filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join('logs', f'notion_update_{timestamp}.log')
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # This will also print to console
        ]
    )
    return logging.getLogger(__name__)


def fetch_page(notion: Client, database_id: str, start_cursor: str = None, page_size: int = 100) -> Dict[str, Any]:
    """
    Fetch a single page of results from Notion database
    Args:
        notion: Notion client
        database_id: ID of the Notion database
        start_cursor: Cursor for pagination
        page_size: Number of results per page (max 100)
    """
    params = {
        'database_id': database_id,
        'start_cursor': start_cursor,
        'page_size': page_size
    }
    return notion.databases.query(**params)


def get_notion_database(notion_api_key: str, database_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
    """
    Get all pages from a Notion database with improved performance
    Args:
        notion_api_key: Notion API key
        database_id: ID of the Notion database
        page_size: Number of results per page (max 100)
    Returns:
        List of database pages
    """
    notion = Client(auth=notion_api_key)
    results = []
    start_cursor = None
    
    while True:
        # Fetch a page of results
        page = fetch_page(notion, database_id, start_cursor=start_cursor, page_size=page_size)
        current_results = page.get('results', [])
        results.extend(current_results)
        
        # Check if there are more pages
        if not page.get('has_more', False):
            break
            
        # Update cursor for next page
        start_cursor = page.get('next_cursor')
        if not start_cursor:
            break
            
    return results


def extract_property_value(prop):
    """
    Extract value from a Notion property based on its type
    Args:
        prop: Notion property object
    Returns:
        Extracted value from the property
    Raises:
        ValueError: If property type is not supported
    """
    if prop['type'] == 'title':
        # Handle title type (e.g., Word)
        if prop['title']:
            return prop['title'][0]['text']['content']
        return ''
    elif prop['type'] == 'rich_text':
        # Handle rich_text type (e.g., Meaning)
        if prop['rich_text']:
            content_parts = []
            for text_block in prop['rich_text']:
                if text_block['type'] == 'text':
                    content_parts.append(text_block['text']['content'])
                elif text_block['type'] == 'equation':
                    content_parts.append(text_block['equation']['expression'])
            return ' '.join(content_parts)
        return ''
    elif prop['type'] == 'number':
        # Handle number type (e.g., Multiplicity)
        if prop['number'] is not None:
            return int(prop['number']) + 1
        return 1
    else:
        raise ValueError(f"Unsupported property type '{prop['type']}'")


def create_word_dataframe(database, column_names):
    """
    Create a DataFrame from Notion database with specified column names
    Args:
        database: Notion database object
        column_names: List of column names to extract from the database
    Returns:
        pandas.DataFrame: DataFrame containing the extracted data
    Raises:
        ValueError: If database is empty, required columns are missing, or property type is not supported
    """
    # Extract data from database
    data = []
    
    for page in database:
        properties = page.get('properties', {})
        row_data = {'page_id': page['id']}  # Add page ID to row data
        
        for col_name in column_names:
            if col_name in properties:
                row_data[col_name] = extract_property_value(properties[col_name])
            else:
                row_data[col_name] = ''
        
        # Always extract created_time
        row_data[CREATED_TIME_COLUMN_NAME] = properties[CREATED_TIME_COLUMN_NAME]['date']['start']
        
        data.append(row_data)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    if df.empty:
        return pd.DataFrame(columns=['page_id'] + column_names + [CREATED_TIME_COLUMN_NAME])
        
    return df


def filter_by_recent_days(df: pd.DataFrame, days: int) -> pd.DataFrame:
    """
    Filter DataFrame to only include words created within the last k days
    
    Args:
        df: Input DataFrame containing created_time column
        days: Number of days to look back
        
    Returns:
        DataFrame containing only words created within the last k days
    """
    if CREATED_TIME_COLUMN_NAME not in df.columns:
        raise ValueError("DataFrame must contain 'created_time' column")
    
    # Convert created_time to datetime
    df[CREATED_TIME_COLUMN_NAME] = pd.to_datetime(df[CREATED_TIME_COLUMN_NAME])
    
    # Calculate the cutoff date
    cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
    
    # Filter the DataFrame
    return df[df[CREATED_TIME_COLUMN_NAME] >= cutoff_date]


def get_random_pages(df: pd.DataFrame, n_from_full: int, n_from_recent: int = 0, days: int = None) -> pd.DataFrame:
    """
    Get random pages from the DataFrame, combining samples from both the full database
    and a date-filtered subset. The probability of selection is proportional to the
    Multiplicity value of each page.
    
    Args:
        df: Input DataFrame containing Word, Meaning, and Multiplicity columns
        n_from_full: Number of random pages to select from full database
        n_from_recent: Number of random pages to select from recent subset (default: 0)
        days: Optional number of days to filter by for the subset
        
    Returns:
        DataFrame containing randomly selected pages
    """
    # Get random pages from full database
    full_indices = np.random.choice(
        len(df),
        size=min(n_from_full, len(df)),
        replace=False,
        p=df[MULTIPLICITY_COLUMN_NAME] / df[MULTIPLICITY_COLUMN_NAME].sum()
    )
    full_selection = df.iloc[full_indices]
    
    # If days is specified and n_from_recent > 0, get additional random pages from recent subset
    if days is not None and n_from_recent > 0:
        recent_df = filter_by_recent_days(df, days)
        if not recent_df.empty:
            recent_indices = np.random.choice(
                len(recent_df),
                size=min(n_from_recent, len(recent_df)),
                replace=False,
                p=recent_df[MULTIPLICITY_COLUMN_NAME] / recent_df[MULTIPLICITY_COLUMN_NAME].sum()
            )
            recent_selection = recent_df.iloc[recent_indices]
            
            # Combine both selections
            combined_df = pd.concat([full_selection, recent_selection], ignore_index=True)
            
            # Shuffle the combined DataFrame
            combined_df = combined_df.sample(frac=1, ignore_index=True)
            
            return combined_df[['page_id', WORD_COLUMN_NAME, MEANING_COLUMN_NAME, MULTIPLICITY_COLUMN_NAME]]
    
    # If no days specified, n_from_recent is 0, or recent subset is empty, return only full selection
    return full_selection[['page_id', WORD_COLUMN_NAME, MEANING_COLUMN_NAME, MULTIPLICITY_COLUMN_NAME]]


def get_prompt(df: pd.DataFrame) -> str:
    """
    Generate a prompt for the Gemini API based on the DataFrame.
    
    Args:
        df: Input DataFrame containing Word and Meaning columns
        
    Returns:
        Prompt for the Gemini API
    """
    Prompt = "한국어 사용자가 영어 단어를 학습할 수 있도록 입력 단어들에 대한 다양한 문제를 만들어줘 \
          단어는 여러 개가 입력이 되며, 각 단어 당 적어도 한 문제는 만들어 \
          문제에 문자 \";\" 는 포함시키지 마 \
          출력 형식으로 제공된 형식을 제외하고는 출력을 생성하지 마\
          각 입력 단어는 \"[단어;뜻]\" 형태로 주어져 <출력 형식>: \"Q: 문제;A:단어\" <입력 단어들>:"
    
    # Format each row as "(Word;Meaning)"
    word_entries = []
    for _, row in df.iterrows():
        word_entries.append(f"[{row[WORD_COLUMN_NAME]};{row[MEANING_COLUMN_NAME]}]")
    
    # Join all entries with spaces
    formatted_words = " ".join(word_entries)
    
    # Combine the prompt with the formatted words
    final_prompt = f"{Prompt} {formatted_words}"
    
    return final_prompt


def update_word_multiplicity(notion: Client, page_id: str, current_multiplicity: int, decrease: bool = False) -> bool:
    """
    Update the multiplicity of a word in the Notion database.
    
    Args:
        notion: Notion client
        page_id: ID of the Notion page to update
        current_multiplicity: Current multiplicity value (already incremented/decremented by 1 from extract_property_value)
        decrease: If True, decrease multiplicity by 1, otherwise increase by 1
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    # logger = setup_logger()
    
    try:
        # Update the page
        notion.pages.update(
            page_id=page_id,
            properties={
                "Multiplicity": {
                    "number": int(current_multiplicity)  # No need to add/subtract 1 as it's already done
                }
            }
        )
        
        # # Verify the update by fetching the updated page
        # updated_page = notion.pages.retrieve(page_id=page_id)
        # updated_multiplicity = updated_page['properties']['Multiplicity']['number']
        # 
        # # Compare the updated value with what we tried to set
        # if updated_multiplicity != current_multiplicity:
        #     logger.warning(f"Multiplicity update verification failed. Expected: {current_multiplicity}, Got: {updated_multiplicity}")
        #     return False
            
        # logger.info(f"Successfully updated multiplicity for page {page_id} to {current_multiplicity}")
        return True
    except Exception as e:
        # Get the full traceback
        # error_traceback = traceback.format_exc()
        # logger.error(f"Error updating multiplicity:\n{error_traceback}")
        return False
