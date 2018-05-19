import discord
from discord.ext import commands
from sys import exit
from os import environ
from cogs.utils.db import check_database
from cogs.utils.misc import add_role_to_streamers


# TODO Fix the bug where removing the last suggestion deletes it from the DB, but leaves hanging in the channel
# TODO Sort output list by id

# TODO MAKE EXISTS CHECK A SEPARATE FUNCTION!!!
# TODO PROVIDE HELP INSTRUCTIONS, separate commands into groups, add multi-server support(?)
# TODO 2000 symbols limit for suggestions list

description = '''An awkward attempt at making a discord bot'''


initial_extensions = ['cogs.suggestions',
                      'cogs.tags',
                      'cogs.dictionaries',
                      'cogs.wisdom',
                      'cogs.admin',
                      'cogs.owner']


def get_prefix(_bot, message):
    """A callable Prefix. This could be edited to allow per server prefixes."""
    prefixes = ['$']

    if not message.guild:
        return ['$', '!', '?']

    return commands.when_mentioned_or(*prefixes)(_bot, message)


class CompanionCube(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix, description=description)
        self.db_name = 'cube.db'


bot = CompanionCube()


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game('with turrets'))
    for guild in bot.guilds:
        await add_role_to_streamers(guild)


@bot.event
async def on_member_update(before, after):
    guild = before.guild
    channel = discord.utils.get(guild.text_channels, name='troubleshoot') \
        or discord.utils.get(guild.text_channels, name='secluded_cave')
    role = discord.utils.get(guild.roles, name='Live Queue')
    if after.activity and after.activity.type.name == 'streaming':
        if not before.activity or before.activity.type.name != 'streaming':
            await channel.send(f'{after.name} is {after.activity.type.name}. Attempting to add role.')
            await after.add_roles(role)
        else:
            return
    if before.activity and before.activity.type.name == 'streaming':
        if not after.activity or after.activity.type.name != 'streaming':
            await channel.send(f'{after.name} stopped {before.activity.type.name}. Attempting to remove role.')
            await after.remove_roles(role)


if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.')
    if check_database(bot.db_name):
        bot.run(environ['BOT_PROD'])
    else:
        exit(1)
