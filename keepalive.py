from flask import Flask
from threading import Thread
import os

app=Flask("KeepAlive")

@app.route("/")
def index():
    return "<h1>VibinBot KeepAlive service</h1>"

Thread(target=app.run,args=("0.0.0.0", os.getenv("PORT"))).start()