# download_links.py
import re
from typing import List

# Updated Regex Pattern:
# DOWNLOAD_PATTERN = r"(\d{2}\.\d{2}\.\d{4} (?:F-(?:Video|Static))_N-[\w\+\-()]+(?:_[\w\+\-()]*)*_Co-\d{2,3}.*?(?:_Cm-[A-Z]{2,3})?_De-[A-Z]{2,3}(?:-\d{1,2})?)"
DOWNLOAD_PATTERN = r"(\d{2}\.\d{2}\.\d{4} (?:F-(?:Video|Static))_N-[\w\+\-()]+(?:_[\w\+\-()]*)*_Co-\d{2,3}.*?(?:_Cm-[A-Z]{2,3})?_De-[A-Z]{2,3})(?:-\d{1,2})?"

def extract_download_links(description: str) -> List[str]:
    """
    Parse the task description text and extract download folder names matching the pattern.
    
    Args:
        description (str): The task's description text.
        
    Returns:
        List[str]: A list of matched download link strings.
    """
    # return re.findall(DOWNLOAD_PATTERN, description)
    pattern = r'''
    (\d{2}\.\d{2}\.\d{4})  # Date (DD.MM.YYYY)
    [- ]                    # Hyphen/space separator
    (F-(?:Video|Static)     # F-Video/F-Static
    (?:_[-\w\+]+)+          # Allow hyphens, plus signs, and word chars
    _De-[A-Z]{2,3}          # Final _De- component
    )                       # End main pattern
    (?:-\d{1,2})?           # Optional numeric suffix
    '''
    
    matches = re.findall(pattern, description, re.VERBOSE)
    return [f"{date} {rest}" for date, rest in matches]