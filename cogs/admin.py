import sqlite3
from discord import TextChannel
from discord.ext import commands
from random import choice as random_choice
from cogs.utils.messages import update_banner, rejections
from cogs.utils.misc import check_admin_rights
from contextlib import closing


class AdminCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def say(self, ctx, channel_id: str, *, message_text):
        if ctx.author.id in [173747843314483210, 270744594243649536]:
            if isinstance(ctx.channel, TextChannel):
                try:
                    await ctx.message.delete()
                except:  # TODO find the proper name for the permissions exception
                    pass
            if '#' not in channel_id:
                dest_channel = ctx.bot.get_channel(int(channel_id))
                await dest_channel.send(message_text)
            else:
                channel_id = channel_id.strip('<#>')
                dest_channel = ctx.bot.get_channel(int(channel_id))
                await dest_channel.send(message_text)
        else:
            await ctx.send(random_choice(rejections))

    @commands.command()
    async def wipe_games(self, ctx):
        """Purges the game suggestions list, command available only to Admin role"""
        if await check_admin_rights(ctx):
            with closing(sqlite3.connect(self.bot.db_name)) as con:
                with con:
                    exists = con.execute('SELECT * FROM Suggestions WHERE suggestion_type=? LIMIT 1;',
                                         ('game',)).fetchall()
                if exists:
                    with con:
                        con.execute('DELETE FROM Suggestions WHERE suggestion_type=?;', ('game',))
                        exists = con.execute('SELECT * FROM Suggestions WHERE suggestion_type=? LIMIT 1;',
                                             ('game',)).fetchall()
                    if not exists:
                        await update_banner(ctx, 'games')
                        await ctx.send('Successfully deleted all the game suggestions')
                    else:
                        await ctx.send(
                            'Couldn\'t delete the game suggestions, please contact Euqimor for troubleshooting')
                else:
                    await ctx.send('No game suggestions found')
        else:
            await ctx.send(random_choice(rejections))

    @commands.command()
    async def wipe_movies(self, ctx):
        """Purges the movie suggestions list, command available only to Admin role"""
        if await check_admin_rights(ctx):
            with closing(sqlite3.connect(self.bot.db_name)) as con:
                with con:
                    exists = con.execute('SELECT * FROM Suggestions WHERE suggestion_type=? LIMIT 1;',
                                         ('movie',)).fetchall()
                if exists:
                    with con:
                        con.execute('DELETE FROM Suggestions WHERE suggestion_type=?;', ('movie',))
                        exists = con.execute('SELECT * FROM Suggestions WHERE suggestion_type=? LIMIT 1;',
                                             ('movie',)).fetchall()
                    if not exists:
                        await update_banner(ctx, 'movies')
                        await ctx.send('Successfully deleted all the movie suggestions')
                    else:
                        await ctx.send(
                            'Couldn\'t delete the movie suggestions, please contact Euqimor for troubleshooting')
                else:
                    await ctx.send('No movie suggestions found')
        else:
            await ctx.send(random_choice(rejections))

        @commands.command(hidden=True)
        async def wipe_banners(_ctx):
            if await _ctx.bot.is_owner(_ctx.author):
                guild = _ctx.guild
                channel = [x for x in guild.text_channels if x.name == 'game_suggestions_bot'][0]
                message_list = []
                async for message in channel.history(limit=100):
                    if message.author.id == _ctx.bot.user.id:
                        message_list.append(message)
                if message_list:
                    for message in message_list:
                        await message.delete()
            else:
                await _ctx.send(random_choice(rejections))


def setup(bot):
    bot.add_cog(AdminCog(bot))
