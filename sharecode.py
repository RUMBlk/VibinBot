import discord
import traceback
from discord.ext import tasks, commands
import database as db
import localisation as loc
from uuid import uuid4
import binascii
import os
import re
from hashlib import sha256
import asyncio

async def hashtag(name, mention, salt = os.getenv('salt')):
    if salt is not None: mention = mention+salt
    hex = sha256(mention.encode()).hexdigest()[:8]
    lat4 = ''
    for i in range(4):
        num = int(hex[(2*i):2+(2*i)], 16) % 74 + 48
        if (num >= 91 and num <= 96) or (num >= 58 and num <= 64): num += 10
        lat4 += chr(num)
    return f'{name}#{lat4}'

async def attachments_to_url(message):
    attachments = ''
    for item in message.attachments:
        attachments += f'\n{item.url}'
    return attachments

async def transmit(bot, message = None, sender = None, content = None, embeds = [], mimic = True):
    author_id = None
    if message is not None: 
        sender = message.channel
        author_id = message.author.id
        tag = await hashtag(message.author.display_name, message.author.mention)

    webhooks = await sender.webhooks()
    webhook = discord.utils.get(webhooks, name = bot.user.name)
    if webhook is None: webhook = await sender.create_webhook(name=bot.user.name, reason = "Required for the bot to execute share code network commands!")
    if author_id != webhook.id:
        channelDB = db.channels.get_or_create(ChannelID = sender.id)[0]
        network = db.channels.select().where((db.channels.shareCode == channelDB.shareCode) & (db.channels.shareCode != None) & (db.channels.ChannelID != sender.id))
        if network is not None:
            if message is not None:
                if content is None: content = message.content
                if embeds is None: embeds = message.embeds
            else: mimic = False

            mentions = re.findall(r'@.*#\d\d\d\d', content)
            for item in network:
                channel = bot.get_channel(item.ChannelID)
                webhooks = await channel.webhooks()
                webhook = discord.utils.get(webhooks, name = bot.user.name) #await get_webhook(webhooks, bot.user.name)

                for mention in mentions:
                    split = mention.split('#')
                    ping = discord.utils.get(channel.guild.members, name=split[0][1:], discriminator=split[1])
                    if ping is not None:
                        content = content.replace(mention, f'{ping.mention}')

                if webhook is None: webhook = await channel.create_webhook(name=bot.user.name, reason = "Required for the bot to execute share code network commands!")
                if mimic is False: await webhook.send(content = content, embeds = embeds, avatar_url = bot.user.display_avatar)
                else: await webhook.send(content = content, embeds = embeds, username = tag, avatar_url = message.author.display_avatar)

class transmitted():
    webhook = None
    fetchedMessage = None

    async def fetch(self, bot, message):
        self.bot = bot 
        self.message = message
        webhooks = await message.channel.webhooks()
        webhook = discord.utils.get(webhooks, name = bot.user.name)
        if webhook is not None: webhook = webhook.id
        if message.author.id != webhook:
            tag = await hashtag(message.author.name, message.author.mention)
            tag = tag.split('#')[-1]
            channelDB = db.channels.get_or_create(ChannelID = message.channel.id)[0]
            network = db.channels.select().where((db.channels.shareCode == channelDB.shareCode) & (db.channels.shareCode != None) & (db.channels.ChannelID != message.channel.id))
            if network is not None:
                for item in network:
                    channel = self.bot.get_channel(item.ChannelID)
                    webhooks = await channel.webhooks()
                    self.webhook = discord.utils.get(webhooks, name = self.bot.user.name)
                    #attachments = await attachments_to_url(message).split('\n')
                    self.fetchedMessage = await channel.history(around = message.created_at).find(lambda m: f'#{tag}' in m.author.name and m.content == message.content and m.embeds == message.embeds)
        return self
        
    async def delete(self):
        if self.fetchedMessage is not None: await self.webhook.delete_message(message_id = self.fetchedMessage.id)
    async def edit(self, content, embeds):
        if self.fetchedMessage is not None: await self.webhook.edit_message(message_id = self.fetchedMessage.id, content = content, embeds = embeds)

