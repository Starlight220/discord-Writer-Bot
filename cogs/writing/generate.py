import time

from interactions import Extension, Option, OptionType, Choice, CommandContext
from interactions import extension_command as command

from structures.generator import NameGenerator
from structures.user import User

VISIBLE_TO_EVERYONE = 0
HIDDEN_EPHEMERAL = 1

SUPPORTED_TYPES = {
    'char': 'Character',
    'place': 'Place',
    'land': 'Land',
    'idea': 'Idea',
    'book': 'Book',
    'book_fantasy': 'Fantasy Book',
    'book_horror': 'Horror Book',
    'book_hp': 'Harry Potter Book',
    'book_mystery': 'Mystery Book',
    'book_rom': 'Romance Book',
    'book_sf': 'Sci-Fi Book',
    'prompt': 'Prompt',
    'face': 'Face',
    'question_char': 'Character-building question',
    'question_world': 'World-building question',
}


class Generate(Extension):
    def __init__(self, bot):
        self.bot = bot
        self._urls = {
            'face': 'https://thispersondoesnotexist.com/image'
        }

    @command(
        name="generate",
        description="Random generator for character names, place names, land names, book titles, story ideas, prompts.",
        options=[
            Option(
                name="type",
                description="What to generate",
                required=True,
                type=OptionType.STRING,
                choices=[
                    Choice(
                        name=name,
                        value=value
                    ) for value, name in SUPPORTED_TYPES.items()
                ]
            ),
            Option(
                name="amount",
                description="How many items to generate",
                required=False,
                type=OptionType.INTEGER
            ),
            Option(
                name="hidden",
                description="Should the response be in a hidden (ephemeral) message?",
                type=OptionType.INTEGER,
                required=False,
                choices=[
                    Choice(value=VISIBLE_TO_EVERYONE, name='Visible to everyone'),
                    Choice(value=HIDDEN_EPHEMERAL, name='Visible only to you')
                ]
            )
        ]
    )
    async def generate(self, context: CommandContext, type: str, amount: int = None,
                       hidden: int = VISIBLE_TO_EVERYONE):
        """
        Random generator for various things (character names, place names, land names, book titles, story ideas, prompts).
        Define the type of item you wanted generated and then optionally, the amount of items to generate.

        :param SlashContext context: Slash command context
        :param str type: Type of generation to do
        :param int amount: Amount of items to get
        :param bool hidden: Should the response be hidden to other users
        :rtype void:
        """
        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer(ephemeral=hidden == HIDDEN_EPHEMERAL)

        # TODO: fix guild usage
        # Make sure the guild has this command enabled.
        # if not Guild(context.guild).is_command_enabled('generate'):
        #     return await context.send(lib.get_string('err:disabled', context.guild.id))

        user = User(context.author.id, context.guild_id, context)

        # If no amount specified, use the default
        if amount is None:
            amount = NameGenerator.DEFAULT_AMOUNT

        # For faces, we want to just call an API url.
        if type == 'face':
            return await context.send(self._urls['face'] + '?t=' + str(int(time.time())))

        generator = NameGenerator(type, context)
        results = generator.generate(amount)
        join = '\n'

        # For prompts, add an extra line between them.
        if type == 'prompt':
            join += '\n'

        names = join.join(results['names'])

        return await context.send(user.get_mention() + ', ' + results['message'] + names)


def setup(bot):
    bot.add_cog(Generate(bot))
