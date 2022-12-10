import logging
import os
import discord
from dotenv import load_dotenv, find_dotenv
import traceback
import os.path
from database import *
import VB_discord
import keepalive

debug = False
debug_guild=None
bot_token=None
if not os.path.exists("tmp/"): os.mkdir("tmp/")

if os.getenv("DEBUG") == "eH2u":
    debug = True
    debug_guild=["926849077507928084"]
    print("DEBUG MODE ENABLED!")
    load_dotenv(find_dotenv())

BOT_TOKEN = None
if debug: BOT_TOKEN = os.environ['DEBUG_TOKEN']
else: BOT_TOKEN = os.environ['BOT_TOKEN']

intents = discord.Intents.none()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = discord.Bot(intents = intents, debug_guilds=debug_guild)

logging.basicConfig(level=logging.INFO)

VB_discord.Bot(bot, os.environ['DELAY'], BOT_TOKEN, debug)
