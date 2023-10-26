from __future__ import print_function

from typing import List, Dict, Union, Any

import os
import time
import json
import base64
import argparse

from pygments import highlight, lexers, formatters

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from tqdm import tqdm

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

msgs_list: List[Dict[str, str]] = []

def resolve_msg(req_id:int, response:Dict, exception:Any=None):
  msg: Dict = {}
  for header in response['payload']['headers']:
    for item in ['From', 'Subject', 'Date']:
      if header['name'] == item: msg[item] = header['value']
  msg['Link'] = f"https://mail.google.com/mail/u/0/#inbox/{response['id']}"
  msg['Snippet'] = f"{response['snippet']}"
  msgs_list.append(msg)

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

def fetch_mails(gmail:str, query:str, limit:int):
  creds = get_credentials()
  try:
    service = build('gmail', 'v1', credentials=creds)
    msgs = service.users().messages().list(
      userId=gmail, maxResults=limit, q=query
    ).execute().get('messages', [])
    bt = service.new_batch_http_request()
    for m in msgs:
      bt.add(
        service.users().messages().get(userId='me', id=m['id']), callback=resolve_msg
      )
    bt.execute()
  except HttpError as error:
    print(f'An error occurred: {error}')

def main(query:str, limit:int):
  start = time.time()
  with open('config.json', 'r') as f: user = json.load(f)
  fetch_mails('me', query, limit)
  formatted_json = json.dumps(msgs_list, indent=2, sort_keys=True, ensure_ascii=False)
  colorful_json = highlight(
    formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter()
  )
  print(colorful_json)
  print(f"Retrieved {len(msgs_list)} messages in {time.time() - start:.4f} s")

if __name__ == '__main__':
  ap = argparse.ArgumentParser()
  ap.add_argument("-q", "--query", default="", help="query to search mail")
  ap.add_argument("-l", "--limit", default=20, help="limit for number of results")
  to_args = {}
  args = ap.parse_args()
  for k in args.__dict__:
    to_args[k] = args.__dict__[k]
  main(**to_args)


