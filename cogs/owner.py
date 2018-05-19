import discord
import sqlite3
from contextlib import closing
from discord.ext import commands
from cogs.utils.misc import check_admin_rights
from cogs.utils.messages import update_banner, rejections, message_games_by_author, embed_suggestions_in_category
from random import choice as random_choice


class OwnerCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def status(self, ctx, user: discord.Member):
        if user.activity:
            await ctx.send(f'{user.name} is {user.activity.type.name}')
        else:
            await ctx.send(f'{user.name}: no activity')

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def mystatus(self, ctx):
        user = ctx.message.author
        await ctx.send(user.activity.type.name) if user.activity else await ctx.send('No activity')

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def stream(self, ctx):
        await self.bot.change_presence(activity=discord.Streaming(name="test", url="https://www.twitch.tv/123"))

    @commands.command()
    async def wipe_user(self, ctx, user_id: str):
        """Purges the user and all related content from the database, command available only to Admin role"""
        if await check_admin_rights(ctx):
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
        else:
            await ctx.send(random_choice(rejections))

    @commands.command(hidden=True)
    async def games_full(self, ctx):
        """Prints games suggested so far grouped by suggestion author's name"""
        message = message_games_by_author(ctx)
        await ctx.send(message)

    @commands.command(hidden=True)
    async def games_list(self, ctx):
        """Prints games suggested so far in one list"""
        e = embed_suggestions_in_category(ctx, 'game')
        author_pic_url = 'https://static-cdn.jtvnw.net/jtv_user_pictures/f01a051288087531-profile_image-70x70.png'
        e.set_thumbnail(url='https://cdn0.iconfinder.com/data/icons/social-network-7/50/16-128.png')
        e.set_author(name='AellaQ', url='https://www.twitch.tv/aellaq', icon_url=author_pic_url)
        await ctx.send(embed=e)

    @commands.command()
    async def set_prefix(self, ctx, message: str):  # TODO save permanently
        prefix = message.strip()
        if await check_admin_rights(ctx):
            ctx.bot.command_prefix = prefix
            await ctx.send('The prefix is set to ' + str(ctx.bot.command_prefix))
        else:
            await ctx.send(random_choice(rejections))

    @commands.command(aliases=['set_nickname'])
    async def set_nick(self, ctx, *, message: str = ''):
        nickname = message.strip()
        if await check_admin_rights(ctx):
            bot_member = [x for x in ctx.bot.get_all_members() if x.bot and x.id == ctx.bot.user.id][0]
            await bot_member.edit(nick=nickname)
            await ctx.send('Nickname set')
        else:
            await ctx.send(random_choice(rejections))

    @commands.command(aliases=['set_playing'])
    async def set_status(self, ctx, *, message: str = ''):  # TODO save permanently?
        status = message.strip()
        if await check_admin_rights(ctx):
            await ctx.bot.change_presence(activity=discord.Game(status))
            await ctx.send('Status set')
        else:
            await ctx.send(random_choice(rejections))


def setup(bot):
    bot.add_cog(OwnerCog(bot))
