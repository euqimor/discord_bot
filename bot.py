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
from db_helpers import *


# TODO Fix the bug where removing the last suggestion deletes it from the DB, but leaves hanging in the channel
# TODO Sort output list by id

# TODO MAKE EXISTS CHECK A SEPARATE FUNCTION!!!
# TODO PROVIDE HELP INSTRUCTIONS, separate commands into groups, add multi-server support(?)
# TODO 2000 symbols limit for suggestions list


description = '''An awkward attempt at making a discord bot'''
bot = commands.Bot(command_prefix='$', description=description)
db_name = 'cube.db'


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game('with turrets'))


# UNIMPLEMENTED UNTIL THE BUG GETS FIXED
# @bot.event
# async def on_member_update(before, after):
#     guild = before.guild
#     channel = [x for x in guild.text_channels if x.name == 'secluded_cave'][0]
#     role = [x for x in guild.roles if x.name == 'Live Queue'][0]
#     if after.id == 173747843314483210:
#         if after.activity:
#             await channel.send(after.activity.type)
#         else:
#             await channel.send(str(after.activity))
#     # if after.activity and after.id == 173747843314483210 and after.activity.type is discord.enums.ActivityType.streaming:
#     #     await channel.send(after.activity.type)
#     #     await channel.send('attempting to add roles')
#     #     await after.add_roles(role)
#     # if before.activity and after.id == 173747843314483210 and before.activity.type is discord.enums.ActivityType.streaming and after.activity.type != before.activity.type:
#     #     await channel.send('attempting to remove roles')
#     #     await after.remove_roles(role)


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
                'CREATE TABLE Proverbs(proverb TEXT);',
                'CREATE TABLE Tags (id INTEGER PRIMARY KEY, user_id INT, tag_name TEXT, tag_content TEXT,\
                 UNIQUE (tag_name COLLATE NOCASE));',
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


@bot.group(invoke_without_command=True)
async def tag(ctx, *, tag_name=''):
    """
    Retrieves tag by name
    Usage example: `tag mytag` will fetch `mytag` from saved tags
    """
    if tag_name == '':
        await ctx.send('Tag name required')
    else:
        tag_name = tag_name.strip()
        if tag_name[0] == '\"':
            tag_name = tag_name.strip('"')
        with closing(sqlite3.connect(db_name)) as con:
            with con:
                line = con.execute('SELECT tag_content FROM Tags WHERE tag_name=?', (tag_name,)).fetchone()
        if line:
            line = line[0]
            await ctx.send(line)
        else:
            await ctx.send('Tag "{}" not found'.format(tag_name))


@tag.command()
async def add(ctx, *, content=''):
    """
    Add a tag
    Usage example: `tag add tagname your text here` or `tag add \"long tag name\" your text here`
    If the name is more than one word long, put it in quotes, otherwise only the first word will be used as a name
    No quotes are needed for the rest of the text
    """
    if not content or len(content.split())==1:
        await ctx.send('Tag content cannot be empty')
        return
    elif content[0] != '\"':
        tag_name = content.split()[0]
        tag_content = content[len(tag_name):].strip()
    else:
        tag_name = content.split('" ')[0][1:]
        tag_content = content[len(tag_name)+2:].strip()
    user_id = ctx.author.id
    username = str(ctx.author.name)
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            add_user_to_db_or_pass(con, username, user_id)
        try:
            with con:
                con.execute('INSERT INTO Tags(user_id, tag_name, tag_content) VALUES(?, ?, ?);',(user_id, tag_name, tag_content))
            await ctx.send('Successfully added "{}" to {}\'s tags'.format(tag_name, username))
        except sqlite3.IntegrityError:
            await ctx.send('Failed to add tag "{}", name already exists'.format(tag_name))


@tag.command()
async def delete(ctx, *, tag_name=''):
    """
    Delete a tag (admin or owner only)
    Usage example: `tag remove tagname`
    """
    if tag_name == '':
        await ctx.send('Tag name required')
    else:
        tag_name = tag_name.strip()
        if tag_name[0] == '\"':
            tag_name = tag_name.strip('"')
        with closing(sqlite3.connect(db_name)) as con:
            with con:
                result = con.execute('SELECT ROWID, user_id FROM Tags WHERE tag_name=?', (tag_name,)).fetchone()
                if result:
                    tag_id, owner_id = result[0], result[1]
                    if tag_id == ctx.author.id or await check_admin_rights(ctx):
                        con.execute('DELETE FROM Tags WHERE ROWID=?;', (tag_id,))
                        await ctx.send('Successfully deleted tag "{}"'.format(tag_name))
                    else:
                        await ctx.send('You are not this tag\'s owner or admin, {}, stop ruckusing!'.format(ctx.author.name))
                else:
                    await ctx.send('Tag "{}" not found'.format(tag_name))


