from __future__ import print_function

import os

from oauth2client import tools
import json
import xmltodict
import datetime
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

drive_service = None
output_folder = "3.Output"
mime_json = 'application/json'
mime_xml = 'text/xml'
application_token = ""
user_directory = os.path.expanduser('~')
credentials_directory = os.path.join(user_directory, '.flexfi')
temp_directory = credentials_directory

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'FlexFi-Python'
Credentials = None


def convert_json_to_object(file_content):
    """Converts a json string to object"""
    object = json.loads(file_content)
    print(object)
    return object


def convert_xml_to_object(file_content):
    """Converts a xml string to object"""
    object = xmltodict.parse(file_content, dict_constructor=dict)
    print(object)
    return object


def split_for_files(object, files_list, file_name = None):
    """Splits a object to any different files to be saved as CSV (because of the arrays)"""
    if not hasattr(object, "keys"):
        return

    current_file = "main" if not file_name else file_name

    keys = sorted(object.keys())

    for key in keys:
        if key.startswith("@"):
            continue

        children = object.get(key)

        is_array = isinstance(children, list);

        column_name = key

        if is_array:
            column_name += "[]"

        files_list.add_header(current_file, column_name)

        if (
            type(children) is str or
            type(children) is int or
            type(children) is datetime.date or
			type(children) is float
        ):
            files_list.set_column_value(current_file, column_name, children)

        if children:
            if is_array and len(children) > 0:
                # Add the column parent_index in the new file to link it with the parent one
                files_list.add_header(key, "parent_index")
                # Sets in the current file the concatenation between the name of the file that will be
                # generated and the id of the data that will be generated in this secondary file
                current_file_index = files_list.get_file_current_index(current_file)
                files_list.set_column_value(current_file, column_name, key + ":" + str(current_file_index))

                for child in children:
                    files_list.set_column_value(key, "parent_index", str(current_file_index))
                    split_for_files(child, files_list, key)
                    # Sets the new current index in the secondary file
                    files_list.increment_file_current_index(key)
            else:
                split_for_files(children, files_list, file_name)


def convert_file(file, output_files_list):
    """Converts a google drive file to an object ready to be saved."""
    # Converts the file from json/xml to a python object
    if file.Type == "json":
        converted_object = convert_json_to_object(file.Content)
    elif file.Type == "xml":
        converted_object = convert_xml_to_object(file.Content)
    else:
        # TODO Generate log
        return False

    split_for_files(converted_object, output_files_list)

    return True
