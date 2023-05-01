import discord
from discord.ext import tasks, commands
import database as db
import datetime
from datetime import timezone
import localisation as loc
from uuid import uuid4
import re
from hashlib import sha256
import sharecode

async def attachments_to_url(attachments):
    urls = ''
    for item in attachments:
        urls += f'{item.url}\n'
    return urls[:-1]

async def format(bot, content, reference = None, attachments = None, timeformats = None):
    if hasattr(reference, 'message_id'):
        channel = await bot.fetch_channel(reference.channel_id)
        reference = await channel.fetch_message(reference.message_id)
        refname = reference.author.display_name
        if reference.is_system is True: tag = f'{refname}[SYSTEM]'
        elif reference.author.bot is False: tag = await sharecode.hashtag(refname, reference.author.mention)
        else: tag = f'{refname}[B]'
        reply = f'> >**{tag}**: '
        if reference.content != '':
            reply_len = 80-len(reply)
            reply_content = re.sub(r'> >.*\n', '', reference.content, 1)[:reply_len].split('\n')[0]
            if len(reference.content) > reply_len: reply_content = f'{reply_content[:-3]}...'
        else: reply_content = 'Attachment(s) or/and embed(s)'
        content = f'{reply}{reply_content}\n{content}'
    if attachments != []:
        urls = await attachments_to_url(attachments)
        if content != '': content = f'{content}\n{urls}'
        else: content = urls

    if timeformats is not None:
        for match in timeformats:
            timestamp = int(datetime.datetime.now(timezone.utc).replace(hour = 0, minute = 0, second = 0, microsecond = 0).timestamp())
            match = match[0]
            tf_split = match.split(':')
            for i in range(len(tf_split)):
                murica = 'AM'.lower() in tf_split[-1].lower() or 'PM'.lower() in tf_split[-1].lower()
                if i == len(tf_split)-1:
                    if '+' in tf_split[i]: timestamp -= int(tf_split[i].split('+')[-1])*3600
                    elif '-' in tf_split[i]: timestamp += int(tf_split[i].split('-')[-1])*3600
                    if 'PM'.lower() in tf_split[i].lower(): timestamp += 3600*12
                    tf_split[i] = tf_split[i][:2]
                if i == 0:
                    if murica and int(tf_split[i][:2] == 12): tf_split[i] = 0 #bruhbruhbruh
                    try: 
                        timestamp += int(tf_split[i])*3600
                    except:
                        timestamp += int(tf_split[i][0])*3600
                elif i == 1: timestamp += int(tf_split[i])*60
            content = content.replace(f'<{match}>', f'<t:{timestamp}:t>')

    ids = re.findall(r'(?<=\<@)[0-9]+(?=\>)', content)
    for id in ids:
        mention = f'<@{id}>'
        try:
            user = await bot.fetch_user(id)
            tag = await sharecode.hashtag(user.display_name, mention)
        except:
            tag = await sharecode.hashtag('UnknownUser', mention)
        content = content.replace(mention, f'**{tag}**')

    content = re.sub(r'<@&[0-9]*>', '**[role]**', content)

    mention_blacklist = ['@everyone', '@here']
    for mention in mention_blacklist:
        content = content.replace(mention, f'**{mention[1:]}**')
    #a   
    return content

class filter(commands.Cog):
    bot = discord.Bot()
    locale_class = loc.locale().get('message_filter')
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        if message.author != self.bot.user:
            if message.channel.permissions_for(message.guild.me).manage_webhooks and message.channel.permissions_for(message.guild.me).manage_messages and not message.author.bot:
                webhooks = await message.channel.webhooks()
                webhook = discord.utils.get(webhooks, name = self.bot.user.name) #await get_webhook(webhooks, bot.user.name)
                if webhook is None: webhook = await message.channel.create_webhook(name=self.bot.user.name, reason = "Required for the bot to execute share code network commands!")
                if message.author.id != webhook:
                    content = message.content
                    timeregex = r'<(((((([0-9]|0[0-9]|1[0-2]):([0-5][0-9]))|([0-9]|0[0-9]|1[0-2]))( am| pm|am|pm| AM| PM|AM|PM))|(([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])))(((\+|\-)([0-9][0-9]|[0-9]))|))>'
                    timeformats = re.findall(timeregex, message.content) #:fumbo:
                    if timeformats != []:
                        for i in range(len(timeformats)):
                            if not('+' in timeformats[i][0] or '-' in timeformats[i][0]):
                                timeformats[i] = list(timeformats[i])
                                authorDB = db.members.get_or_none(db.members.GuildID == message.guild.id, db.members.UserID == message.author.id)
                                if authorDB is not None:
                                   content = content.replace(timeformats[i][0], timeformats[i][0]+authorDB.Timezone)
                                   timeformats[i][0] += authorDB.Timezone
                        content = await format(self.bot, content, message.reference, message.attachments, timeformats)
                        msg = await webhook.send(content, embeds = message.embeds, username = await sharecode.hashtag(message.author.display_name, message.author.mention), avatar_url = message.author.display_avatar, wait=True)
                        await message.delete()
                        await sharecode.transmit(self.bot, msg, msg.author, msg.content, msg.embeds)

    message_filter = discord.SlashCommandGroup("message_filter", locale_class.get('desc'))
    @message_filter.command(description = locale_class.get('desc'))
    async def timezone(self, ctx, timezone: str):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_func = self.locale_class.get('timezone')
        if re.findall(r'(((\+|\-)([0-9][0-9]|[0-9])))', timezone[:3]) == []:
            answer = locale_func.get('timezone_limit_error')
        else:
            authorDB = db.members.get_or_create(GuildID = guildDB.id, UserID = ctx.author.id)[0]
            authorDB.Timezone = timezone[:3]
            authorDB.save()
            answer = locale_func.get('success')
        await ctx.respond(content = answer, ephemeral = True)
