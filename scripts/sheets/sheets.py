import google.oauth2.service_account
import apiclient.discovery
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
import logging

logger = logging.getLogger("perfsheets")


class Sheets:
    def __init__(self, sheetid, cell_range, service_account_file):
        self.sheetid = sheetid
        self.service_account = service_account_file
        self.cell_range = cell_range

    def _get_sheets_service(self, read_only: bool = False):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        self.credentials = (
            google.oauth2.service_account.Credentials.from_service_account_file(
                str(self.service_account),
                scopes=scopes,
            )
        )
        return apiclient.discovery.build("sheets", "v4", credentials=self.credentials)

    def create(self, title):
        """Create a spreadsheet with title"""
        spreadsheet = {"properties": {"title": title}}
        try:
            spreadsheet = (
                self._get_sheets_service()
                .spreadsheets()
                .create(body=spreadsheet, fields="spreadsheetId")
                .execute()
            )
            logger.info(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
            self.sheetid = spreadsheet.get("spreadsheetId")
        except HttpError as error:
            raise Exception(f"An error occurred while creating google sheet: {error}")

    def create_permission(self, email):
        """Adds write permissions for email user to the generated sheet"""

        permission = {
            "type": "user",
            "role": "writer",
            "emailAddress": email,
        }

        service = apiclient.discovery.build("drive", "v3", credentials=self.credentials)
        try:
            service.permissions().create(fileId=self.sheetid, body=permission).execute()
        except HttpError as error:
            raise Exception(
                f"An error occurred while adding permissions to google sheet: {error}"
            )

    def auto_resize_columns(self):
        """Resizes columns in a Google Sheet to fit the data."""
        request_body = {
            "requests": [
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": 0,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 7,
                        }
                    }
                }
            ]
        }
        try:
            self._get_sheets_service().spreadsheets().batchUpdate(
                spreadsheetId=self.sheetid, body=request_body
            ).execute()
        except HttpError as error:
            raise Exception(f"Resizing columns failed: {error}")

    def get_values(self) -> list[list]:
        """
        Get current cell values from the spreadsheet
        """
        try:
            result = (
                self._get_sheets_service()
                .spreadsheets()
                .values()
                .get(spreadsheetId=self.sheetid, range=self.cell_range)
                .execute()
            )
            values = result.get("values", [])
            return values
        except HttpError as error:
            raise Exception(f"{error} while getting values from google sheet")

    def update_values(self, new_values: list[list]):
        """
        Update cell values in google sheet
        """
        try:
            body = {"values": new_values}
            result = (
                self._get_sheets_service()
                .spreadsheets()
                .values()
                .update(
                    spreadsheetId=self.sheetid,
                    range=self.cell_range,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")
