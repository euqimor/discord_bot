from discord.ext import commands
from contextlib import closing
import sqlite3
import aiohttp
import difflib
import requests


class SteamCog:
    def __init__(self, bot):
        self.bot = bot
        self.get_steam_apps_list()

    def get_steam_apps_list(self):
        apps_url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
        r = requests.get(apps_url)
        r.raise_for_status()
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                con.execute(f'CREATE TABLE IF NOT EXISTS Steam (app_id INT PRIMARY KEY , app_name TEXT)')
                for app in r.json()['applist']['apps']:
                    app_id = app["appid"]
                    app_name = app["name"].lower().replace('™', '')
                    con.execute(f'INSERT OR IGNORE INTO Steam (app_id, app_name) VALUES (?, ?);', (app_id, app_name))

    async def get_steam_apps_list_async(self):
        apps_url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
        async with aiohttp.ClientSession() as session:
            async with session.get(apps_url) as r:
                r.raise_for_status()
                r_json = await r.json()
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                con.execute(f'CREATE TABLE IF NOT EXISTS Steam (app_id INT PRIMARY KEY , app_name TEXT)')
                for app in r_json['applist']['apps']:
                    app_id = app["appid"]
                    app_name = app["name"].lower().replace('™', '')
                    con.execute(f'INSERT OR IGNORE INTO Steam (app_id, app_name) VALUES (?, ?);', (app_id, app_name))

    @commands.group(invoke_without_command=True)
    async def steam(self, ctx, *, app_name=''):
        """
        Searches for a Steam item (game or any other title) matching the provided name and posts a link if found.
        Example:
        $steam the cat lady
        """
        async def post_results(result):
            if len(result) == 1:
                app_id = result[0][0]
                await ctx.send(f'https://store.steampowered.com/app/{app_id}/')
            else:
                disambiguation = f"Several titles with the same name found\n"
                for i in range(len(result)):
                    app_id = result[len(result) - i - 1][0]
                    disambiguation += f'\n{i+1}. https://store.steampowered.com/app/{app_id}/'
                await ctx.send(disambiguation)
        if app_name == '':
            await ctx.send('Please provide a name to search for')
            return
        app_name = app_name.strip().lower()
        if app_name[0] == '\"':
            app_name = app_name.strip('"')
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                result = con.execute('SELECT app_id FROM Steam WHERE app_name=?', (app_name,)).fetchall()
                if result:
                    await post_results(result)
                else:  # if game not found, update games list from Steam
                    await self.get_steam_apps_list_async()
                    result = con.execute('SELECT app_id FROM Steam WHERE app_name=?', (app_name,)).fetchall()
                    if result:
                        await post_results(result)
                    else:  # if still not found, search for relevant names
                        close_enough = con.execute('SELECT app_id FROM Steam WHERE app_name LIKE ?',
                                                   (f'%{app_name}%', )).fetchone()
                        app_names_list = [x[0] for x in con.execute('SELECT app_name FROM Steam').fetchall()]
                        matches = difflib.get_close_matches(app_name, app_names_list, cutoff=0.4)
                        if matches:
                            matches = '\n'.join(matches).title()
                            if close_enough:
                                await ctx.send(f'Exact match not found, here\'s a title containing `{app_name}`:\n'
                                               f'https://store.steampowered.com/app/{close_enough[0]}/\n'
                                               f'Other close matches:\n```\n{matches}\n```')
                            else:
                                await ctx.send(f'`{app_name}` not found, did you mean:\n```\n{matches}\n```')
                        else:
                            await ctx.send(f'Game "{app_name}" not found')

    @steam.command(aliases=['find'])
    async def search(self, ctx, *, app_name=''):
        """
        Searches for Steam items (games or any other titles) matching the provided name as closely as possible
        and posts a list of top matches.
        Example:
        $steam search edith finch
        """
        if app_name == '':
            await ctx.send('Please provide a name to search for')
            return
        app_name = app_name.strip().lower()
        if app_name[0] == '\"':
            app_name = app_name.strip('"')
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                partial_matches = con.execute('SELECT app_name FROM Steam WHERE app_name LIKE ?',
                                              (f'%{app_name}%',)).fetchall()
                app_names_list = [x[0] for x in con.execute('SELECT app_name FROM Steam').fetchall()]
                matches = difflib.get_close_matches(app_name, app_names_list, n=5, cutoff=0.4)
                if matches:
                    matches = '\n'.join(matches).title()
                    matches_string = f'Top 5 close matches for `{app_name}`:\n```\n{matches}\n```'
                    if partial_matches:
                        partial_matches_string = f'Top 5 titles containing `{app_name}`:\n```\n'
                        limit = 5 if len(partial_matches) >= 5 else len(partial_matches)
                        for i in range(limit):
                            partial_matches_string += partial_matches[i][0].title()+'\n'
                        partial_matches_string += '```\n'
                        await ctx.send(partial_matches_string + matches_string)
                    else:
                        await ctx.send(matches_string)
                else:
                    await ctx.send(f'No matches found for `{app_name}`')

    @steam.command(hidden=True)
    async def _update(self, ctx):
        await self.get_steam_apps_list_async()
        await ctx.send('Game list (probably) updated')


def setup(bot):
    bot.add_cog(SteamCog(bot))
