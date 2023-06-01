import discord
import traceback
from discord.ext import tasks, commands
from datetime import datetime as dt
from datetime import date
import database as db
import localisation as loc

class moderation(commands.Cog):
    bot = discord.Bot()
    locale_class = loc.locale().get(f'{__name__}')

    def __init__(self, bot):
        self.bot = bot

    moderation = discord.SlashCommandGroup("moderation", locale_class.get('desc'))

    @moderation.command(description = locale_class.get('channel').get('desc'))
    async def channel(self, ctx):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_func = locale.get('moderation').get('channel')
        if not ctx.channel.permissions_for(ctx.guild.me).send_messages: answer = locale.get('bot_denied').format_map({'permission': locale.get('permissions').get('send_messages')})
        elif ctx.author != ctx.guild.owner: answer = locale_func.get('user_denied').format_map({'permission': locale.get('permissions').get('owner')})
        else:
            query = db.guilds.update(reports_channel = ctx.channel.id).where(db.guilds.GuildID == ctx.guild.id)
            query.execute()
            answer = locale_func.get('success')
        await ctx.respond(content=answer)

    @bot.message_command(name=locale_class.get('context_report'))
    async def report(self, ctx, message: discord.Message):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_func = locale.get(f'{__class__.__name__}').get('report')

        attachments = 'None'
        for item in message.attachments:
            if attachments == 'None':
                attachments = ''
            attachments += f'{item.url}\n'

        loc_map = {'author': message.author.mention, 'jump_url': message.jump_url, 'posted_at': int(message.created_at.timestamp()), 'reported_content': message.content, 'attachments': attachments}

        reported_content = locale_func.get('head').format_map(loc_map)
        if message.content != '': reported_content += locale_func.get('content').format_map(loc_map)
        if message.attachments: reported_content += locale_func.get(f'attach').format_map(loc_map)
        if message.embeds: reported_content += locale.get(f'embeds', guildDB.locale).format_map(loc_map)

        channel = await self.bot.fetch_channel(guildDB.reports_channel)
        to_react = await channel.send(content = reported_content, embeds = message.embeds)
        await to_react.add_reaction('✅')
            #await channel.send(content=locale().get(f'{status}report', guild.locale).format_map({'author_id': message.author.id, 'reported_content': message.content}))
        await ctx.respond(content = locale.get(locale_func.get('success')), ephemeral = True)

