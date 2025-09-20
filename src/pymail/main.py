from functools import partial
from typing import List, Dict, Any, Optional
import os
import time
import json
import base64
import traceback

from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import typer
import rich
from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.markdown import Markdown, TextElement 
from rich.panel import Panel
from rich.text import Text

SCOPES = [
  'https://www.googleapis.com/auth/gmail.modify',
  'https://www.googleapis.com/auth/gmail.readonly'
]

HOMEPATH = f"{os.path.expanduser('~')}/.config/pymail"

PYMAIL_CREDS = f"{HOMEPATH}/credentials.json"
if os.environ.get("PYMAIL_CREDS", ""):
  PYMAIL_CREDS = os.environ["PYMAIL_CREDS"] 

MY_GMAIL = os.environ.get("MY_GMAIL", "")
USERID = "me"
MAXLIMIT = 300
BATCH_SIZE = 20

app = typer.Typer()
console = Console()

class MyHeading(TextElement):
  def __init__(self):
    super().__init__()
  def __rich_console__(
    self, console:Console, options:ConsoleOptions
  ) -> RenderResult:
    self.text.justify = "left"
    self.text.stylize("bold red")
    yield self.text

Markdown.elements['heading_open'] = MyHeading

def resolve_msg(
  msg_inbox:List[Dict[str,str]], req_id:int, response:Dict, exception:Any 
):
  try:
    msg = {}
    for header in response['payload']['headers']:
      for item in ['From', 'Subject', 'Date']:
        if header['name'] == item:
          msg[item.lower()] = header['value']
    msg['link'] = f"https://mail.google.com/mail/me/#inbox/{response['id']}"
    msg['snippet'] = f"{response['snippet']}"
    msg_inbox.append(msg)
  except Exception:
    console.print(f"Not resolved, req_id {req_id}!")
    console.print(f"Traceback {traceback.format_exc()}")

def get_credentials() -> Credentials:
  creds = None
  token_path = f"{HOMEPATH}/token.json"
  os.makedirs(HOMEPATH, exist_ok=True)
  if os.path.exists(token_path):
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
  console.print(f"credentials set? = {creds is not None}")
  start = time.time()
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      console.print("token expired!!")
      creds.refresh(Request())
      console.print("token refreshed!!")
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
        PYMAIL_CREDS, SCOPES
      )
      creds = flow.run_local_server(port=0)
    console.print(f"token generated! writing file to {token_path}")
    console.print(f"that took {time.time()-start:.3f}s")
    with open(token_path, 'w') as token:
      token.write(creds.to_json())
  return creds

def fetch_mails(
  query:str="", limit:int=5
) -> List[Optional[Dict[str,str]]]:
  creds = get_credentials()
  try:
    service = build("gmail", "v1", credentials=creds)
    res = service.users().messages().list(
      userId=USERID,
      maxResults=limit,
      q=query,
      labelIds=["INBOX"]
    ).execute()
    msgs = res.get('messages', [])
    msg_inbox = []
    n = len(msgs)
    batches = [msgs[i:i+BATCH_SIZE] for i in range(0, n, BATCH_SIZE)]
    for batch in batches:
      bt = service.new_batch_http_request()
      for msg in batch:
        bt.add(
          service.users().messages().get(userId=USERID, id=msg['id']),
          callback = partial(resolve_msg, msg_inbox)
        )
      bt.execute()
    return msg_inbox
  except HttpError as error:
    if error.resp.status == 403:
      console.print(f"Permission deined! Check API scopes..")
      console.print(f"{error.resp}")
  return []

def send_mail(
  to_addr:str,
  subject:str="Automated Mail",
  content:str="Hi,\n\nThis is an automated email\n\nRegards, PyMail",
) -> Dict:
  creds = get_credentials()
  send_message = None
  try:
    service = build("gmail", "v1", credentials=creds)
    message = EmailMessage()
    message.set_content(content)
    message["To"] = to_addr
    message["From"] = MY_GMAIL
    message["Subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {"raw": encoded_message}
    send_message = (
      service.users()
      .messages()
      .send(userId=USERID, body=create_message)
      .execute()
    )
    console.print("message sent!")
  except HttpError as error:
    console.print(f"An error occurred: {error}")
  return send_message

@app.command()
def fetch(query:str, limit:int):
  start = time.time()
  limit = min(limit, MAXLIMIT)
  console.print(f"query = {query}, limit = {limit} max allowed {MAXLIMIT}")
  with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description] {task.description}\n"),
    transient=True,
  ) as progress:
    progress.add_task(description='fetching mails..', total=limit)
    res = fetch_mails(query=query, limit=limit)
    if not res:
      console.print("Coundn't fetch mails! Check the logs!")
      return
  for msg in res:
    console.print(
      Panel(
        Markdown(
          f"""
## {msg['subject']}
\n{msg['snippet']}
\n[Open in browser]({msg['link']})
          """
        )
      )
    )
  console.print(f"Fetched requested mails in {time.time()-start:.3f}s")

@app.command()
def write():
  if not MY_GMAIL:
    console.print(f"$MY_GMAIL environment variable is not set!")
    console.print(f"Please set $MY_GMAIL to your gmail-id.")
    console.print(f"With `export MY_GMAIL=<your-gmail>`")
    return
  to_addr = Prompt.ask("To (recipient address)")
  subject = Prompt.ask("Subject")
  content = Prompt.ask("Content (body)")
  console.print(f"To: {to_addr}, Subject: {subject}")
  console.print(f"Content: {content}")
  confirmation = send_mail(to_addr, subject, content=content)
  console.print(json.dumps(confirmation, indent=2))

def cli(): app()

