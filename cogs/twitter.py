# This is a twitter cog for a Discord bot. It grabs tweets from a specified feed and
# posts them to a channel in the Discord server.
# Author: ryanalexanderhughes@gmail.com (@broccoligamedev)

from discord.ext import commands
import asyncio
import twitter
from cogs.utils.misc import save_to_config


class TwitterCog(commands.Cog):
    def __init__(self, bot):
        self.api = None
        self.bot = bot
        self.last_posted_tweet_time = 0
        self.text_channel_id = 0
        self.twitter_account_name = ""
        self.twitter_task = None

    # Make cog commands only available to admins
    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author) or ctx.author.guild_permissions.administrator

    # Cog setup
    async def on_ready(self):
        print("Initializing TwitterCog.")
        self.twitter_account_name = self.bot.config["twitter_account_name"]
        self.text_channel_id = self.bot.config["twitter_text_channel_id"]
        self.api = twitter.Api(
            consumer_key=self.bot.config["twitter_consumer_key"],
            consumer_secret=self.bot.config["twitter_consumer_secret"],
            access_token_key=self.bot.config["twitter_access_token"],
            access_token_secret=self.bot.config["twitter_access_secret"]
        )
        # Check the current timeline so we only post new tweets.
        # Note: If the bot goes down, it could miss tweets. In practice, this isn't a big deal
        # but it could be improved by using the database so the bot remembers which tweets it's 
        # already posted. 
        tweets = await self.get_tweets()
        if len(tweets) > 0:
            self.last_posted_tweet_time = tweets[-1].created_at_in_seconds
        print("Running TwitterCog loop.")
        # This starts the asyc loop for checking and posting tweets
        self.twitter_task = self.bot.loop.create_task(
            self.post_tweets()
        )

    # Post tweets to the provided Discord channel. The loop runs every 30 seconds.
    async def post_tweets(self):
        text_channel = self.bot.get_channel(self.text_channel_id)
        while True:
            tweets = await self.get_tweets()
            for tweet in tweets:
                if tweet.created_at_in_seconds > self.last_posted_tweet_time:
                    self.last_posted_tweet_time = tweet.created_at_in_seconds
                    await text_channel.send(f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
            await asyncio.sleep(30)
    
    # Return a list of tweets, oldest to newest
    async def get_tweets(self):
        posts = self.api.GetUserTimeline(screen_name=self.twitter_account_name)
        posts.reverse()
        return posts

    # Helper method to save settings
    @staticmethod
    def save_settings(value: str, line_number: int):
        """
        replaces line `line_number` with `value` in twitter.txt
        the first line is line_number 0
        """
        with open("twitter.txt", 'r+') as f:
            secrets = f.read().splitlines()
            secrets[line_number] = value
            f.seek(0)
            f.write('\n'.join(secrets)+'\n')

    @commands.group(invoke_without_command=True, name='twitter')
    async def _twitter(self, ctx):
        """
        Show/change current twitter settings, see $help twitter
        `$twitter` with no arguments shows current settings
        """
        await ctx.channel.send(f'Twitter account: `@{self.twitter_account_name}`'
                               f'\n\nPosting to: <#{self.text_channel_id}>')

    @_twitter.command()
    async def channel(self, ctx, channel_id):
        """
        Set to which channel to post tweets, accepts #channel or numeric channel id
        Usage examples:
        $twitter channel #general
        or
        $twitter channel 337724971348525057
        """
        channel_id = channel_id.strip('<#>')
        self.text_channel_id = int(channel_id)
        self.twitter_task.cancel()
        self.twitter_task = self.bot.loop.create_task(self.post_tweets())
        save_to_config('twitter_text_channel_id', channel_id)
        await ctx.channel.send(f'Tweet channel set to <#{self.text_channel_id}>')

    @_twitter.command()
    async def account(self, ctx, account_name):
        """
        Set which twitter account to track
        Usage examples:
        $twitter account @broccoligamedev
        or
        $twitter account broccoligamedev
        """
        account_name = account_name.strip('@')
        self.twitter_account_name = account_name
        self.twitter_task.cancel()
        self.twitter_task = self.bot.loop.create_task(self.post_tweets())
        save_to_config('twitter_account_name', account_name)
        await ctx.channel.send(f'Tracking twitter account `@{self.twitter_account_name}`')


def setup(bot):
    try:
        cog = TwitterCog(bot)
        bot.add_cog(cog)
    except Exception as e:
        print(e)
        raise e
