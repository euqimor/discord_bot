import discord
from discord.ext import commands
from sys import exit
from os import environ, path
from cogs.utils.db import check_database
from cogs.utils.misc import add_role_to_streamers, remove_role_from_non_streamers, append_partner_link
import yaml
import re


description = '''An awkward attempt at making a discord bot'''
initial_extensions = ['cogs.suggestions',
                      'cogs.tags',
                      # 'cogs.twitter',
                      'cogs.dictionaries',
                      'cogs.silly',
                      'cogs.admin',
                      'cogs.owner',
                      'cogs.dice',
                      'cogs.steam',
                      ]


def get_prefix(_bot, message):
    """A callable Prefix. This could be edited to allow per server prefixes."""
    prefixes = ['$']

    if not message.guild:
        return ['$', '!', '?']

    return commands.when_mentioned_or(*prefixes)(_bot, message)


class CompanionCube(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix, description=description)
        self.config = {}
        self.db_name = 'cube.db'
        self.humble_expr = re.compile('(?:^|.*)(https?://www.humblebundle.com.*?)(?:\s|$)')
        # self.spice = [
        #     'Spice? Do you spice?',
        #     'Spice? What do you think? Little spice?',
        #     'Spice? Spice it? Little spice?'
        # ]
        # self.spice_cooldown_start = 0.0

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}.\nException: {e}')


bot = CompanionCube()


@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user.name} ({bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Game('with turrets'))
    for guild in bot.guilds:
        await add_role_to_streamers(guild)
        await remove_role_from_non_streamers(guild)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        user = ctx.bot.get_user(173747843314483210)
        await user.send(error)


# @bot.event
# async def on_message(message):
#     if 'spice' in message.clean_content.strip('?!,.*').split() and (time.time() - bot.spice_cooldown_start) > 21600:
#         bot.spice_cooldown_start = time.time()
#         await message.channel.send(random.choice(bot.spice))
#     await bot.process_commands(message)


@bot.event
async def on_message(message):
    regex_search = re.match(bot.humble_expr, message.clean_content)
    if regex_search and not '?partner=' in regex_search[1]:
        partner_link = append_partner_link(regex_search[1])
        await message.channel.send(f"Humbly converting the link to Aella's partner link if you feel like using it:\
                                   \n{partner_link}\
                                   \n\nIf you want more information on how the Humble Partner program works, here's the FAQ: \
                                   \nhttps://support.humblebundle.com/hc/en-us/articles/223517768-Humble-Partner-Program-FAQ")
    await bot.process_commands(message)


@bot.event
async def on_member_update(before, after):
    guild = before.guild
    bot_role = guild.me.top_role

    # only add to members that are below us
    if after.top_role > bot_role:
        return

    # add or remove streaming role as necessary
    role = discord.utils.get(guild.roles, name='Live Queue')
    if after.activity is None or after.activity.type.name != 'streaming':
        if role in after.roles:
            await after.remove_roles(role)
    else:
        if not role in after.roles:
            await after.add_roles(role)

if __name__ == '__main__':
    if check_database(bot.db_name):
        if path.exists("config.yaml"):
            with open("config.yaml") as f:
                print("Reading from config file.")
                bot.config = yaml.load(f)
                secret_key = bot.config["discord_token"]
                bot.run(secret_key)
        else:
            print("Config file not found, terminating.")
            exit(1)
    else:
        print("Database connection failed, terminating.")
        exit(1)
