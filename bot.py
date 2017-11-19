import discord
from discord.ext import commands
import dict_query
import random
import sqlite3
import os
import sys
from time import sleep
from collections import defaultdict
from contextlib import closing
from urllib.request import pathname2url

# TODO MAKE EXISTS CHECK A SEPARATE FUNCTION!!!
# TODO PROVIDE HELP INSTRUCTIONS, separate commands into groups, add multi-server support(?)
# TODO 2000 symbols limit for suggestions list


description = '''An awkward attempt at making a discord bot'''
bot = commands.Bot(command_prefix='$', description=description)
db_name = 'cube.db'


def check_database(db_name):
    path = os.path.realpath(db_name)
    db_uri = 'file:{}?mode=rw'.format(pathname2url(path))
    con = None
    try:
        con = sqlite3.connect(db_uri, uri=True)
        print('Database connection test successful: {}'.format(path))
        return True
    except sqlite3.OperationalError:
        print('Database not found: {}\nAttempting to create a new database'.format(path))
        try:
            con = sqlite3.connect(db_name)
            commands = [
                'CREATE TABLE Users(user_id INT PRIMARY KEY, username TEXT);',
                'CREATE TABLE Suggestions (id INTEGER PRIMARY KEY, user_id INT, suggestion TEXT, suggestion_type TEXT,\
                 FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE,\
                 UNIQUE (suggestion COLLATE NOCASE, suggestion_type));',
            ]
            for command in commands:
                con.execute(command)
            print('New database created: {}'.format(path))
            return True
        except sqlite3.Error as e:
            print('Database creation failed: {}'.format(e))
    finally:
        if con:
            con.close()
        else:
            return False




@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name='with turrets'))


async def check_admin_rights(ctx):
    try:
        roles = ctx.author.roles
    except AttributeError:
        await ctx.send('Something went wrong. If you tried this command in a DM, the bot '
                       'doesn\'t know how to check if you have admin rights.')
        return None
    success_flag = 0
    for role in roles:
        if role.permissions.administrator:
            success_flag = 1
    if ctx.author.id == 173747843314483210:
        success_flag = 1
    return bool(success_flag)


@bot.command()
async def suggest(ctx, *, data):
    """Adds a game suggestion"""
    user_id = ctx.author.id
    username = str(ctx.author.name)
    game = ' '.join(data.split())
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            con.execute('UPDATE OR IGNORE Users SET username=? WHERE user_id=?;',(username, user_id))
            con.execute('INSERT OR IGNORE INTO Users(username, user_id) VALUES(?, ?);',(username, user_id))
        try:
            with con:
                con.execute('INSERT INTO Suggestions(user_id, suggestion, suggestion_type) VALUES(?, ?, ?);',(user_id, game, 'game'))
            await update_banner('games')
            await ctx.send('{} suggested {} for stream'.format(username, game))
        except sqlite3.IntegrityError:
            await ctx.send('{} has already been suggested'.format(game))


@bot.command(aliases=['movie'])
async def suggest_movie(ctx, *, data):
    """Adds a movie suggestion"""
    user_id = ctx.author.id
    username = str(ctx.author.name)
    movie = ' '.join(data.split())
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            con.execute('UPDATE OR IGNORE Users SET username=? WHERE user_id=?;',(username, user_id))
            con.execute('INSERT OR IGNORE INTO Users(username, user_id) VALUES(?, ?);',(username, user_id))
        try:
            with con:
                con.execute('INSERT INTO Suggestions(user_id, suggestion, suggestion_type) VALUES(?, ?, ?);',(user_id, movie, 'movie'))
            await update_banner('movies')
            await ctx.send('{} suggested {} for movie night'.format(username, movie))
        except sqlite3.IntegrityError:
            await ctx.send('{} has already been suggested'.format(movie))


