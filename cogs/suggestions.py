from discord.ext import commands
import sqlite3
from cogs.utils.db import add_user_to_db_or_pass
from cogs.utils.messages import update_banner
from cogs.utils.misc import check_admin_rights
from contextlib import closing


class SuggestionsCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def suggest(self, ctx, *, data):
        """Adds a game suggestion"""
        user_id = ctx.author.id
        username = str(ctx.author.name)
        game = ' '.join(data.split())
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                add_user_to_db_or_pass(con, username, user_id)
            try:
                with con:
                    con.execute('INSERT INTO Suggestions(user_id, suggestion, suggestion_type) VALUES(?, ?, ?);',
                                (user_id, game, 'game'))
                await update_banner(ctx, 'games')
                await ctx.send('{} suggested "{}" for stream'.format(username, game))
            except sqlite3.IntegrityError:
                await ctx.send('"{}" has already been suggested'.format(game))

    @commands.command(aliases=['movie_suggest'])
    async def suggest_movie(self, ctx, *, data):
        """Adds a movie suggestion"""
        user_id = ctx.author.id
        username = str(ctx.author.name)
        movie = ' '.join(data.split())
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                add_user_to_db_or_pass(con, username, user_id)
            try:
                with con:
                    con.execute('INSERT INTO Suggestions(user_id, suggestion, suggestion_type) VALUES(?, ?, ?);',
                                (user_id, movie, 'movie'))
                await update_banner(ctx, 'movies')
                await ctx.send('{} suggested "{}" for movie night'.format(username, movie))
            except sqlite3.IntegrityError:
                await ctx.send('"{}" has already been suggested'.format(movie))

    @commands.command()
    async def remove(self, ctx, *, data):
        """Removes the game suggestion if the game was suggested by the user issuing the command"""
        if await check_admin_rights(ctx):
            await self.adminremove(ctx, data)
        else:
            user_id = ctx.author.id
            username = str(ctx.author.name)
            game = ' '.join(data.split())
            with closing(sqlite3.connect(self.bot.db_name)) as con:
                with con:
                    con.execute('UPDATE OR IGNORE Users SET username=? WHERE user_id=?;', (username, user_id))
                    con.execute('INSERT OR IGNORE INTO Users(username, user_id) VALUES(?, ?);', (username, user_id))
                    exists = con.execute('SELECT * FROM Suggestions \
                                          WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                                         (user_id, game, 'game')).fetchall()
                if exists:
                    with con:
                        con.execute(
                            'DELETE FROM Suggestions WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                            (user_id, game, 'game'))
                        exists = con.execute('SELECT * FROM Suggestions \
                                              WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                                             (user_id, game, 'game')).fetchall()
                    if not exists:
                        await update_banner(ctx, 'games')
                        await ctx.send('Successfully deleted "{}" from {}\'s game suggestions'.format(game, username))
                    else:
                        await ctx.send(
                            'Couldn\'t delete "{}" from {}\'s game suggestions, please contact Euqimor for troubleshooting'.format(
                                game, username))
                else:
                    await ctx.send('"{}" not found in {}\'s game suggestions'.format(game, username))

    @commands.command(aliases=['movie_remove'])
    async def remove_movie(self, ctx, *, data):
        """Removes the movie suggestion if the movie was suggested by the user issuing the command"""
        if await check_admin_rights(ctx):
            await self.adminremove_movie(ctx, data)
        else:
            user_id = ctx.author.id
            username = str(ctx.author.name)
            movie = ' '.join(data.split())
            with closing(sqlite3.connect(self.bot.db_name)) as con:
                with con:
                    con.execute('UPDATE OR IGNORE Users SET username=? WHERE user_id=?;', (username, user_id))
                    con.execute('INSERT OR IGNORE INTO Users(username, user_id) VALUES(?, ?);', (username, user_id))
                    exists = con.execute('SELECT * FROM Suggestions \
                                          WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                                         (user_id, movie, 'movie')).fetchall()
                if exists:
                    with con:
                        con.execute(
                            'DELETE FROM Suggestions WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                            (user_id, movie, 'movie'))
                        exists = con.execute('SELECT * FROM Suggestions \
                                              WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                                             (user_id, movie, 'movie')).fetchall()
                    if not exists:
                        await update_banner(ctx, 'movies')
                        await ctx.send('Successfully deleted "{}" from {}\'s movie suggestions'.format(movie, username))
                    else:
                        await ctx.send(
                            'Couldn\'t delete "{}" from {}\'s movie suggestions, please contact Euqimor for troubleshooting'
                            .format(movie, username))
                else:
                    await ctx.send('"{}" not found in {}\'s movie suggestions'.format(movie, username))

    async def adminremove(self, ctx, data):
        """Removes the game from any user's suggestions"""
        game = ' '.join(data.split())
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                exists = con.execute('SELECT * FROM Suggestions \
                                              WHERE suggestion LIKE ? AND suggestion_type=?;',
                                     (game, 'game')).fetchall()
            if exists:
                with con:
                    con.execute('DELETE FROM Suggestions WHERE suggestion LIKE ? AND suggestion_type=?;',
                                (game, 'game'))
                    exists = con.execute('SELECT * FROM Suggestions \
                                                  WHERE suggestion LIKE ? AND suggestion_type=?;',
                                         (game, 'game')).fetchall()
                if not exists:
                    await update_banner(ctx, 'games')
                    await ctx.send('Successfully deleted "{}" from game suggestions'.format(game))
                else:
                    await ctx.send(
                        'Couldn\'t delete "{}" from game suggestions, please contact Euqimor for troubleshooting'
                        .format(game))
            else:
                await ctx.send('"{}" not found in game suggestions'.format(game))

    async def adminremove_movie(self, ctx, data):
        """Removes the movie from any user's suggestions"""
        movie = ' '.join(data.split())
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                exists = con.execute('SELECT * FROM Suggestions \
                                      WHERE suggestion LIKE ? AND suggestion_type=?;',
                                     (movie, 'movie')).fetchall()
            if exists:
                with con:
                    con.execute('DELETE FROM Suggestions WHERE suggestion LIKE ? AND suggestion_type=?;',
                                (movie, 'movie'))
                    exists = con.execute('SELECT * FROM Suggestions \
                                          WHERE suggestion LIKE ? AND suggestion_type=?;',
                                         (movie, 'movie')).fetchall()
                if not exists:
                    await update_banner(ctx, 'movies')
                    await ctx.send('Successfully deleted "{}" from movie suggestions'.format(movie))
                else:
                    await ctx.send(
                        'Couldn\'t delete "{}" from movie suggestions, please contact Euqimor for troubleshooting'
                        .format(movie))
            else:
                await ctx.send('"{}" not found in movie suggestions'.format(movie))


def setup(bot):
    bot.add_cog(SuggestionsCog(bot))
