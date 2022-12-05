import os
import discord
from dotenv import load_dotenv, find_dotenv
import traceback
import os.path
from Modules.database import *

debug = False
debug_guilds=None
bot_token=None
if not os.path.exists("tmp/"): os.mkdir("tmp/")


if os.getenv("DEBUG") != "eH2u":
    debug = True
    debug_guild=["926849077507928084"]
    print("DEBUG MODE ENABLED!")
    load_dotenv(find_dotenv())

intents = discord.Intents.none()
intents.guilds = True

bot = discord.Bot(intents = intents, debug_guilds=debug_guild)

import Modules.discord
Modules.discord.Bot(bot, os.environ['DELAY'], os.environ['BOT_TOKEN'], debug)