@bot.command()
async def remove(ctx, *, data):
    """Removes the game suggestion if the game was suggested by the user issuing the command"""
    user_id = ctx.author.id
    username = str(ctx.author.name)
    game = ' '.join(data.split())
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            con.execute('UPDATE OR IGNORE Users SET username=? WHERE user_id=?;',(username, user_id))
            con.execute('INSERT OR IGNORE INTO Users(username, user_id) VALUES(?, ?);',(username, user_id))
            exists = con.execute('SELECT * FROM Suggestions \
                                  WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                                 (user_id, game, 'game')).fetchall()
        if exists:
            with con:
                con.execute('DELETE FROM Suggestions WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',(user_id, game, 'game'))
                exists = con.execute('SELECT * FROM Suggestions \
                                      WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                                     (user_id, game, 'game')).fetchall()
            if not exists:
                await update_banner('games')
                await ctx.send('Successfully deleted {} from {}\'s game suggestions'.format(username, game))
            else:
                await ctx.send('Couldn\'t delete {} from {}\'s game suggestions, please contact Euqimor for troubleshooting'.format(username, game))
        else:
            await ctx.send('{} not found in {}\'s game suggestions'.format(username, game))


@bot.command(aliases=['movie_remove'])
async def remove_movie(ctx, *, data):
    """Removes the movie suggestion if the movie was suggested by the user issuing the command"""
    user_id = ctx.author.id
    username = str(ctx.author.name)
    movie = ' '.join(data.split())
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            con.execute('UPDATE OR IGNORE Users SET username=? WHERE user_id=?;',(username, user_id))
            con.execute('INSERT OR IGNORE INTO Users(username, user_id) VALUES(?, ?);',(username, user_id))
            exists = con.execute('SELECT * FROM Suggestions \
                                  WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                                 (user_id, movie, 'movie')).fetchall()
        if exists:
            with con:
                con.execute('DELETE FROM Suggestions WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',(user_id, movie, 'movie'))
                exists = con.execute('SELECT * FROM Suggestions \
                                      WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                                     (user_id, movie, 'movie')).fetchall()
            if not exists:
                await update_banner('movies')
                await ctx.send('Successfully deleted {} from {}\'s movie suggestions'.format(username, movie))
            else:
                await ctx.send('Couldn\'t delete {} from {}\'s movie suggestions, please contact Euqimor for troubleshooting'.format(username, movie))
        else:
            await ctx.send('{} not found in {}\'s movie suggestions'.format(username, movie))


@bot.command(aliases=['admin_remove'])
async def adminremove(ctx, *, data):
    """Removes the game from suggestions, command available only to Admin role"""
    game = ' '.join(data.split())
    if await check_admin_rights(ctx):
        with closing(sqlite3.connect(db_name)) as con:
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
                    await update_banner('games')
                    await ctx.send('Successfully deleted {} from game suggestions'.format(game))
                else:
                    await ctx.send('Couldn\'t delete {} from game suggestions, please contact Euqimor for troubleshooting'
                                   .format(game))
            else:
                await ctx.send('{} not found in suggestions'.format(game))
    else:
        await ctx.send(random.choice(rejections))


@bot.command(aliases=['movie_adminremove, adminremove_movie, admin_remove_movie'])
async def adminremove_movie(ctx, *, data):
    """Removes the movie from suggestions, command available only to Admin role"""
    movie = ' '.join(data.split())
    if await check_admin_rights(ctx):
        with closing(sqlite3.connect(db_name)) as con:
            with con:
                exists = con.execute('SELECT * FROM Suggestions \
                                      WHERE suggestion LIKE ? AND suggestion_type=?;',
                                     (movie, 'movie')).fetchall()
            if exists:
                with con:
                    con.execute('DELETE FROM Suggestions WHERE suggestion LIKE ? AND suggestion_type=?;',(movie, 'movie'))
                    exists = con.execute('SELECT * FROM Suggestions \
                                          WHERE suggestion LIKE ? AND suggestion_type=?;',
                                         (movie, 'movie')).fetchall()
                if not exists:
                    await update_banner('movies')
                    await ctx.send('Successfully deleted {} from movie suggestions'.format(movie))
                else:
                    await ctx.send(
                        'Couldn\'t delete {} from movie suggestions, please contact Euqimor for troubleshooting'
                        .format(movie))
            else:
                await ctx.send('{} not found in suggestions'.format(movie))
    else:
        await ctx.send(random.choice(rejections))


@bot.command()
async def wipe_games(ctx):
    """Purges the game suggestions list, command available only to Admin role"""
    if await check_admin_rights(ctx):
        with closing(sqlite3.connect(db_name)) as con:
            with con:
                exists = con.execute('SELECT * FROM Suggestions WHERE suggestion_type=? LIMIT 1;', ('game',)).fetchall()
            if exists:
                with con:
                    con.execute('DELETE FROM Suggestions WHERE suggestion_type=?;',('game',))
                    exists = con.execute('SELECT * FROM Suggestions WHERE suggestion_type=? LIMIT 1;',('game',)).fetchall()
                if not exists:
                    await update_banner('games')
                    await ctx.send('Successfully deleted all the game suggestions')
                else:
                    await ctx.send('Couldn\'t delete the game suggestions, please contact Euqimor for troubleshooting')
            else:
                await ctx.send('No game suggestions found')
    else:
        await ctx.send(random.choice(rejections))


@bot.command()
async def wipe_movies(ctx):
    """Purges the movie suggestions list, command available only to Admin role"""
    if await check_admin_rights(ctx):
        with closing(sqlite3.connect(db_name)) as con:
            with con:
                exists = con.execute('SELECT * FROM Suggestions WHERE suggestion_type=? LIMIT 1;',('movie',)).fetchall()
            if exists:
                with con:
                    con.execute('DELETE FROM Suggestions WHERE suggestion_type=?;',('movie',))
                    exists = con.execute('SELECT * FROM Suggestions WHERE suggestion_type=? LIMIT 1;',('movie',)).fetchall()
                if not exists:
                    await update_banner('movies')
                    await ctx.send('Successfully deleted all the movie suggestions')
                else:
                    await ctx.send('Couldn\'t delete the movie suggestions, please contact Euqimor for troubleshooting')
            else:
                await ctx.send('No movie suggestions found')
    else:
        await ctx.send(random.choice(rejections))


@bot.command()
async def wipe_user(ctx, user_id:str):
    """Purges the user and all related content from the database, command available only to Admin role"""
    if await check_admin_rights(ctx):
        user_id = user_id.strip('<@>')
        with closing(sqlite3.connect(db_name)) as con:
            with con:
                exists = con.execute('SELECT username FROM Users WHERE user_id=? LIMIT 1;',(user_id,)).fetchall()
            if exists:
                username = exists[0]
                with con:
                    con.execute('PRAGMA FOREIGN_KEYS=ON;')
                    con.execute('DELETE FROM Users WHERE user_id=?;',(user_id,))
                    exists = con.execute('SELECT username FROM Users WHERE user_id=? LIMIT 1;', (user_id,)).fetchall()
                if not exists:
                    await update_banner('movies')
                    await update_banner('games')
                    await ctx.send('Successfully deleted user {} from the database'.format(username))
                else:
                    await ctx.send('Couldn\'t delete the user, please contact Euqimor for troubleshooting')
            else:
                await ctx.send('User not found in the database')
    else:
        await ctx.send(random.choice(rejections))


def message_games_by_author():
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            suggestions = con.execute('SELECT username, suggestion \
                                        FROM Users NATURAL JOIN \
                                        (SELECT * FROM Suggestions WHERE suggestion_type=="game") Q;').fetchall()
        if suggestions:
            message = '__**SUGGESTIONS BY AUTHOR**__\n\n'
            suggestions_dict = defaultdict(list)
            for username, game in suggestions:
                suggestions_dict[username].append(game)
            for username in suggestions_dict:
                message += '**{}:**\n```'.format(username)
                for game in suggestions_dict[username]:
                    message += '\n{}'.format(game)
                message += '```'
        else:
            message = '__**SUGGESTIONS BY AUTHOR**__\n\nNothing has been suggested yet'
        return message


def message_suggestions_in_category(suggestion_type: str):
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            suggestions = con.execute('SELECT suggestion FROM Suggestions WHERE suggestion_type==?;',(suggestion_type,)).fetchall()
        if suggestions:
            message = '__**SUGGESTED {}**__\n```\n'.format(suggestion_type.upper())
            for entry in suggestions:
                message += '\n{}'.format(entry[0])
            message += '```'
        else:
            message = '__**SUGGESTED {}**__\n\nNothing has been suggested yet'.format(suggestion_type.upper())
        return message


@bot.command()
async def games_full(ctx):
    """Prints games suggested so far grouped by suggestion author's name"""
    message = message_games_by_author()
    await ctx.send(message)


@bot.command()
async def games_list(ctx):
    """Prints games suggested so far in one list"""
    message = message_suggestions_in_category('game')
    await ctx.send(message)


@bot.command(aliases=['miriam', 'Miriam', 'MIRIAM', 'GODDAMITMIRIAM', 'word', 'mw', 'Merriam', 'dict'])
async def merriam(ctx, *, word: str):
    """Queries Merriam-Webster's Collegiate Dictionary for a word definition. Well, tries to at least..."""
    word = ' '.join(word.split())
    # try:
    query_result = dict_query.query_merriam(word, os.environ['MERRIAM'])
    cases = query_result  # the word may have changed if you queried for the past tense for example
    # except:
    #     await ctx.send('Something went wrong during online query')
    # try:
    phrase = dict_query.parse_merriam(cases)
    # except:
    #     await ctx.send('Something went wrong during result parsing')
    if phrase != '' and phrase is not None:
        if len(phrase) >= 2000:
            message_list = dict_query.split_message(phrase)
            # for message in message_list:
            await ctx.send(message_list[0])
            await ctx.send('\_'*20+'\nRead more: '+'https://www.merriam-webster.com/dictionary/'+'%20'.join(word.split(' ')))
        else:
            await ctx.send(phrase)
    else:
        message = await ctx.send('Could not find the word or something went wrong with the request')
        sleep(4)
        await message.delete()


@bot.command(hidden=True)
async def say(ctx, channel_id: str, *, message_text):
    if ctx.author.id in [173747843314483210, 270744594243649536]:
        if isinstance(ctx.channel, discord.TextChannel):
            try:
                await ctx.message.delete()
            except:  # TODO find the proper name for the permissions exception
                pass
        if '#' not in channel_id:
            dest_channel = bot.get_channel(int(channel_id))
            await dest_channel.send(message_text)
        else:
            channel_id = channel_id.strip('<#>')
            dest_channel = bot.get_channel(int(channel_id))
            await dest_channel.send(message_text)
    else:
        await ctx.send(random.choice(rejections))


async def update_banner(banner_type):

    def suggestions_exist(suggestion_type):
        with closing(sqlite3.connect(db_name)) as con:
            with con:
                if con.execute('SELECT * FROM Suggestions WHERE suggestion_type=? LIMIT 1;', (suggestion_type,)).fetchall():
                    return True
        return False

    guild = bot.guilds[0]
    channel = [x for x in guild.text_channels if x.name == 'game_suggestions_bot'][0]
    message_list = []
    async for message in channel.history(limit=100):
        if message.author.id == bot.user.id:
            message_list.append(message)
    if message_list:
        if banner_type == 'games' and suggestions_exist('game'):
            await message_list[2].edit(content=message_suggestions_in_category('game'))
            await message_list[1].edit(content=message_games_by_author())
        elif banner_type == 'movies' and suggestions_exist('movie'):
            await message_list[0].edit(content=message_suggestions_in_category('movie'))
        else:
            for message in message_list:
                message.delete()
    else:
        if suggestions_exist('game') or suggestions_exist('movie'):
            await channel.send(message_suggestions_in_category('game'))
            await channel.send(message_games_by_author())
            await channel.send(message_suggestions_in_category('movie'))


@bot.command()
async def set_prefix(ctx, message: str):  # TODO save permanently
    prefix = message.strip()
    if await check_admin_rights(ctx):
        bot.command_prefix = prefix
        await ctx.send('The prefix is set to '+str(bot.command_prefix))
    else:
        await ctx.send(random.choice(rejections))


@bot.command(aliases=['set_nickname'])
async def set_nick(ctx, *, message: str = ''):
    nickname = message.strip()
    if await check_admin_rights(ctx):
        bot_member = [x for x in bot.get_all_members() if x.bot and x.id == bot.user.id][0]
        await bot_member.edit(nick=nickname)
        await ctx.send('Nickname set')
    else:
        await ctx.send(random.choice(rejections))


@bot.command(aliases=['set_playing'])
async def set_status(ctx, *, message: str = ''):  # TODO save permanently?
    status = message.strip()
    if await check_admin_rights(ctx):
        await bot.change_presence(game=discord.Game(name=status))
        await ctx.send('Status set')
    else:
        await ctx.send(random.choice(rejections))


if __name__ == '__main__':
    rejections = ['Nope', 'Nu-uh', 'You are not my supervisor!', 'Sorry, you are not important enough to do that -_-',
                  'Stop trying that, or I\'ll report you to Nightmom!', 'Yeah, right.']
    if check_database(db_name):
        bot.run(os.environ['BOT_KEY'])
    else:
        sys.exit(1)