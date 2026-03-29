import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""def publish_to_sheets(content: str) -> dict:
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "D:\content-ops-\backend\content-ops-project-3adabd59b581.json", scope
        )

        client = gspread.authorize(creds)

        sheet = client.open("content_posts").sheet1

        row = [content, "linkedin", "pending"]
        sheet.append_row(row)

        logger.info("Content added successfully")
        return {"status": "success"}

    except Exception as e:
        logger.error(str(e))
        return {"status": "error", "message": str(e)}

"""
def publish_to_sheets(content: str) -> dict:
    
    """Sends generated/approved content to a Google Sheet named 'content_posts'.
    Content is stored in Column A. Service account email: 
    content-bot@content-ops-project.iam.gserviceaccount.com"""
    
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    # Robust credentials file path handling
    creds_filename = r"D:\content-ops-\backend\content-ops-project-3adabd59b581.json"
    possible_paths = [
        creds_filename,
        os.path.join("backend", creds_filename),
        os.path.join(os.path.dirname(__file__), "..", "..", creds_filename)
    ]
    
    creds_file = None
    for path in possible_paths:
        if os.path.exists(path):
            creds_file = path
            break
            
    if not creds_file:
        error_msg = f"Credentials file {creds_filename} not found. Searched in: {possible_paths}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        client = gspread.authorize(creds)
        
        try:
            sheet = client.open("content_posts").sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            error_msg = "Google Sheet 'content_posts' not found. Ensure it exists AND is shared with content-bot@content-ops-project.iam.gserviceaccount.com"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        # Column A: Generated Content
        # Column B: Platform (Always 'linkedin')
        # Column C: Status (Always 'pending')
        row = [content, "linkedin", "pending"]
        sheet.append_row(row)
        
        logger.info(f"Successfully archived content to Column A and set Column B to 'linkedin': {content[:50]}...")
        return {"status": "success", "message": "Content archived successfully."}

    except Exception as e:
        error_msg = f"Google Sheets error: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

if __name__ == "__main__":
    test_content = "Automated test from ContentOps AI at " + datetime.now().isoformat()
    print(publish_to_sheets(test_content))
