from __future__ import print_function

from typing import List, Dict, Union

import json
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from tqdm import tqdm

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

msgs_list: List[Dict[str, str]] = []

def fetch_msg(req_id:int, response:Dict, exception):
  msg: Dict = {}
  for header in response['payload']['headers']:
    if header['name'] == 'From': msg['From'] = header['value']
    if header['name'] == 'Subject': msg['Subject'] = header['value']
  msgs_list.append(msg)

def render_messages(user:Dict):
  print(f"Messages for {user['gmail']} - Limited to the first {user['limit']} mails\n")
  for msg in msgs_list:
    print(msg['From'])
    print(msg['Subject'])
    print('')

def get_credentials() -> Credentials:
  creds = None
  if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
      creds = flow.run_local_server(port=0)
      with open('token.json', 'w') as token:
        token.write(creds.to_json())
  return creds

def fetch_mails(user:Dict, query:str=''):
  creds = get_credentials()
  try:
    service = build('gmail', 'v1', credentials=creds)
    msgs = service.users().messages().list(
      userId=user['gmail'], maxResults=user['limit'], q=query
    ).execute().get('messages', [])
    bt = service.new_batch_http_request()
    for m in msgs:
      bt.add(
        service.users().messages().get(userId='me', id=m['id']), callback=fetch_msg
      )
    bt.execute()
  except HttpError as error:
    print(f'An error occurred: {error}')

def main():
  with open('config.json', 'r') as f: user = json.load(f)
  fetch_mails(user)
  render_messages(user)

if __name__ == '__main__': main()