@bot.group(invoke_without_command=True)
async def wisdom(ctx, *, word_or_phrase=''):
    """
    Inspirational words of wisdom
    Add one or more words after the command to try and search for a proverb with the given word or phrase
    Get a random proverb if the words weren't provided or found
    """
    line = ''
    with closing(sqlite3.connect(db_name)) as con:
        if word_or_phrase:
            word_or_phrase = '%{}%'.format(word_or_phrase.strip())
            with con:
                line = con.execute('SELECT proverb FROM Proverbs WHERE proverb LIKE ?', (word_or_phrase,)).fetchone()
        if line:
            line = line[0]
        else:
            with con:
                max_id = con.execute('SELECT MAX(ROWID) FROM Proverbs;').fetchone()[0]
                id = random.randint(1, max_id)
                line = con.execute('SELECT proverb FROM Proverbs WHERE ROWID=?', (id,)).fetchone()[0]
    emoji = ''
    try:
        for item in ctx.guild.emojis:
            if item.name == 'praisegold' or item.name == 'praise_golden':
                emoji = item
                break
    except:
        pass
    await ctx.send('{} {}'.format(line, emoji))


@wisdom.command()
async def use(ctx, *, word_or_phrase=''):
    """
    Replaces "The Dark Souls" with supplied word or phrase
    """
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            max_id = con.execute('SELECT MAX(ROWID) FROM Proverbs;').fetchone()[0]
            id = random.randint(1, max_id)
            line = con.execute('SELECT proverb FROM Proverbs WHERE ROWID=?', (id,)).fetchone()[0]
    line = line.replace('The Dark Souls', word_or_phrase)
    emoji = ''
    try:
        roll = random.randint(1, 100)
        if roll <= 20:
            for item in ctx.guild.emojis:
                if item.name == 'praisegold' or item.name == 'praise_golden':
                    emoji = item
                    break
        elif 20 < roll <= 60:
            for item in ctx.guild.emojis:
                if item.name == 'thonk':
                    emoji = item
                    break
        else:
            roll_emoji = random.randint(0, len(ctx.guild.emojis))
            emoji = ctx.guild.emojis[roll_emoji]
    except:
        pass
    await ctx.send('{} {}'.format(line, emoji))


@bot.command()
async def suggest(ctx, *, data):
    """Adds a game suggestion"""
    user_id = ctx.author.id
    username = str(ctx.author.name)
    game = ' '.join(data.split())
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            add_user_to_db_or_pass(con, username, user_id)
        try:
            with con:
                con.execute('INSERT INTO Suggestions(user_id, suggestion, suggestion_type) VALUES(?, ?, ?);',(user_id, game, 'game'))
            await update_banner(ctx, 'games')
            await ctx.send('{} suggested "{}" for stream'.format(username, game))
        except sqlite3.IntegrityError:
            await ctx.send('"{}" has already been suggested'.format(game))


@bot.command(aliases=['movie_suggest'])
async def suggest_movie(ctx, *, data):
    """Adds a movie suggestion"""
    user_id = ctx.author.id
    username = str(ctx.author.name)
    movie = ' '.join(data.split())
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            add_user_to_db_or_pass(con, username, user_id)
        try:
            with con:
                con.execute('INSERT INTO Suggestions(user_id, suggestion, suggestion_type) VALUES(?, ?, ?);',(user_id, movie, 'movie'))
            await update_banner(ctx, 'movies')
            await ctx.send('{} suggested "{}" for movie night'.format(username, movie))
        except sqlite3.IntegrityError:
            await ctx.send('"{}" has already been suggested'.format(movie))


@bot.command()
async def remove(ctx, *, data):
    """Removes the game suggestion if the game was suggested by the user issuing the command"""
    if await check_admin_rights(ctx):
        await adminremove(ctx, data)
    else:
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
                    await update_banner(ctx, 'games')
                    await ctx.send('Successfully deleted "{}" from {}\'s game suggestions'.format(game, username))
                else:
                    await ctx.send('Couldn\'t delete "{}" from {}\'s game suggestions, please contact Euqimor for troubleshooting'.format(game, username))
            else:
                await ctx.send('"{}" not found in {}\'s game suggestions'.format(game, username))


@bot.command(aliases=['movie_remove'])
async def remove_movie(ctx, *, data):
    """Removes the movie suggestion if the movie was suggested by the user issuing the command"""
    if await check_admin_rights(ctx):
        await adminremove_movie(ctx, data)
    else:
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
                    await update_banner(ctx, 'movies')
                    await ctx.send('Successfully deleted "{}" from {}\'s movie suggestions'.format(movie, username))
                else:
                    await ctx.send('Couldn\'t delete "{}" from {}\'s movie suggestions, please contact Euqimor for troubleshooting'.format(movie, username))
            else:
                await ctx.send('"{}" not found in {}\'s movie suggestions'.format(movie, username))


