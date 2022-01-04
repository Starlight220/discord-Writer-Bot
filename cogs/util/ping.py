import lib
from structures.guild import Guild
from discord.ext import commands
from discord_slash import cog_ext, SlashContext


class Ping(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="ping", description="Displays latency between client and bot")
    async def ping(self, context: SlashContext):
        """
        Displays latency between client and bot
        """
        context.defer()
        if not Guild(context.guild).is_command_enabled('ping'):
            return await context.send(lib.get_string('err:disabled', context.guild.id))

        latency = round(self.bot.latency * 1000, 2)
        return await context.send('Pong! ' + str(latency) + 'ms')

    @commands.command(name="ping")
    @commands.guild_only()
    async def old_ping(self, context):
        await context.send(lib.get_string('err:slash', context.guild.id))


def setup(bot):
    bot.add_cog(Ping(bot))
