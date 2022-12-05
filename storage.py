import traceback
import dropbox
import os
import shutil
from datetime import datetime

class drop(object):
    def __init__(self, key, sec, token):
        self.dbx = dropbox.Dropbox(app_key = key,
                app_secret = sec,
                oauth2_refresh_token = token
        )

    def download(self, debug=False):
        try:
            if debug == True:
                print("You're in debug mode, do you really want to download storage?(Y/N): ")
                answer = ""
                while(answer != "Y" and answer != "N"):
                    answer = input().upper()
                    if answer != "Y" and answer != "N": print("Uncorrect answer, try again(Y/N): ")
                if answer == "Y": debug = False
            else:
                if not os.path.exists("tmp/"): os.mkdir("tmp/")
                dbx.dbx.files_download_to_file('tmp/session_last.zip', '/sessions/session_last.zip')
                shutil.unpack_archive("tmp/session_last.zip")
        except:
            print("Database not found! The new one will be created.")
            traceback.print_exc()

    def upload(self, path="tmp/session", debug = False):
        try:
            print("Shutting down:")
            print("Archiving session before closing...")
            shutil.make_archive(base_dir=path ,root_dir = path, format = 'zip', base_name = "tmp/")
            print("Uploading archive...")
            with open("tmp/session_last.zip", "rb") as f:
                dbx.dbx.files_upload(f.read(), "/sessions/session_last.zip", mode=dropbox.files.WriteMode.overwrite)
                f.close()
        except:
            print("Dropbox upload error!")
            traceback.print_exc()




