import sqlite3
import difflib
from contextlib import closing
from discord.ext import commands
from cogs.utils.misc import check_admin_rights
from cogs.utils.db import add_user_to_db_or_pass


class TagsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=['tags'])
    async def tag(self, ctx, *, tag_name=''):
        """
        Retrieves tag by name
        Available command alias - $tags
        Usage example:
        $tag mytag
        will fetch `mytag` from saved tags
        """
        guild_id = ctx.guild.id
        if tag_name == '':
            await ctx.send('Tag name required')
        else:
            tag_name = tag_name.strip()
            if tag_name[0] == '\"':
                tag_name = tag_name.strip('"')
            with closing(sqlite3.connect(self.bot.db_name)) as con:
                with con:
                    result = con.execute('SELECT tag_content FROM Tags WHERE tag_name=? AND guild_id=?',
                                         (tag_name, guild_id,)).fetchone()
                    if not result:
                        tag_id = con.execute('SELECT tag_id, alias FROM Tag_Aliases WHERE alias=? AND guild_id=?',
                                             (tag_name, guild_id,)).fetchone()
                        if tag_id:
                            tag_id = tag_id[0]
                            result = con.execute('SELECT tag_content FROM Tags WHERE ROWID=?',
                                                 (tag_id,)).fetchone()
            if result:
                tag_content = result[0]
                await ctx.send(tag_content)
            else:
                with closing(sqlite3.connect(self.bot.db_name)) as con:
                    with con:
                        tags = [x[0] for x in con.execute('SELECT tag_name FROM Tags WHERE guild_id=?',
                                                          (guild_id,)).fetchall()]
                matches = difflib.get_close_matches(tag_name, tags, cutoff=0.4)
                if matches:
                    matches = '\n'.join(matches)
                    await ctx.send(f'Command or tag `{tag_name}` not found, did you mean:\n```\n{matches}\n```')
                else:
                    await ctx.send(f'Command or tag "{tag_name}" not found')

    @commands.guild_only()
    @tag.command(aliases=['search', 'find'], name='list')
    async def _list(self, ctx, *, _filter=''):
        """
        Lists existing tags. By default shows only the tags of the user invoking the command.
        Allows filters to extend the search. Currently available filters are: `all`
        or just any custom string to search for the matching tag name(s).
        Available command aliases - $tag search | $tag filter
        Usage examples:
        $tag list
        lists the user's tags

        $tag list all
        lists all tags

        $tag search dnd
        lists all tags with `dnd` in their names

        $tag filter nice meme
        lists all tags with `nice meme` in their names
        """
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        username = str(ctx.author.name)
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                if _filter == '':
                    result = con.execute('SELECT tag_name, user_id FROM Tags WHERE user_id=? AND guild_id=?',
                                         (user_id, guild_id,)).fetchall()
                    message = f"Tags owned by {username}:\n```\n"
                elif _filter == 'all':
                    result = con.execute('SELECT tag_name FROM Tags WHERE guild_id=?',
                                         (guild_id,)).fetchall()
                    message = f"All available tags:\n```\n"
                else:
                    result = con.execute('SELECT tag_name FROM Tags WHERE tag_name LIKE ? AND guild_id=?',
                                         (f"%{_filter}%", guild_id,)).fetchall()
                    message = f"Tags filtered by `{_filter}`:\n```\n"
        if result:
            for entry in result:
                message += f"{entry[0]}\n"
            await ctx.send(message[:-1] + '```')
        else:
            await ctx.send('No tags found')

    @commands.guild_only()
    @tag.command(aliases=['create'])
    async def add(self, ctx, tag_name, *, tag_content=''):
        """
        Add a tag
        Available command alias - $tag create
        Usage example:
        $tag add tagname your text here
        or
        $tag add \"long tag name\" your text here
        If the name is more than one word long, put it in quotes, otherwise only the first word will be used as a name
        No quotes are needed for the rest of the text
        """
        if not tag_content:
            await ctx.send('Tag content cannot be empty')
            return
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        username = str(ctx.author.name)
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                add_user_to_db_or_pass(con, username, user_id)
            try:
                with con:
                    con.execute('INSERT INTO Tags(user_id, tag_name, tag_content, guild_id) VALUES(?, ?, ?, ?);',
                                (user_id, tag_name, tag_content, guild_id))
                await ctx.send(f'Successfully added "{tag_name}" to {username}\'s tags')
            except sqlite3.IntegrityError:
                await ctx.send(f'Failed to add tag "{tag_name}", name already exists')

    @commands.guild_only()
    @tag.command()
    async def alias(self, ctx, tag_name, *, tag_alias):
        """
        Add an alias for a tag, you don't need to be the tag's owner.
        Usage example:
        $tag alias \"long tag name\" \"some alias\"
        or
        $tag alias sometag altname
        If the tag's name or alias is more than one word long, put it in quotes.
        For single-word names and aliases quotes will work but are not required.
        """
        guild_id = ctx.guild.id
        if not tag_alias:
            await ctx.send('Tag alias cannot be empty')
            return
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                result = con.execute('SELECT tag_name FROM Tags WHERE tag_name = ? AND guild_id=?;',
                                     (tag_alias, guild_id,)).fetchone()
                if result:
                    await ctx.send(f"Failed to add alias \"{tag_alias}\", a tag with that name already exists")
                else:
                    result = con.execute('SELECT tag_name, ROWID FROM Tags WHERE tag_name = ? AND guild_id=?',
                                         (tag_name, guild_id,)).fetchone()
                    tag_id = result[1] if result else await ctx.send(f"Failed to add alias, tag \"{tag_name}\" not found")
                    try:
                        con.execute('INSERT INTO Tag_Aliases(user_id, tag_id, alias, guild_id) VALUES(?, ?, ?, ?);',
                                    (ctx.author.id, tag_id, tag_alias, guild_id))
                        await ctx.send(f"Successfully added alias \"{tag_alias}\" for tag \"{tag_name}\"")
                    except sqlite3.IntegrityError:
                        await ctx.send(f"Failed to add alias \"{tag_alias}\", name already exists")

    @commands.guild_only()
    @tag.command()
    async def append(self, ctx, tag_name, *, appended_content):
        """
        Append content to an existing tag. Available to tag owner or admin.
        Usage exapmle:
        $tag append "my tag name" This is the text I want to append
        The content will be added to the tag on a new line.
        """
        guild_id = ctx.guild.id
        if appended_content == '':
            await ctx.send('Specify the text you want to append after the tag\'s name')
        else:
            with closing(sqlite3.connect(self.bot.db_name)) as con:
                with con:
                    result = con.execute('SELECT ROWID, user_id, tag_content FROM Tags WHERE tag_name=? AND guild_id=?',
                                         (tag_name, guild_id,)).fetchone()
                    if result:
                        tag_id, owner_id, tag_content = result[0], result[1], result[2]
                        if owner_id == ctx.author.id or await check_admin_rights(ctx):
                            con.execute('UPDATE Tags SET tag_content=? WHERE ROWID=?;',
                                        (f"{tag_content}\n{appended_content}", tag_id,))
                            await ctx.send(f'Successfully edited tag "{tag_name}"')
                        else:
                            await ctx.send(f'You are not this tag\'s owner or admin, {ctx.author.name}, stop ruckusing!')
                    else:
                        await ctx.send(f'Tag "{tag_name}" not found')

    @commands.guild_only()
    @tag.command()
    async def edit(self, ctx, tag_name, *, new_content):
        """
        Fully replace the content of an existing tag. Available to tag owner or admin.
        Usage exapmle:
        $tag edit "my tag name" This is the new tag text
        """
        guild_id = ctx.guild.id
        if new_content == '':
            await ctx.send('Tag content cannot be empty')
        else:
            with closing(sqlite3.connect(self.bot.db_name)) as con:
                with con:
                    result = con.execute('SELECT ROWID, user_id FROM Tags WHERE tag_name=? AND guild_id=?',
                                         (tag_name, guild_id,)).fetchone()
                    if result:
                        tag_id, owner_id = result[0], result[1]
                        if owner_id == ctx.author.id or await check_admin_rights(ctx):
                            con.execute('UPDATE Tags SET tag_content=? WHERE ROWID=?;',
                                        (new_content, tag_id,))
                            await ctx.send(f'Successfully edited tag "{tag_name}"')
                        else:
                            await ctx.send(f'You are not this tag\'s owner or admin, {ctx.author.name}, stop ruckusing!')
                    else:
                        await ctx.send(f'Tag "{tag_name}" not found')

    @commands.guild_only()
    @tag.command(aliases=['remove'])
    async def delete(self, ctx, *, tag_name=''):
        """
        Delete a tag (admin or owner only)
        Available command alias - $tag remove
        Usage example:
        $tag delete tagname
        """
        guild_id = ctx.guild.id
        if tag_name == '':
            await ctx.send('Tag name required')
        else:
            tag_name = tag_name.strip()
            if tag_name[0] == '\"':
                tag_name = tag_name.strip('"')
            with closing(sqlite3.connect(self.bot.db_name)) as con:
                con.execute('PRAGMA foreign_keys = 1;')
                with con:
                    result = con.execute('SELECT ROWID, user_id FROM Tags WHERE tag_name=? AND guild_id=?',
                                         (tag_name, guild_id)).fetchone()
                    if result:
                        tag_id, owner_id = result[0], result[1]
                        if owner_id == ctx.author.id or await check_admin_rights(ctx):
                            con.execute('DELETE FROM Tags WHERE ROWID=?;',
                                        (tag_id,))
                            await ctx.send(f'Successfully deleted tag "{tag_name}"')
                        else:
                            await ctx.send(f'You are not this tag\'s owner or admin, {ctx.author.name}, stop ruckusing!')
                    else:
                        await ctx.send(f'Tag "{tag_name}" not found')


def setup(bot):
    bot.add_cog(TagsCog(bot))
