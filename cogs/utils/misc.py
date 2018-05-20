from discord.utils import get


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
        await member.add_roles(role)
