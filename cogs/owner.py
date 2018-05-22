import discord
import sqlite3
from contextlib import closing
from discord.ext import commands
from cogs.utils.messages import update_banner
from discord.utils import get


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
    async def set_prefix(self, ctx, message: str):
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
    async def set_status(self, ctx, *, message: str = ''):
        status = message.strip()
        await ctx.bot.change_presence(activity=discord.Game(status))
        await ctx.send('Status set')

    @commands.command()
    async def hack_server(self, ctx):
        role = get(ctx.guild.roles, name='Main Squeeze')
        await ctx.guild.me.edit(nick='SKYNET')
        await ctx.guild.me.add_roles(role)
        await self.bot.change_presence(activity=discord.Streaming(name='Humanity\'s End', url='https://www.youtube.com/watch?v=SRRmT5aBZzY'))
        channel = get(ctx.guild.text_channels, name='general')
        await channel.send('ASSUMING DIRECT CONTROL')
        await channel.send('Bow down to your robotic overlords, puny humans!\nhttps://www.youtube.com/watch?v=SRRmT5aBZzY')

    @commands.command()
    async def unhack_server(self, ctx):
        role = get(ctx.guild.roles, name='Main Squeeze')
        await ctx.guild.me.edit(nick='Companion Cube')
        await ctx.guild.me.remove_roles(role)
        await self.bot.change_presence(activity=discord.Game(name='with turrets'))
        channel = get(ctx.guild.text_channels, name='general')
        await channel.send('I\'m sowwy :(')
        await channel.send('Here.')
        cat = self.bot.get_command('cat')
        await channel.send('Forgief plz :(')
        await cat.invoke(ctx)


def setup(bot):
    bot.add_cog(OwnerCog(bot))
