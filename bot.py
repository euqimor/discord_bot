import discord
from discord.ext import commands
import dict_query
from time import sleep
import random

# TODO PROVIDE HELP INSTRUCTIONS, separate commands into groups, add multi-server support(?)
# TODO 2000 symbols limit for suggestions list

description = '''An awkward attempt at making a discord bot'''
bot = commands.Bot(command_prefix='$', description=description)


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


def load_suggestions():
    """
    :return: tries to load a dict of suggestions from a file,
    otherwise returns empty dict
    """
    suggestions = load_data_from_file('suggestions')
    if not suggestions:
        suggestions = {}
    return suggestions


def save_data_to_file(data, filename):
    """
    :param data: data to be stored into a file
    :param filename: filename to save data to
    :return: None, saves dict as a file for future usage
    """
    with open(filename, 'w') as file:
        file.write(str(data))


def load_data_from_file(filename):
    """
    :param filename: file from which to load the data
    :return: returns eval() of the file contents
    """
    try:
        with open(filename) as file:
            data = eval(file.read())
        return data
    except FileNotFoundError:
        print('File not found')
    except:
        print('Something went wrong during data evaluation')


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name='with turrets'))


def create_games_message(suggestions):
    message = ''
    if suggestions:
        for userid in suggestions:
            if suggestions[userid]['games']:
                message += '**'+suggestions[userid]['username']+':**\n'+'```'
                for game in suggestions[userid]['games']:
                    message += '\n' + game
                message += '```'
        if message == '':
            message = '__**SUGGESTIONS BY AUTHOR**__\n\nNothing has been suggested yet'
        else:
            message = '__**SUGGESTIONS BY AUTHOR**__\n\n' + message
    else:
        message = '__**SUGGESTIONS BY AUTHOR**__\n\nNothing has been suggested yet'
    return message


@bot.command()
async def games_full(ctx):
    """Prints games suggested so far grouped by suggestion author's name"""
    message = create_games_message(suggestions)
    await ctx.send(message)


# def create_list_message(suggestions):
#     if suggestions:
#         set_of_games = set({})
#         message = '__**SUGGESTED GAMES**__\n```\n'
#         for userid in suggestions:
#             for game in suggestions[userid]['games']:
#                 if game.lower() not in [x.lower() for x in set_of_games]:
#                     set_of_games.add(game)
#         for game in set_of_games:
#             message += '\n' + game
#         message += '```'
#     else:
#         message = 'Nothing has been suggested yet'
#     return message


def create_item_list_message(suggestions, entry_name: str):
    if suggestions:
        set_of_items = set({})
        for userid in suggestions:
            if suggestions[userid][entry_name]:
                for item in suggestions[userid][entry_name]:
                    if item.lower() not in [x.lower() for x in set_of_items]:
                        set_of_items.add(item)
        if set_of_items:
            message = '__**SUGGESTED {}**__\n```\n'.format(entry_name.upper())
            for item in set_of_items:
                message += '\n' + item
            message += '```'
        else:
            message = '__**SUGGESTED {}**__\n```\nNothing has been suggested yet'.format(entry_name.upper())
    else:
        message = '__**SUGGESTED {}**__\n```\nNothing has been suggested yet'.format(entry_name.upper())
    return message


@bot.command()
async def games_list(ctx):
    """Prints games suggested so far in one list"""
    message = create_item_list_message(suggestions, 'games')
    await ctx.send(message)


@bot.command()
async def suggest(ctx, *, data):
    """Adds a game suggestion"""
    userid = ctx.author.id
    name = str(ctx.author.name)
    game = ' '.join(data.split())
    already_suggested = 0
    if userid in suggestions:
        if game.lower() not in [x.lower() for x in suggestions[userid]['games']]:
            suggestions[userid]['games'].add(game)
        else:
            already_suggested = 1
        if suggestions[userid]['username'] != name:
            suggestions[userid]['username'] = name
    else:
        suggestions[userid] = {}
        suggestions[userid]['username'] = name
        suggestions[userid]['games'] = {game}
    save_data_to_file(suggestions, 'suggestions')
    if already_suggested:
        await ctx.send('{} is in your game suggestions already'.format(game))
    else:
        await update_banner('games')
        await ctx.send('{} suggested {} for stream'.format(name, game))


