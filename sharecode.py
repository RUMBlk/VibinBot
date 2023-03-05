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

async def attachments_to_url(attachments):
    urls = ''
    for item in attachments:
        urls += f'{item.url}\n'
    return urls[:-1]

async def format(bot, content, reference = None, attachments = None):
    if hasattr(reference, 'message_id'):
        channel = await bot.fetch_channel(reference.channel_id)
        reference = await channel.fetch_message(reference.message_id)
        tag = await hashtag(reference.author.display_name, reference.author.mention)
        reply = f'> >{tag}: '
        if reference.content != '':
            reply_content = re.sub(r'> >.*\n', '', reference.content, 1)[:80-len(reply)]
        else: reply_content = 'Attachment(s) or/and embed(s)'
        content = f'{reply}{reply_content}\n{content}'
    if attachments != []:
        urls = await attachments_to_url(attachments)
        if content != '': content = f'{content}\n{urls}'
        else: content = urls
    return content

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
                content = await format(bot, content, message.reference, message.attachments)
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
                formated_content = await format(bot, message.content, message.reference, message.attachments)
                for item in network:
                    channel = self.bot.get_channel(item.ChannelID)
                    webhooks = await channel.webhooks()
                    self.webhook = discord.utils.get(webhooks, name = self.bot.user.name)
                    self.fetchedMessage = await channel.history(around = message.created_at, limit=11).find(lambda m: f'#{tag}' in m.author.name and m.content == formated_content) 
                    async for msg in channel.history(around = message.created_at, limit = 11):
                        print(msg.content)

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
        msgType_whitelist = [discord.MessageType.default, discord.MessageType.reply]
        if isinstance(message.channel, discord.TextChannel) and message.type in msgType_whitelist and message.channel.permissions_for(message.guild.me).manage_webhooks:
            webhooks = await message.channel.webhooks()
            webhook = discord.utils.get(webhooks, name = self.bot.user.name)
            if webhook is not None: webhook = webhook.id
            if message.author.id != webhook:
                guildDB = db.guilds.get(db.guilds.GuildID == message.guild.id)
                channelDB = db.channels.get_or_create(ChannelID = message.channel.id)[0]
                if(channelDB.shareCode is not None):
                    shareCode_channels =  db.channels.select().where((db.channels.shareCode == channelDB.shareCode) & (db.channels.ChannelID != message.channel.id))
                    await transmit(self.bot, message)

    @commands.Cog.listener("on_message_delete")
    async def on_message_delete(self, message):
        if isinstance(message.channel, discord.TextChannel) and message.channel.permissions_for(message.guild.me).manage_webhooks:
            tm = await transmitted().fetch(self.bot, message)
            await tm.delete()

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit(self, before, after):
        if isinstance(before.channel, discord.TextChannel) and before.channel.permissions_for(before.guild.me).manage_webhooks:
            tm = await transmitted().fetch(self.bot, before)
            formated_content = await format(self.bot, after.content, after.reference, after.attachments)
            await tm.edit(content = formated_content, embeds = after.embeds)
            

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

    @channel.command(description = locale_class.get('desc'))
    async def deletemsg(self, ctx, message_id):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_class = locale.get('sharecode')
        locale_func = locale_class.get('deleteMsg')
        locale_map = {'messageID': message_id}
        message = await ctx.channel.fetch_message(message_id)
        if ctx.author == message.author:
            tm = await transmitted().fetch(self.bot, message)
            await tm.delete()
            answer = locale_func.get('success')
        else: answer = locale_func.get('fail')
        await ctx.respond(content = answer.format_map(locale_map), ephemeral = True)