class sharecode(commands.Cog):
    bot = discord.Bot()
    locale_class = loc.locale().get('sharecode')
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        print(message.attachments)
        if isinstance(message.channel, discord.TextChannel) and message.channel.permissions_for(message.guild.me).manage_webhooks:
            webhooks = await message.channel.webhooks()
            webhook = discord.utils.get(webhooks, name = self.bot.user.name)
            if webhook is not None: webhook = webhook.id
            if message.author.id != webhook:
                guildDB = db.guilds.get(db.guilds.GuildID == message.guild.id)
                channelDB = db.channels.get_or_create(ChannelID = message.channel.id)[0]
                if(channelDB.shareCode is not None):
                    shareCode_channels =  db.channels.select().where((db.channels.shareCode == channelDB.shareCode) & (db.channels.ChannelID != message.channel.id))

                    attachments = await attachments_to_url(message)
                    await transmit(self.bot, message, content = message.content + attachments)

    @commands.Cog.listener("on_message_delete")
    async def on_message_delete(self, message):
        if message.channel.permissions_for(message.guild.me).manage_webhooks: 
            tm = await transmitted().fetch(self.bot, message)
            await tm.delete()

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit(self, before, after):
        if after.channel.permissions_for(after.guild.me).manage_webhooks: 
            tm = await transmitted().fetch(self.bot, before)
            await tm.edit(content = after.content, embeds = after.embeds)
            

    channel = discord.SlashCommandGroup("sharecode", locale_class.get('desc'))

    @channel.command(description = locale_class.get('desc'))
    async def generate(self, ctx):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_class = locale.get('sharecode')
        locale_func = locale_class.get('generate')
        locale_map = {'shareCode': None, 'guild': ctx.guild.name, 'channel': ctx.channel.name, 'permission': locale.get('permissions').get('manage_webhooks')}
        if not ctx.channel.permissions_for(ctx.guild.me).manage_webhooks: answer = locale.get("bot_denied")
        elif not ctx.channel.permissions_for(ctx.author).manage_webhooks: answer = locale.get('user_denied')
        else:
            channelDB = db.channels.get_or_create(ChannelID = ctx.channel.id)[0]
            sharecode = str(uuid4())
            locale_map['shareCode'] = sharecode
            await transmit(self.bot, sender = ctx.channel, content = locale_class.get('on_left').format_map(locale_map))
            channelDB.shareCode = sharecode
            channelDB.save()
            await transmit(self.bot, sender = ctx.channel, content = locale_class.get('on_join').format_map(locale_map))
            answer = locale_func.get('success')
        await ctx.respond(content = answer.format_map(locale_map), ephemeral = True)
        
    @channel.command(description = locale_class.get('desc'))
    async def set(self, ctx, sharecode = None):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_class = locale.get('sharecode')
        locale_func = locale_class.get('set')
        locale_map = {'shareCode': sharecode, 'guild': ctx.guild.name, 'channel': ctx.channel.name, 'permission': locale.get('permissions').get('manage_webhooks')}
        if not ctx.channel.permissions_for(ctx.guild.me).manage_webhooks: answer = locale.get("bot_denied")
        elif not ctx.channel.permissions_for(ctx.author).manage_webhooks: answer = locale.get('user_denied')
        else:
            channelDB = db.channels.get_or_create(ChannelID = ctx.channel.id)[0]
            await transmit(self.bot, sender = ctx.channel, content = locale_class.get('on_left').format_map(locale_map))
            channelDB.shareCode = sharecode
            channelDB.save()
            await transmit(self.bot, sender = ctx.channel, content = locale_class.get('on_join').format_map(locale_map))
            answer = locale_func.get('success')
        await ctx.respond(content = answer.format_map(locale_map), ephemeral = True)

    @channel.command(description = locale_class.get('desc'))
    async def remove(self, ctx):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_class = locale.get('sharecode')
        locale_func = locale_class.get('remove')
        locale_map = {'shareCode': None, 'guild': ctx.guild.name, 'channel': ctx.channel.name, 'permission': locale.get('permissions').get('manage_webhooks')}
        if not ctx.channel.permissions_for(ctx.guild.me).manage_webhooks: answer = locale.get("bot_denied")
        elif not ctx.channel.permissions_for(ctx.author).manage_webhooks: answer = locale.get('user_denied')
        else:
            channelDB = db.channels.get_or_create(ChannelID = ctx.channel.id)[0]
            await transmit(self.bot, sender = ctx.channel, content = locale_class.get('on_left').format_map({'shareCode': sharecode, 'guild': ctx.guild.name, 'channel': ctx.channel.name}))
            channelDB.shareCode = None
            channelDB.save()
            answer = locale_func.get('success')
        await ctx.respond(content = answer.format_map(locale_map), ephemeral = True)
