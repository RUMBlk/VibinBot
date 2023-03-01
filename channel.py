import discord
import traceback
from discord.ext import tasks, commands
import database as db
import localisation as loc
from uuid import uuid4
import binascii
import os

async def transmit(bot, shareCode_channels, content, embeds = None, stickers = None, webhook = False, member = None):
    for channel in shareCode_channels:
        channel = bot.get_channel(channel.ChannelID)
        if webhook is False:
           await channel.send(content = content, embeds = embeds, stickers = stickers)
        else:
            bot_name = bot.user.name
            webhook = None
            webhooks = await channel.webhooks()
            for item in webhooks:
                if item.name == bot_name:
                    webhook = item
                    break
            if webhook is None: webhook = await channel.create_webhook(name=bot_name, reason = "Required for the bot to execute share code network commands!")
            if member is None: await webhook.send(content = content, embeds = embeds)
            else: await webhook.send(content = content, embeds = embeds, username = member.display_name, avatar_url = member.display_avatar)

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

                await transmit(bot, shareCode_channels, content = message.content + attachments, embeds = message.embeds, stickers = message.stickers, webhook = True, member = message.author)


    channel = discord.SlashCommandGroup("channel", locale_class.get('desc'))

    @channel.command(description = locale_class.get('sharecode').get('desc'))
    async def sharecode(self, ctx, sharecode = None):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_func = locale.get('channel').get('sharecode')
        if not ctx.channel.permissions_for(ctx.guild.me).manage_webhooks: answer = locale.get("bot_denied")
        elif not ctx.channel.permissions_for(ctx.author).manage_webhooks: answer = locale.get('user_denied')
        else:
            channelDB = db.channels.get_or_create(ChannelID = ctx.channel.id)[0]
            if sharecode is None:
                sharecode = str(uuid4())
                answer = locale_func.get('generated')
            elif sharecode.lower() == 'none':
                shareCode_channels = db.channels.select().where((db.channels.shareCode == channelDB.shareCode) & (db.channels.ChannelID != ctx.channel.id))
                sharecode = None
                await transmit(self.bot, shareCode_channels,content = locale_func.get('on_left').format_map({'shareCode': sharecode, 'guild': ctx.guild.name, 'channel': ctx.channel.name, 'permission': locale.get('permissions').get('manage_webhooks')}))
                answer = locale_func.get('delete')
            elif channelDB.shareCode == sharecode: answer = locale_func.get('exists')
            else: 
                shareCode_channels = db.channels.select().where((db.channels.shareCode == sharecode) & (db.channels.ChannelID != ctx.channel.id))
                await transmit(self.bot, shareCode_channels,content = locale_func.get('on_join').format_map({'shareCode': sharecode, 'guild': ctx.guild.name, 'channel': ctx.channel.name, 'permission': locale.get('permissions').get('manage_webhooks')}))
                answer = locale_func.get('set')
            channelDB.shareCode = sharecode
            channelDB.save()
        await ctx.respond(content = answer.format_map({'shareCode': sharecode, 'guild': ctx.guild.name, 'channel': ctx.channel.name, 'permission': locale.get('permissions').get('manage_webhooks')}), ephemeral = True)

    #@channel.command(description = locale_class.get('shareCode_generate').get('desc'))
    #async def sharecode_generate(self, ctx):
    #    guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
    #    locale = loc.locale(guildDB.locale)
    #    locale_func = locale.get('channel').get('shareCode_generate')
    #    if not ctx.channel.permissions_for(ctx.guild.me).manage_webhooks: answer = locale.get("bot_denied")
    #    elif ctx.channel.permissions_for(ctx.author).manage_webhooks:
    #        sharecode = str(uuid4())
    #        channelDB = db.channels.get_or_create(ChannelID = ctx.channel.id)[0]
    #        channelDB.shareCode = sharecode
    #        channelDB.save()
    #        answer = locale_func.get('success')
    #    await ctx.respond(content = answer.format_map({'shareCode': sharecode, 'permission': locale.get('permissions').get('manage_webhooks')}))

    #@channel.command(description = locale_class.get('shareCode_set').get('desc'))
    #async def sharecode_set(self, ctx, sharecode):
    #    guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
    #    locale = loc.locale(guildDB.locale)
    #    locale_func = locale.get('channel').get('shareCode_set')
    #    channelDB = db.channels.get_or_create(ChannelID = ctx.channel.id)[0]
    #    channelDB.shareCode = sharecode
    #    channelDB.save()
    #    await ctx.respond(content = locale_func('success').format_map({'shareCode': sharecode}))
