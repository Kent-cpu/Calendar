import json
import httplib2
import apiclient.discovery
import gspread
from pprint import pprint
from oauth2client.service_account import ServiceAccountCredentials


CREDENTIALS_FILE = 'creds.json'
# ID Google Sheets документа (можно взять из его URL)
spreadsheet_id = '1BbjZxzIjTQ1ACC0q3kYqXJl-0RChhXQe_viwL7tF1PI'
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)

# Пример чтения файла
values = service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range='A2:E5',
    majorDimension='COLUMNS'
).execute()

buf = values.get("Физ-ра")
#print(values.keys())
print(values['values'][0][0])