@bot.command(aliases=['movie'])
async def suggest_movie(ctx, *, data):
    """Adds a game suggestion"""
    userid = ctx.author.id
    name = str(ctx.author.name)
    movie = ' '.join(data.split())
    already_suggested = 0
    if userid in suggestions:
        if movie.lower() not in [x.lower() for x in suggestions[userid]['movies']]:
            suggestions[userid]['movies'].add(movie)
        else:
            already_suggested = 1
        if suggestions[userid]['username'] != name:
            suggestions[userid]['username'] = name
    else:
        suggestions[userid] = {}
        suggestions[userid]['username'] = name
        suggestions[userid]['movies'] = {movie}
    save_data_to_file(suggestions, 'suggestions')
    if already_suggested:
        await ctx.send('{} is in your movie suggestions already'.format(movie))
    else:
        await update_banner('movies')
        await ctx.send('{} suggested {} for movie night'.format(name, movie))


@bot.command()
async def remove(ctx, *, data):
    """Removes the game suggestion if the game was suggested by the user issuing the command"""
    userid = ctx.author.id
    name = str(ctx.author.name)
    game = ' '.join(data.split())
    success_flag = 0
    game_found = ('', 0)
    if userid in suggestions:
        for existing_game in suggestions[userid]['games']:
            if game.lower() == existing_game.lower():
                game_found = (existing_game, 1)
                break
        if game_found[1]:
            suggestions[userid]['games'].remove(game_found[0])
            save_data_to_file(suggestions, 'suggestions')
            await update_banner('games')
            success_flag = 1
    if success_flag:
        await ctx.send('Successfully deleted '+game+' from '+name+'\'s game suggestions')
    elif not game_found[1]:
        await ctx.send('\"'+game+'\" not found in '+name+'\'s game suggestions')
    else:
        await ctx.send('Something went wrong')


@bot.command(aliases=['movie_remove'])
async def remove_movie(ctx, *, data):
    """Removes the movie suggestion if the movie was suggested by the user issuing the command"""
    userid = ctx.author.id
    name = str(ctx.author.name)
    movie = ' '.join(data.split())
    success_flag = 0
    movie_found = ('', 0)
    if userid in suggestions:
        for existing_movie in suggestions[userid]['movies']:
            if movie.lower() == existing_movie.lower():
                movie_found = (existing_movie, 1)
                break
        if movie_found[1]:
            suggestions[userid]['movies'].remove(movie_found[0])
            save_data_to_file(suggestions, 'suggestions')
            await update_banner('movies')
            success_flag = 1
    if success_flag:
        await ctx.send('Successfully deleted '+movie+' from '+name+'\'s movie suggestions')
    elif not movie_found[1]:
        await ctx.send('\"'+movie+'\" not found in '+name+'\'s movie suggestions')
    else:
        await ctx.send('Something went wrong')


@bot.command()
async def adminremove(ctx, *, data):
    """Removes the game from every list, command only available to Admin role"""
    game = ' '.join(data.split())
    global suggestions
    if await check_admin_rights(ctx):
        entries_to_delete = []
        for userid in suggestions:
            for existing_game in suggestions[userid]['games']:
                if game.lower() == existing_game.lower():
                    entries_to_delete.append({'userid':userid, 'game':existing_game})
        if entries_to_delete:
            for entry in entries_to_delete:
                suggestions[entry['userid']]['games'].remove(entry['game'])
            save_data_to_file(suggestions, 'suggestions')
            await update_banner('games')
            await ctx.send('Successfully deleted ' + game + ' from suggestions')
        else:
            await ctx.send('Game \"'+game+'\" not found in suggestions')
    else:
        await ctx.send(random.choice(rejections))


