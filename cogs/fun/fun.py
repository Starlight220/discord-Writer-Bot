import random

import interactions
from interactions import Client, extension_command as command, Option, OptionType, CommandContext

import lib
from structures.guild import Guild


class Fun(interactions.Extension):

    ROLL_MAX_SIDES = 1000000000000
    ROLL_MAX_ROLLS = 100

    def __init__(self, bot: Client):
        self.bot: Client = bot

    @command(
        name="8ball",
        description="Ask the magic 8ball a question",
        options=[
            Option(
                name="question",
                description="What is your question for the magic 8ball?",
                type=OptionType.STRING,
                required=True
            )
        ]
    )
    async def _8ball(self, context: CommandContext, question: str):
        """
        Ask the magic 8-ball a question.

        :param SlashContext context: SlashContext object
        :param str question: The question the user is asking
        :rtype: void
        """

        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Make sure the guild has this command enabled.
        if not Guild(context.guild).is_command_enabled('8ball'):
            return await context.send(lib.get_string('err:disabled', context.guild_id))

        guild_id = context.guild_id

        # Pick a random answer
        i: int = random.randrange(21)
        answer: str = lib.get_string(f"8ball:{i}", guild_id)

        # Send the message
        await context.send(
            context.author.mention + ', ' +
            lib.get_string('8ball:yourquestion', guild_id).format(question) + answer
        )

    @command(
        name="flip",
        description="Flip a coin"
    )
    async def flip(self, context: CommandContext):
        """
        Flips a coin.

        :param SlashContext context: SlashContext object
        :rtype: void
        """

        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Make sure the guild has this command enabled.
        if not Guild(context.guild).is_command_enabled('flip'):
            return await context.send(lib.get_string('err:disabled', context.guild_id))

        guild_id = context.guild_id

        # Random number between 1-2 to choose heads or tails.
        rand = random.randrange(2)
        side = 'heads' if rand == 0 else 'tails'

        # Send the message.
        await context.send(lib.get_string('flip:' + side, guild_id))

    @command(
        name="quote",
        description="Generate a random motivational quote"
    )
    async def quote(self, context: CommandContext):
        """
        A random motivational quote to inspire you.

        :param SlashContext context: SlashContext object
        :rtype: void
        """

        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Make sure the guild has this command enabled.
        if not Guild(context.guild).is_command_enabled('quote'):
            return await context.send(lib.get_string('err:disabled', context.guild.id))

        guild_id = context.guild_id

        # Load the JSON file with the quotes
        quotes = lib.get_asset('quotes', guild_id)

        # Choose a random quote.
        max = len(quotes) - 1
        quote = quotes[random.randint(1, max)]

        # Send the message
        await context.send(format(quote['quote'] + ' - *' + quote['name'] + '*'))

    @command(
        name="reassure",
        description="Send a random reassuring message to a user or yourself",
        options=[
            Option(
                name="who",
                description="Who do you want to reassure?",
                option_type=OptionType.USER,
                required=False
            )
        ]
    )
    async def reassure(self, context: CommandContext, who: interactions.User = None):
        """
        Reassures you that everything will be okay.

        :param SlashContext context: SlashContext object
        :param str|None who: The name of the user to reassure
        :rtype: void
        """
        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Make sure the guild has this command enabled.
        if not Guild(context.guild).is_command_enabled('reassure'):
            return await context.send(lib.get_string('err:disabled', context.guild_id))

        guild_id = context.guild_id

        # If no name passed through, default to the author of the command.
        if who is None:
            mention = context.author.mention
        else:
            mention = who.mention

        # Load the JSON file with the quotes.
        messages = lib.get_asset('reassure', guild_id)

        # Pick a random message.
        max = len(messages) - 1
        quote = messages[random.randint(1, max)]

        # Send the message.
        await context.send(mention + ', ' + format(quote))

    @command(
        name="roll",
        description="Roll some dice",
        options=[
            Option(
                name="dice",
                description="What dice do you want to roll? Format: {number}d{sides}, e.g. 1d20, 2d8, etc... Default: 1d6",
                option_type=OptionType.STRING,
                required=False
            )
        ]
    )
    async def roll(self, context: CommandContext, dice: str = '1d6'):
        """
        Rolls a dice between 1-6, or 1 and a specified number (max 100).
        Can also roll multiple dice at once (max 100) and get the total.

        :param SlashContext context: SlashContext object
        :param str dice: The dice to roll, e.g. 1d6, 2d10, etc...
        :rtype: void
        """

        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Make sure the guild has this command enabled.
        if not Guild(context.guild).is_command_enabled('roll'):
            return await context.send(lib.get_string('err:disabled', context.guild_id))

        guild_id = context.guild_id

        import re
        # Make sure the format is correct (1d6).
        regex_matches = re.search(r'(\d)d(\d)', dice)
        if regex_matches is None:
            return await context.send(lib.get_string('roll:format', guild_id))
        else:
            sides, rolls = regex_matches.group(1, 2)

        # Make sure the sides and rolls are valid.
        if sides < 1:
            sides = 1
        elif sides > self.ROLL_MAX_SIDES:
            sides = self.ROLL_MAX_SIDES

        if rolls < 1:
            rolls = 1
        elif rolls > self.ROLL_MAX_ROLLS:
            rolls = self.ROLL_MAX_ROLLS

        total = 0
        output = ''

        # Roll the dice {rolls} amount of times.
        for x in range(rolls):
            val = random.randint(1, sides)
            total += val
            output += ' [ ' + str(val) + ' ] '

        # Now print out the total.
        output += '\n**' + lib.get_string('roll:total', guild_id) + str(total) + '**'

        # Send message.
        await context.send(output)


def setup(bot: Client):
    """
    Add the cog to the bot
    :param bot: Discord bot
    :rtype void:
    """
    Fun(bot)
