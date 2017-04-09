from __future__ import print_function

from oauth2client import tools
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

from GoogleDrive import GoogleDrive

drive_client = GoogleDrive()

def main():
    drive_client.watch_changes()

if __name__ == '__main__':
    main()
