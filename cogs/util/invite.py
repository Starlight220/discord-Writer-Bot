import discord
from interactions import Client, Extension, extension_command as command, CommandContext

import lib
# from structures.guild import Guild


class Invite(Extension):
    def __init__(self, bot):
        self.client: Client = bot

    @command(
        name="invite",
        scope=894554679143464960,
        description="""
        Displays an embed with and invite link
        """
    )
    async def invite(self, context: CommandContext):
        # TODO: fix Guild -- `context.guild` doesn't exist anymore; use `context.guild_id`!
        # if not Guild(context.guild).is_command_enabled('invite'):
        #     return await context.send(lib.get_string('err:disabled', context.guild.id))

        config = lib.get('./settings.json')
        invite_embed = discord.Embed(title='Invite Link', color=652430, url=config.invite_url)
        invite_embed.add_field(name='Click the title for the invite link!',
                               value="Use the Above link to invite the bot to your servers!")

        await context.send(embed=invite_embed)


def setup(bot):
    Invite(bot)
