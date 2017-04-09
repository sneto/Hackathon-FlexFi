from __future__ import print_function

import os
import time
from apiclient import discovery
from apiclient import http

import httplib2
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from DriveFile import DriveFile
from FilesList import FilesList
import Object2CsvConverter

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


class GoogleDrive:
    def __init__(self):
        self.drive_service = None
        self.input_folders = ["1.JSON", "2.XML"]
        self.output_folder = "3.Output"
        self.mime_json = 'application/json'
        self.mime_xml = 'text/xml'
        self.LastUsedToken = ""
        self.user_directory = os.path.expanduser('~')
        self.credentials_directory = os.path.join(self.user_directory, '.flexfi')
        # self.temp_directory = os.path.join(user_directory, '.temp')
        self.temp_directory = self.credentials_directory

        # If modifying these scopes, delete your previously saved credentials
        # at ~/.credentials/drive-python-quickstart.json
        self.SCOPES = 'https://www.googleapis.com/auth/drive'
        self.CLIENT_SECRET_FILE = 'client_secret.json'
        self.APPLICATION_NAME = 'FlexFi-Python'
        self.Credentials = None
        self.iniciate()

    def iniciate(self):
        """Creates the main objects to this class work correctly."""

        self.get_credentials()
        http = self.Credentials.authorize(httplib2.Http())
        self.drive_service = discovery.build('drive', 'v3', http=http)

    def get_credentials(self):
        """Gets valid user credentials from storage or shows the login page in a browser.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        """
        if not os.path.exists(self.credentials_directory):
            os.makedirs(self.credentials_directory)

        credential_path = os.path.join(self.credentials_directory,
                                       'drive-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        self.Credentials = credentials

    def get_initial_page_token(self):
        """Gets a initial page token."""
        response = self.drive_service.changes().getStartPageToken().execute()
        print('Start token: %s' % response.get('startPageToken'))
        return response.get('startPageToken')

    def save_page_token(self):
        """Save a pagetoken to a file"""
        page_token_path = os.path.join(self.credentials_directory, 'page_token.txt')

        if os.path.exists(page_token_path):
            os.remove(page_token_path)

        with open(page_token_path, "w+") as file:
            file.write(self.LastUsedToken)

    def get_page_token(self):
        """Get a pagetoken (try first on file and then in the api)"""
        page_token_path = os.path.join(self.credentials_directory, 'page_token.txt')

        def get_inicial_token():
            self.LastUsedToken = self.get_initial_page_token()
            # Save the token to file, so if the application is restarted, it will use the saved token
            self.save_page_token()

        if not os.path.exists(page_token_path):
            get_inicial_token()
            return True

        with open(page_token_path, "r") as file:
            self.LastUsedToken = file.readline()

        if not self.LastUsedToken:
            get_inicial_token()

        return True

    def check_file_removed(self, file_id):
        """Checks is a file was removed"""
        files_result = self.drive_service.files().get(fileId = file_id,
                                                      fields = "explicitlyTrashed").execute()

        if files_result:
            return files_result["explicitlyTrashed"]
        else:
            return False

    def get_changed_files(self):
        """Get a lista of changed files"""
        changed_files = []

        next_token = self.LastUsedToken

        while True:
            if not next_token:
                break

            response = self.drive_service.changes().list(pageToken=next_token,
                                                         spaces='drive').execute()
            # Saves the last used token
            self.LastUsedToken = next_token

            changes = response.get('changes')

            if not changes or len(changes) == 0:
                break

            for change in response.get('changes'):
                # Process change
                file = change.get("file")
                removed = change["removed"]

                if removed:
                    continue

                trashed = self.check_file_removed(change.get('fileId'))
                if not trashed:
                    mime_type = file.get('mimeType')

                    drive_file = DriveFile()

                    if mime_type == self.mime_json:
                        drive_file.Type = "json"
                    elif mime_type == self.mime_xml:
                        drive_file.Type = "xml"
                    else:
                        continue

                    drive_file.Id = change.get('fileId')
                    drive_file.Name = file.get('name')
                    drive_file.Content = self.download_file_content(drive_file.Id)

                    changed_files.append(drive_file)

            # if there is another page, get its token to its data
            if response.get('newStartPageToken'):
                next_token = response.get('newStartPageToken')
            else:
                next_token = response.get('nextPageToken')

        return changed_files

    def get_files_to_process(self):
        """Get a list of files that must be processed"""
        return self.get_changed_files()

    def download_file_content(self, file_id):
        """Download a file content from api"""
        try:
            return self.drive_service.files().get_media(fileId=file_id).execute().decode("utf-8")
        except Exception as error:
            print('An error occurred: %s' % error)
            return None

    def process_file(self, file_to_process):
        # Instantiates the object that has the structure to receive the object splited data
        output_files_list = FilesList()

        if Object2CsvConverter.convert_file(file_to_process, output_files_list):
            file_to_process.ProcessedFile = output_files_list
            self.send_to_drive(file_to_process)

    def watch_changes(self):
        """Watch for file changes in the drive files"""

        # Loads a page token before starting the api requests
        self.get_page_token()

        while True:
            files_to_process = self.get_files_to_process()

            if files_to_process and len(files_to_process) > 0:
                for file in files_to_process:
                    try:
                        self.process_file(file)
                    except Exception as e:
                        print("Error: " + e)
                        # TODO register log

            self.save_page_token()
            # sleep for 10 seconds before checking the drive for changes again
            time.sleep(10)

    def find_or_create_out_folder(self):
        """Find os create a remote folder"""

        files_result = self.drive_service.files().list(q="name='" + self.output_folder + "' and mimeType='application/vnd.google-apps.folder'").execute()

        if files_result and files_result["files"] and len(files_result["files"]) > 0:
            return files_result.get("files")[0].get("id")
        else:
            file_metadata = {
                'name': self.output_folder,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            created_file = self.drive_service.files().create(body=file_metadata,
                                                             fields='id').execute()
            return created_file.get('id')

    def delete_file_if_exists(self, parent_id, file_name):
        files_result = self.drive_service.files().list(
            q="name='" + file_name + "' and '" + parent_id + "' in parents").execute()
        # q = "name='" + self.output_folder + "' and '" + parent_id + "' in parents '").execute()

        if files_result and len(files_result.get("files")) > 0:
            for file in files_result.get("files"):
                self.drive_service.files().delete(fileId = file.get("id")).execute()

    def send_to_drive(self, processed_file):
        """Send a processed file and its content to the drive"""
        folder_id = self.find_or_create_out_folder()

        for sub_file in processed_file.ProcessedFile.Files:
            name = processed_file.Name + "_" + sub_file.Name + ".csv"

            self.delete_file_if_exists(folder_id, name)

            if not os.path.exists(self.temp_directory):
                os.makedirs(self.temp_directory)

            tmp_file_path = os.path.join(self.temp_directory, name)

            file_metadata = {
                'name': name,
                'parents': [folder_id]
            }

            # Generates a file in the disk to upload to the drive
            sub_file.generate_csv_content_file(tmp_file_path)
            media_body = http.MediaFileUpload(tmp_file_path, "text/csv")

            try:
                self.drive_service.files().create(body=file_metadata,
                                                  media_body=media_body,
                                                  fields='id').execute()
                media_body.stream().close()
            except Exception as e:
                print("Error while sending the CSV file: " + e)
            finally:
                os.remove(tmp_file_path)
