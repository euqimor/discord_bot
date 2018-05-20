import discord
import sqlite3
from contextlib import closing
from discord.ext import commands
from cogs.utils.messages import update_banner, find_suggestion_name_by_index


class OwnerCog:
    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(hidden=True)
    @commands.guild_only()
    async def status(self, ctx, user: discord.Member):
        if user.activity:
            await ctx.send(f'{user.name} is {user.activity.type.name}')
        else:
            await ctx.send(f'{user.name}: no activity')

    @commands.command(hidden=True)
    @commands.guild_only()
    async def mystatus(self, ctx):
        user = ctx.message.author
        await ctx.send(user.activity.type.name) if user.activity else await ctx.send('No activity')

    @commands.command(hidden=True)
    @commands.guild_only()
    async def stream(self, ctx):
        await self.bot.change_presence(activity=discord.Streaming(name="test", url="https://www.twitch.tv/123"))

    @commands.command()
    @commands.guild_only()
    async def wipe_user(self, ctx, user_id: str):
        """Purges the user and all related content from the database, command available only to Admin role"""
        user_id = user_id.strip('<@>')
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                exists = con.execute('SELECT username FROM Users WHERE user_id=? LIMIT 1;', (user_id,)).fetchall()
            if exists:
                username = exists[0][0]
                with con:
                    con.execute('PRAGMA FOREIGN_KEYS=ON;')
                    con.execute('DELETE FROM Users WHERE user_id=?;', (user_id,))
                    exists = con.execute('SELECT username FROM Users WHERE user_id=? LIMIT 1;',
                                         (user_id,)).fetchall()
                if not exists:
                    await update_banner(ctx, 'movies')
                    await update_banner(ctx, 'games')
                    await ctx.send('Successfully deleted user {} from the database'.format(username))
                else:
                    await ctx.send('Couldn\'t delete the user, please contact Euqimor for troubleshooting')
            else:
                await ctx.send('User not found in the database')

    @commands.command()
    async def set_prefix(self, ctx, message: str):  # TODO save permanently
        prefix = message.strip()
        ctx.bot.command_prefix = prefix
        await ctx.send('The prefix is set to ' + str(ctx.bot.command_prefix))

    @commands.command(aliases=['set_nickname'])
    async def set_nick(self, ctx, *, message: str = ''):
        nickname = message.strip()
        bot_member = [x for x in ctx.bot.get_all_members() if x.bot and x.id == ctx.bot.user.id][0]
        await bot_member.edit(nick=nickname)
        await ctx.send('Nickname set')

    @commands.command(aliases=['set_playing'])
    async def set_status(self, ctx, *, message: str = ''):  # TODO save permanently?
        status = message.strip()
        await ctx.bot.change_presence(activity=discord.Game(status))
        await ctx.send('Status set')

    @commands.command(hidden=True)
    async def find(self, ctx, message_index: int, suggestion_index: int):
        guild = ctx.guild
        channel = discord.utils.get(guild.text_channels, name='game_suggestions_bot')
        message_list = await channel.history(limit=3).flatten()
        name = find_suggestion_name_by_index(message_list[message_index], suggestion_index)
        ctx.send(f'{name}')


def setup(bot):
    bot.add_cog(OwnerCog(bot))
