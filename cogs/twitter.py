# This is a twitter cog for a Discord bot. It grabs tweets from a specified feed and
# posts them to a channel in the Discord server.
# Author: ryanalexanderhughes@gmail.com (@broccoligamedev)

# --- NOTES ON SETUP ---
# The cog is going to look for a file called "twitter.txt" for the info it needs to function.
# The file should contain the following, in order, on separate lines:
#
# 1. The name of the Twitter account you want to watch. e.g. "broccoligamedev"
# 2. The ID of the Discord channel you want to post tweets to.
# 3. The Twitter app consumer key.
# 4. The Twitter app consumer secret.
# 5. The Twitter app access token key.
# 6. The Twitter app access token secret.
#
# ----------------------

from discord.ext import commands
import asyncio
import twitter

class TwitterCog:
    def __init__(self, bot):
        self.api = None
        self.bot = bot
        self.last_posted_tweet_time = 0
        self.TEXT_CHANNEL_ID = 0
        self.TWITTER_ACCOUNT_NAME = ""
        self.twitter_task = None

    # Make cog commands only available to admins
    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author) or ctx.author.guild_permissions.administrator

    # Cog setup
    async def on_ready(self):
        print("Reading from twitter.txt.")
        with open("twitter.txt") as f:
            secrets = f.read().splitlines()
            self.TWITTER_ACCOUNT_NAME = secrets[0]
            self.TEXT_CHANNEL_ID = int(secrets[1])
            self.api = twitter.Api(
                consumer_key=secrets[2],
                consumer_secret=secrets[3],
                access_token_key=secrets[4],
                access_token_secret=secrets[5]
            )
        print("Ok.")
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
        text_channel = self.bot.get_channel(self.TEXT_CHANNEL_ID)
        while True:
            tweets = await self.get_tweets()
            for tweet in tweets:
                if tweet.created_at_in_seconds > self.last_posted_tweet_time:
                    self.last_posted_tweet_time = tweet.created_at_in_seconds
                    await text_channel.send(
                        "https://twitter.com/{}/status/{}".format(
                            tweet.user.screen_name, 
                            tweet.id
                        )
                    )
            await asyncio.sleep(30)
    
    # Return a list of tweets, oldest to newest
    async def get_tweets(self):
        posts = self.api.GetUserTimeline(screen_name=self.TWITTER_ACCOUNT_NAME)
        posts.reverse()
        return posts

    # Helper method to save settings
    def save_settings(self, value: str, line_number: int):
        """
        replaces line `line_number` with `value` in twitter.txt
        the first line is line_number 0
        """
        with open("twitter.txt", 'r+') as f:
            secrets = f.read().splitlines()
            secrets[line_number] = value
            f.seek(0)
            f.write('\n'.join(secrets))

    @commands.group(invoke_without_command=True, aliases=['twitter'])
    async def _twitter(self, ctx):
        """
        Show/change current twitter settings, see $help twitter
        `$twitter` with no arguments shows current settings
        """
        await ctx.channel.send(f'Twitter account: {self.TWITTER_ACCOUNT_NAME}\nPosting to: {self.bot.get_channel(self.TEXT_CHANNEL_ID)}')

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
        self.TEXT_CHANNEL_ID = int(channel_id)
        self.twitter_task.cancel()
        self.twitter_task = self.bot.loop.create_task(self.post_tweets())
        self.save_settings(channel_id, 1)
        await ctx.channel.send(f'Tweet channel set to #{self.bot.get_channel(self.TEXT_CHANNEL_ID)}')

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
        self.TWITTER_ACCOUNT_NAME = account_name
        self.twitter_task.cancel()
        self.twitter_task = self.bot.loop.create_task(self.post_tweets())
        self.save_settings(account_name, 0)
        await ctx.channel.send(f'Tracking twitter account `@{self.TWITTER_ACCOUNT_NAME}`')


def setup(bot):
    try:
        cog = TwitterCog(bot)
        bot.add_cog(cog)
    except Exception as e:
        print(e)
        raise e
