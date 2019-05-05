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
                    app_name = app["name"].lower()
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
                    app_name = app["name"].lower()
                    con.execute(f'INSERT OR IGNORE INTO Steam (app_id, app_name) VALUES (?, ?);', (app_id, app_name))

    @commands.group(invoke_without_command=True)
    async def steam(self, ctx, *, app_name=''):
        if app_name == '':
            await ctx.send('Please provide name to search for')
        app_name = app_name.strip().lower()
        if app_name[0] == '\"':
            app_name = app_name.strip('"')
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                result = con.execute('SELECT app_id FROM Steam WHERE app_name=?', (app_name,)).fetchone()
                if result:
                    app_id = result[0]
                    await ctx.send(f'https://store.steampowered.com/app/{app_id}/')
                else:  # if game not found, update games list from Steam
                    await self.get_steam_apps_list_async()
                    result = con.execute('SELECT app_id FROM Steam WHERE app_name=?', (app_name,)).fetchone()
                    if result:
                        app_id = result[0]
                        await ctx.send(f'https://store.steampowered.com/app/{app_id}/')
                    else:  # if still not found, search for relevant names
                        app_names_list = [x[0] for x in con.execute('SELECT app_name FROM Steam').fetchall()]
                        matches = difflib.get_close_matches(app_name, app_names_list, cutoff=0.4, )
                        if matches:
                            matches = '\n'.join(matches)
                            await ctx.send(f'Game `{app_name}` not found, did you mean:\n```\n{matches}\n```')
                        else:
                            await ctx.send(f'Game "{app_name}" not found')


def setup(bot):
    bot.add_cog(SteamCog(bot))
