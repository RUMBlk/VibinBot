import traceback
import dropbox
import os
import shutil
from datetime import datetime

def download(dbx: dropbox.Dropbox, debug=False):
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
            dbx.files_download_to_file('tmp/VibinBot.db', '/VibinBot.db')
    except:
        print("Database not found! The new one will be created.")
        traceback.print_exc()

def upload(token: str, path="tmp/session"):
    dbx = dropbox.Dropbox(token)
    try:
        print("Shutting down:")
        print("Archiving session before closing...")
        shutil.make_archive(base_dir=path ,root_dir = path, format = 'zip', base_name = "tmp/")
        print("Uploading archive...")
        with open("tmp/session_last.zip", "rb") as f:
            dbx.files_upload(f.read(), "/sessions/session_last.zip", mode=dropbox.files.WriteMode.overwrite)
            f.close()
    except:
        print("Dropbox upload error!")
        traceback.print_exc()




