#!/usr/bin/env python3

# import discord, json, lib
# from bot import WriterBot
# from discord.ext import commands
# from discord_slash import SlashCommand
#
# # Load the settings for initial setup
# config = lib.get('./settings.json')
#
# # Load the Bot object
# status = discord.Game( 'Booting up...' )
# bot = WriterBot(command_prefix=WriterBot.load_prefix, activity=status)
# slash = SlashCommand(bot, sync_commands=True)
#
# # Load all commands
# bot.load_commands()
#
# # Start the bot
# bot.run(config.token)


import os
import lib
import interactions


def load_commands_on(bot: interactions.Client):
    """
    Load all the commands from the cogs/ directory.
    :return: void
    """
    # Find all the command groups in the cogs/ directory
    for command_dir in ['util', 'fun', 'writing']:
        # Then all the files inside the command group directory
        for file in os.listdir(f'cogs/{command_dir}'):
            # If it ends with .py then try to load it.
            if file.endswith(".py"):
                cog = file[:-3]
                try:
                    bot.load(f"cogs.{command_dir}.{cog}")
                    lib.out(f'[EXT][{dir}.{cog}] loaded')
                except Exception as e:
                    lib.out(f'[EXT][{dir}.{cog}] failed to load')
                    lib.out(e)


# Load the settings for initial setup
config = lib.get('./settings.json')

bot = interactions.Client(config.token)

load_commands_on(bot)

bot.start()