async def adminremove(ctx, data):
    """Removes the game from any user's suggestions"""
    game = ' '.join(data.split())
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
                await update_banner(ctx, 'games')
                await ctx.send('Successfully deleted "{}" from game suggestions'.format(game))
            else:
                await ctx.send('Couldn\'t delete "{}" from game suggestions, please contact Euqimor for troubleshooting'
                               .format(game))
        else:
            await ctx.send('"{}" not found in game suggestions'.format(game))


async def adminremove_movie(ctx, data):
    """Removes the movie from any user's suggestions"""
    movie = ' '.join(data.split())
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
                await update_banner(ctx, 'movies')
                await ctx.send('Successfully deleted "{}" from movie suggestions'.format(movie))
            else:
                await ctx.send(
                    'Couldn\'t delete "{}" from movie suggestions, please contact Euqimor for troubleshooting'
                    .format(movie))
        else:
            await ctx.send('"{}" not found in movie suggestions'.format(movie))


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
                    await update_banner(ctx, 'games')
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
                    await update_banner(ctx, 'movies')
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
                username = exists[0][0]
                with con:
                    con.execute('PRAGMA FOREIGN_KEYS=ON;')
                    con.execute('DELETE FROM Users WHERE user_id=?;',(user_id,))
                    exists = con.execute('SELECT username FROM Users WHERE user_id=? LIMIT 1;', (user_id,)).fetchall()
                if not exists:
                    await update_banner(ctx, 'movies')
                    await update_banner(ctx, 'games')
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


def embed_games_by_author():
    title = 'SUGGESTIONS BY AUTHOR'
    e = discord.Embed(colour=discord.Colour.purple(), title=title)
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            suggestions = con.execute('SELECT username, suggestion \
                                        FROM Users NATURAL JOIN \
                                        (SELECT * FROM Suggestions WHERE suggestion_type=="game") Q;').fetchall()
        if suggestions:
            suggestions_dict = defaultdict(list)
            for username, game in suggestions:
                suggestions_dict[username].append(game)
            for username in suggestions_dict:
                games = ''
                for game in suggestions_dict[username]:
                    games += '{}\n'.format(game)
                e.add_field(name=username, value=games[:-1], inline=False)
        else:
            e.add_field(name='Nothing has been suggested yet', value=':(', inline=False)
        return e


def message_suggestions_in_category(suggestion_type: str):
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            suggestions = con.execute('SELECT suggestion FROM Suggestions WHERE suggestion_type==?;',(suggestion_type,)).fetchall()
        if suggestions:
            message = '__**SUGGESTED {}S**__\n```\n'.format(suggestion_type.upper())
            for entry in suggestions:
                message += '\n{}'.format(entry[0])
            message += '```'
        else:
            message = '__**SUGGESTED {}S**__\n\nNothing has been suggested yet'.format(suggestion_type.upper())
        return message


def embed_suggestions_in_category(suggestion_type: str):
    title = 'SUGGESTED {}S'.format(suggestion_type.upper())
    e = discord.Embed(colour=discord.Colour.purple())
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            suggestions = con.execute('SELECT suggestion FROM Suggestions WHERE suggestion_type==?;',(suggestion_type,)).fetchall()
        if suggestions:
            text = ''
            for entry in suggestions:
                text += '{}\n'.format(entry[0])
            e.add_field(name=title, value=text[:-1], inline=False)
        else:
            text = 'Nothing has been suggested yet'
            e.add_field(name=title, value=text, inline=False)
        return e


@bot.command(hidden=True)
async def games_full(ctx):
    """Prints games suggested so far grouped by suggestion author's name"""
    message = message_games_by_author()
    await ctx.send(message)


@bot.command(hidden=True)
async def games_list(ctx):
    """Prints games suggested so far in one list"""
    e = embed_suggestions_in_category('game')
    author_pic_url='https://static-cdn.jtvnw.net/jtv_user_pictures/f01a051288087531-profile_image-70x70.png'
    e.set_thumbnail(url='https://cdn0.iconfinder.com/data/icons/social-network-7/50/16-128.png')
    e.set_author(name='AellaQ', url='https://www.twitch.tv/aellaq', icon_url=author_pic_url)
    await ctx.send(embed=e)


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


