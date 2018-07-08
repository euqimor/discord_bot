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
        self.bot.loop.create_task(
            self.post_tweets()
        )

    # Post tweets to the provided Discord channel. The loop runs every 30 seconds.
    async def post_tweets(self):
        text_channel = self.bot.get_channel(self.TEXT_CHANNEL_ID)
        while self.bot.run_twitter_loop:
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
        print('Stopping TwitterCog loop, reverting bot.run_twitter_loop back to True')
        self.bot.run_twitter_loop = True
    
    # Return a list of tweets, oldest to newest
    async def get_tweets(self):
        posts = self.api.GetUserTimeline(screen_name=self.TWITTER_ACCOUNT_NAME)
        posts.reverse()
        return posts

def setup(bot):
    try:
        cog = TwitterCog(bot)
        bot.add_cog(cog)
    except Exception as e:
        print(e)
        raise e
