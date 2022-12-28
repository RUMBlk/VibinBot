#Force deploy: b
#Global modules
import logging
import os
from dotenv import load_dotenv, find_dotenv
import traceback
import os.path
import discord
import debug as lib_debug

#Modules from local lib folder
import keepalive
import cogs
from database import *
import minecraft
import localisation as loc

logging.basicConfig(level=logging.INFO)

debug = False
debug_guild=None
bot_token=None
if not os.path.exists("tmp/"): os.mkdir("tmp/")

if os.getenv("DEBUG") == "eH2u":
    debug = True
    debug_guild=["926849077507928084", '1052177498651238439']
    print("DEBUG MODE ENABLED!")
    load_dotenv(find_dotenv())

BOT_TOKEN = None

intents = discord.Intents.none()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.members = True

bot = discord.Bot(intents = intents, debug_guilds=debug_guild)
#Debug
if debug:
   BOT_TOKEN = os.environ['DEBUG_TOKEN']
   bot.add_cog(lib_debug.debug_commands(bot))
else: BOT_TOKEN = os.environ['BOT_TOKEN']
#Main cogs
bot.add_cog(cogs.events(bot))
bot.add_cog(cogs.society(bot))
bot.add_cog(cogs.commands(bot))
#Minecraft cogs
bot.add_cog(minecraft.init(bot)) #init cog loads other Minecraft cogs

@bot.event
async def on_ready():
    await bot.sync_commands()
    print(loc.get('bot_is_ready'))

bot.run(BOT_TOKEN)
