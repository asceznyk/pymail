# pymail

A small CLI client to list your mails from GMail. You can view your mails and also filter them according to your needs. Only thing being to acutally view the mails you might wanna visit the browser.


## Requires
`poetry`


## How to install

1. Clone the repo with `git clone https://github.com/asceznyk/pymail.git`
2. `cd` into the repo and `poetry install -v`
3. Download credentials `credentials.json` from google OAuth2 client-id. See ![Link](https://developers.google.com/gmail/api/quickstart/python)
4. Run `pymail`


## Usage

1. `pymail -q` to query your GMail inbox.
2. `pymail -l` to limit the number of mails.
3. `pymail -q "your query here" -l 10` to use both in combination.

