import discord
import traceback
from discord.ext import tasks, commands
import database as db
import localisation as loc
from uuid import uuid4
import binascii
import os
import cogs

class channel(commands.Cog):
    bot = discord.Bot()
    locale_class = loc.locale().get('channel')
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        if message.author.bot is False:
            bot = self.bot
            guildDB = db.guilds.get(db.guilds.GuildID == message.guild.id)
            channelDB = db.channels.get_or_create(ChannelID = message.channel.id)[0]
            if(channelDB.shareCode is not None):
                shareCode_channels =  db.channels.select().where((db.channels.shareCode == channelDB.shareCode) & (db.channels.ChannelID != message.channel.id))

                attachments = ''
                for item in message.attachments:
                    attachments += f'\n{item.url}'

                for channel in shareCode_channels:
                    channel = bot.get_channel(channel.ChannelID)
                    await channel.send(content = message.content + attachments, embeds = message.embeds, stickers = message.stickers)


    channel = discord.SlashCommandGroup("channel", locale_class.get('desc'))

    @channel.command(description = locale_class.get('shareCode_generate').get('desc'))
    async def sharecode_generate(self, ctx):
        guildDB = db.guilds.get(db.guilds.GuildID == ctx.guild.id)
        locale = loc.locale(guildDB.locale)
        locale_func = locale.get('channel').get('shareCode_generate')
        if not ctx.channel.permissions_for(ctx.guild.me).manage_webhooks: answer = locale.get("bot_denied")
        elif ctx.channel.permissions_for(ctx.author).manage_webhooks:
            sharecode = str(uuid4())
            channelDB = db.channels.get_or_create(ChannelID = ctx.channel.id)[0]
            channelDB.shareCode = sharecode
            channelDB.save()
            answer = locale_func.get('success')
        await ctx.respond(content = answer.format_map({'shareCode': sharecode, 'permission': locale.get('manage_webhooks')}))

    @channel.command(description = locale_class.get('shareCode_set').get('desc'))
    async def sharecode_set(self, ctx, sharecode):
        guildDB = db.guilds.get(db.guilds.GuildID == ctx.guild.id)
        locale = loc.locale(guildDB.locale)
        locale_func = locale.get('channel').get('shareCode_set')
        channelDB = db.channels.get_or_create(ChannelID = ctx.channel.id)[0]
        channelDB.shareCode = sharecode
        channelDB.save()
        await ctx.respond(content = locale_func('success').format_map({'shareCode': sharecode}))
