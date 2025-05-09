import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets']

def get_drive_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv('GOOGLE_CREDENTIALS_FILE'), SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def create_sheet(standings):
    service = get_drive_service()
    sheet = {
        'properties': {
            'title': 'F1 Standings'
        }
    }
    sheet = service.spreadsheets().create(body=sheet).execute()
    sheet_id = sheet['spreadsheetId']
    
    # Update sheet with standings
    body = {
        'values': [[k, v] for k, v in standings.items()]
    }
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range='A1:B',
        valueInputOption='RAW',
        body=body
    ).execute()
    
    return sheet_id

def share_sheet(sheet_id, email):
    service = get_drive_service()
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': email
    }
    service.permissions().create(
        fileId=sheet_id,
        body=permission,
        fields='id'
    ).execute() 