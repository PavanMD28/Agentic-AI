from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

def create_f1_standings_sheet(standings):
    try:
        # Load credentials from service account file
        credentials = service_account.Credentials.from_service_account_file(
            'service_account.json',
            scopes=SCOPES
        )
        
        # Create sheets service
        service = build('sheets', 'v4', credentials=credentials)
        
        # Create new spreadsheet
        spreadsheet = {
            'properties': {
                'title': 'F1 Standings'
            }
        }
        spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
        sheet_id = spreadsheet.get('spreadsheetId')
        
        # Prepare data
        values = [['Position', 'Driver', 'Points']]
        for standing in standings:
            values.append([
                standing['position'],
                standing['driver'],
                standing['points']
            ])
        
        body = {
            'values': values
        }
        
        # Update values
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Make the spreadsheet publicly readable
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        drive_service = build('drive', 'v3', credentials=credentials)
        drive_service.permissions().create(
            fileId=sheet_id,
            body=permission
        ).execute()
        
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    
    except Exception as e:
        print(f"Error creating Google Sheet: {e}")
        return None