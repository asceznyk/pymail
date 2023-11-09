#!/usr/bin/env python3

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
HOMEPATH = f"{os.path.expanduser('~')}/.config/pymail/"

msg_inbox: List[Dict[str, str]] = []

def resolve_msg(req_id:int, response:Dict, exception:Any=None):
  msg: Dict = {}
  for header in response['payload']['headers']:
    for item in ['From', 'Subject', 'Date']:
      if header['name'] == item: msg[item] = header['value']
  msg['Link'] = f"https://mail.google.com/mail/u/0/#inbox/{response['id']}"
  msg['Snippet'] = f"{response['snippet']}"
  msg_inbox.append(msg)

def get_credentials() -> Credentials:
  creds = None
  ftoken = f"{HOMEPATH}/token.json"
  os.makedirs(HOMEPATH, exist_ok=True)
  if os.path.exists(ftoken): ##extra
    creds = Credentials.from_authorized_user_file(ftoken, SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
        f"{HOMEPATH}/credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
      with open(ftoken, 'w') as token: token.write(creds.to_json())
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
  except HttpError as error: print(f'An error occurred: {error}')

def inbox(query:str, limit:int):
  start = time.time()
  fetch_mails('me', query, limit)
  formatted_json = json.dumps(msg_inbox, indent=2, sort_keys=True, ensure_ascii=False)
  colorful_json = highlight(
    formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter()
  )
  print(colorful_json)
  print(f"Retrieved the top {len(msg_inbox)} messages in {time.time() - start:.4f} s")

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("-q", "--query", default="", help="query to search mail")
  ap.add_argument("-l", "--limit", default=20, help="limit for number of results")
  args = ap.parse_args()
  inbox(args.query, args.limit)