@bot.command()
async def oxford(ctx, *, word: str):
    """Query Oxford Dictionary for a word definition."""
    word = ' '.join(word.split())
    app_id = os.environ['OXFORD_APP_ID']
    app_key = os.environ['OXFORD_APP_KEY']
    json_data = dict_query.query_oxford(word, app_id, app_key)
    code = json_data[1]
    if code == 0:
        message = await ctx.send('Could not find the word or something went wrong with the request')
        sleep(4)
        await message.delete()
    else:
        if code == 1:  # if API returned the definition
            parsed_data = dict_query.parse_oxford(json_data[0])
        elif code == 2:  # if the word couldn't be found and we are being redirected to the closest match
            redirect_data = json_data[0]
            word = ' '.join(redirect_data['results'][0]['word'].split('_'))
            json_data = dict_query.query_oxford(word, app_id, app_key)
            parsed_data = dict_query.parse_oxford(json_data[0])
        fields = parsed_data[2]
        title = '{} | Oxford Dictionary'.format(parsed_data[0])
        e = discord.Embed(colour=discord.Colour.blurple(), title=title)
        e.url = parsed_data[1]
        for field in fields:
            e.add_field(name=field['name'], value=field['value'], inline=False)
        await ctx.send(embed=e)


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


async def update_banner(ctx, banner_type):

    def suggestions_exist(suggestion_type):
        with closing(sqlite3.connect(db_name)) as con:
            with con:
                if con.execute('SELECT * FROM Suggestions WHERE suggestion_type=? LIMIT 1;', (suggestion_type,)).fetchall():
                    return True
        return False

    guild = ctx.guild
    channel = [x for x in guild.text_channels if x.name == 'game_suggestions_bot'][0]
    message_list = []
    async for message in channel.history(limit=100):
        if message.author.id == bot.user.id:
            message_list.append(message)
    if message_list:
        if banner_type == 'games' and suggestions_exist('game'):
            e = embed_suggestions_in_category('game')
            author_pic_url='https://static-cdn.jtvnw.net/jtv_user_pictures/f01a051288087531-profile_image-70x70.png'
            e.set_thumbnail(url='https://cdn0.iconfinder.com/data/icons/social-network-7/50/16-128.png')
            e.set_author(name='AellaQ', url='https://www.twitch.tv/aellaq', icon_url=author_pic_url)
            await message_list[2].edit(embed=e)
            await message_list[1].edit(embed=embed_games_by_author())
        elif banner_type == 'movies' and suggestions_exist('movie'):
            e = embed_suggestions_in_category('movie')
            e.colour = discord.Colour.orange()
            e.set_thumbnail(url='https://lh3.googleusercontent.com/TAzWe4fpDp8T7od9EoLTj4zJLV6EJQwBZjJ4mVjyzmKNzd5mVMdLU3k8J7XvErqsg59X2i71SQ=w50-h50-e365')
            await message_list[0].edit(embed=e)
        else:
            for message in message_list:
                message.delete()
    else:
        if suggestions_exist('game') or suggestions_exist('movie'):
            e = embed_suggestions_in_category('game')
            author_pic_url = 'https://static-cdn.jtvnw.net/jtv_user_pictures/f01a051288087531-profile_image-70x70.png'
            e.set_thumbnail(url='https://cdn0.iconfinder.com/data/icons/social-network-7/50/16-128.png')
            e.set_author(name='AellaQ', url='https://www.twitch.tv/aellaq', icon_url=author_pic_url)
            await channel.send(embed=e)
            await channel.send(embed=embed_games_by_author())
            e = embed_suggestions_in_category('movie')
            e.colour = discord.Colour.orange()
            e.set_thumbnail(url='https://lh3.googleusercontent.com/TAzWe4fpDp8T7od9EoLTj4zJLV6EJQwBZjJ4mVjyzmKNzd5mVMdLU3k8J7XvErqsg59X2i71SQ=w50-h50-e365')
            await channel.send(embed=e)


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
        await bot.change_presence(activity=discord.Game(status))
        await ctx.send('Status set')
    else:
        await ctx.send(random.choice(rejections))


@bot.command(hidden=True)
async def wipe_banners(ctx):
    if await bot.is_owner(ctx.author):
        guild = ctx.guild
        channel = [x for x in guild.text_channels if x.name == 'game_suggestions_bot'][0]
        message_list = []
        async for message in channel.history(limit=100):
            if message.author.id == bot.user.id:
                message_list.append(message)
        if message_list:
            for message in message_list:
                await message.delete()
    else:
        await ctx.send(random.choice(rejections))


if __name__ == '__main__':
    rejections = ['Nope', 'Nu-uh', 'You are not my supervisor!', 'Sorry, you are not important enough to do that -_-',
                  'Stop trying that, or I\'ll report you to Nightmom!', 'Yeah, right.']
    if check_database(db_name):
        bot.run(os.environ['BOT_PROD'])
    else:
        sys.exit(1)