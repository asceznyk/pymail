# pymail
A small CLI tool to list and write mails. This is useful if you never want to leave your beloved terminal.


## Requires
```
setuptools
google-python-api-client
google-auth-oauthlib
google-auth-httplib2
rich
typer
```


## How to install
1. Clone the repo with `git clone https://github.com/asceznyk/pymail.git`
2. Create a python environment with `python3 -m venv pymail` or `conda create -n pymail python=3.11`. The `python` version should be `>= 3.10`
3. Download credentials `credentials.json` from google OAuth2 client-id. See [API Docs](https://developers.google.com/gmail/api/quickstart/python)
4. `mv credentials.json ~/.config/pymail` - Move it to your `.config/pymail` directory OR set `export PYMAIL_CREDS="./credentials.json"` 
5. Run `pymail fetch '' 2` - This will fetch 2 e-mails from your inbox


## Usage

- Fetch mails with `pymail fetch [STRING] [INTEGER]` - Fetches emails from your inbox. The first parameter is the query parameter, and the second parameter tells you how many mails to fetch.

- Write a mail with `pymail write` - Let's you write mail and send a mail.

