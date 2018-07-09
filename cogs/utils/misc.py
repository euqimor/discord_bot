from discord.utils import get
import yaml


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


async def add_role_to_streamers(guild):
    role = get(guild.roles, name='Live Queue')
    streaming_members = [x for x in guild.members if x.activity and x.activity.type.name == 'streaming']
    for member in streaming_members:
        if member.top_role < guild.me.top_role:
            await member.add_roles(role)


async def remove_role_from_non_streamers(guild):
    role = get(guild.roles, name='Live Queue')
    members_with_role = [x for x in guild.members if role in x.roles]
    for member in members_with_role:
        if not member.activity or (member.activity and member.activity.type.name != 'streaming'):
            if member.top_role < guild.me.top_role:
              await member.remove_roles(role)


def save_to_config(variable_name, variable_value):
    with open('config.yaml', 'r+') as f:
        config = yaml.load(f)
        config[variable_name] = variable_value
        f.truncate(0)
        f.seek(0)
        yaml.dump(config, f, default_flow_style=False)