@bot.command(aliases=['movie_adminremove'])
async def adminremove_movie(ctx, *, data):
    """Removes the movie from every list, command only available to Admin role"""
    movie = ' '.join(data.split())
    global suggestions
    if await check_admin_rights(ctx):
        entries_to_delete = []
        for userid in suggestions:
            for existing_movie in suggestions[userid]['movies']:
                if movie.lower() == existing_movie.lower():
                    entries_to_delete.append({'userid':userid, 'movie':existing_movie})
        if entries_to_delete:
            for entry in entries_to_delete:
                suggestions[entry['userid']]['movies'].remove(entry['movie'])
            save_data_to_file(suggestions, 'suggestions')
            await update_banner('movies')
            await ctx.send('Successfully deleted ' + movie + ' from movie suggestions')
        else:
            await ctx.send('\"'+movie+'\" not found in movie suggestions')
    else:
        await ctx.send(random.choice(rejections))


@bot.command()
async def adminwipe_games(ctx):
    """Purges the game suggestions list, command only available to Admin role"""
    if await check_admin_rights(ctx):
        global suggestions
        for userid in suggestions:
            suggestions[userid]['games'] = set({})
        save_data_to_file(suggestions, 'suggestions')
        await update_banner('games')
        await ctx.send('All game suggestions successfully deleted')
    else:
        await ctx.send(random.choice(rejections))


@bot.command()
async def adminwipe_movies(ctx):
    """Purges the movie suggestions list, command only available to Admin role"""
    if await check_admin_rights(ctx):
        global suggestions
        for userid in suggestions:
            suggestions[userid]['movies'] = set({})
        save_data_to_file(suggestions, 'suggestions')
        await update_banner('movies')
        await ctx.send('All movie suggestions successfully deleted')
    else:
        await ctx.send(random.choice(rejections))


@bot.command(aliases=['miriam', 'Miriam', 'MIRIAM', 'GODDAMITMIRIAM', 'word', 'mw', 'Merriam', 'word', 'dict'])
async def merriam(ctx, *, word: str):
    """Queries Merriam-Webster's Collegiate Dictionary for a word definition. Well, tries to at least..."""
    word = ' '.join(word.split())
    # try:
    query_result = dict_query.query_merriam(word, keys['merriam_webster'])
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
            except:
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


# async def update_games_banner(ctx):
#     guild = bot.guilds[0]  # TODO think about fixing this. Or don't... Remember that right now ctx is not used
#     channel = [x for x in guild.text_channels if x.name == 'game_suggestions_bot'][0]
#     message_list = []
#     async for message in channel.history(limit=100):
#         if message.author.id == bot.user.id:
#             message_list.append(message)
#     if message_list:
#         if suggestions:
#             await message_list[0].edit(content=create_games_message(suggestions))
#             await message_list[1].edit(content=create_item_list_message(suggestions, 'games'))
#         else:
#             await message_list[0].delete()
#             await message_list[1].delete()
#     else:
#         if suggestions:
#             await channel.send(create_item_list_message(suggestions, 'games'))
#             await channel.send(create_games_message(suggestions))


async def update_banner(banner_type):
    guild = bot.guilds[0]
    channel = [x for x in guild.text_channels if x.name == 'game_suggestions_bot'][0]
    message_list = []
    async for message in channel.history(limit=100):
        if message.author.id == bot.user.id:
            message_list.append(message)
    if message_list:
        if suggestions:
            if banner_type == 'games':
                await message_list[2].edit(content=create_item_list_message(suggestions, 'games'))
                await message_list[1].edit(content=create_games_message(suggestions))
            elif banner_type == 'movies':
                await message_list[0].edit(content=create_item_list_message(suggestions, 'movies'))
        else:
            for message in message_list:
                message.delete()
    else:
        if suggestions:
            await channel.send(create_item_list_message(suggestions, 'games'))
            await channel.send(create_games_message(suggestions))
            await channel.send(create_item_list_message(suggestions, 'movies'))


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
    keys = load_data_from_file('keys')
    rejections = ['Nope', 'Nu-uh', 'You are not my supervisor!', 'Sorry, you are not important enough to do that -_-',
                  'Stop trying that, or I\'ll report you to Nightmom!', 'Yeah, right.']
    suggestions = load_suggestions()
    bot.run(keys['bot'])
