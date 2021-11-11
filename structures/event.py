import discord, lib, time
from structures.db import Database
from structures.user import User

class Event:

    DEFAULT_COLOUR = 15105570
    # By default, limit leaderboard to 10 users
    DEFAULT_LEADERBOARD_LIMIT = 10
    # Because of discord limits, limit the leaderboard to 25 users
    UPPER_LEADERBOARD_LIMIT = 25
    TASKS = {
        'start': 'start',  # This is the task for starting the event
        'end': 'end',  # This is the task for ending the event
    }

    def __init__(self, id):
        self.__db = Database.instance()
        self.__bot = None
        self.__context = None
        self.__guild = None

        self.id = None
        self.guild = None
        self.channel = None
        self.title = None
        self.description = None
        self.img = None
        self.colour = None
        self.startdate = None
        self.enddate = None
        self.started = None
        self.ended = None

        record = self.__db.get('events', {'id': id})
        if record:
            self.id = record['id']
            self.guild = record['guild']
            self.channel = record['channel']
            self.title = record['title']
            self.description = record['description']
            self.img = record['img']
            self.colour = record['colour']
            self.startdate = record['startdate']
            self.enddate = record['enddate']
            self.started = record['started']
            self.ended = record['ended']

    def is_valid(self):
        """
        Check if the event object is valid
        :return:
        """
        return self.id is not None

    def is_running(self):
        """
        Check if the event is currently running
        :return:
        """
        return self.is_valid() and self.get_started() > 0 and self.get_ended() == 0

    def is_ended(self):
        """
        Check if the event has ended
        :return:
        """
        return self.ended and self.ended > 0

    def is_scheduled(self):
        """
        Check if the event has a scheduled start time
        :return:
        """
        return self.get_start_time() > 0

    def get_id(self):
        """
        Get the event id
        :return:
        """
        return self.id

    def get_title(self):
        """
        Return the event title
        :return:
        """
        return self.title

    def get_start_time(self):
        """
        Get the scheduled start timestamp
        :return:
        """
        return int(self.startdate) if self.startdate is not None else 0

    def get_end_time(self):
        """
        Get the scheduled end timestamp
        :return:
        """
        return int(self.enddate) if self.enddate is not None else 0

    def get_started(self):
        """
        Get the started timestamp
        :return:
        """
        return int(self.started) if self.started is not None else 0

    def get_ended(self):
        """
        Get the ended timestamp
        :return:
        """
        return int(self.ended) if self.ended is not None else 0

    def get_guild(self):
        """
        Get the guild ID of the event
        :return:
        """
        return int(self.guild)

    def get_channel(self):
        """
        Get the channel ID of the event
        :return:
        """
        return int(self.channel)

    def get_colour(self):
        """
        Get the colour to use for the embedded messages for this event
        :return:
        """
        return int(self.colour) if self.colour is not None else self.DEFAULT_COLOUR

    def get_description(self):
        """
        Get the event description
        :return:
        """
        return self.description

    def get_image(self):
        """
        Get the image url
        :return:
        """
        return self.img

    def set_bot(self, bot):
        """
        Set the bot object into the event
        :param bot:
        :return:
        """
        self.__bot = bot
        return self

    def set_context(self, context):
        """
        Set the context into the event
        :param context:
        :return:
        """
        self.__context = context
        return self

    def set_guild_object(self, guild):
        """
        Set the Guild object from the original message
        @param guild:
        @return:
        """
        self.__guild = guild
        return self

    def set_title(self, title):
        """
        Set the title
        :param title:
        :return:
        """
        self.title = title
        return self

    def set_channel(self, channel):
        """
        Set the channel ID
        :param channel:
        :return:
        """
        self.channel = channel
        return self

    def set_description(self, desc):
        """
        Set the description
        :param desc:
        :return:
        """
        self.description = desc
        return self

    def set_image(self, image):
        """
        Set the image URL
        :param image:
        :return:
        """
        self.img = image
        return self

    def set_colour(self, colour):
        """
        Set the colour to use
        :param colour:
        :return:
        """
        self.colour = colour
        return self

    def set_started(self, time):
        """
        Set the started time
        :param time:
        :return:
        """
        self.started = time
        return self

    def set_ended(self, time):
        """
        Set the ended time
        :param time:
        :return:
        """
        self.ended = time
        return self

    def set_startdate(self, time):
        """
        Set the start timestamp
        :param time:
        :return:
        """
        self.startdate = time
        return self

    def set_enddate(self, time):
        """
        Set the start timestamp
        :param time:
        :return:
        """
        self.enddate = time
        return self

    def delete(self):
        """
        Delete the event
        :return:
        """
        return self.__db.delete('events', {'id': self.id})

    def save(self):
        """
        Save the current state of the event
        :return:
        """
        return self.__db.update('events', {
            'title': self.title,
            'channel': self.channel,
            'description': self.description,
            'img': self.img,
            'colour': self.colour,
            'startdate': self.startdate,
            'enddate': self.enddate,
            'started': self.started,
            'ended': self.ended
        }, {'id': self.id})

    async def start(self):
        """
        Start the event
        :return:
        """
        now = int(time.time())
        self.set_started(now)
        self.save()
        await self.say( lib.get_string('event:begin', self.get_guild()).format(self.get_title()) )

    async def end(self):
        """
        End the event
        :return:
        """
        now = int(time.time())
        self.set_ended(now)
        self.save()
        await self.say( lib.get_string('event:ended', self.get_guild()).format(self.get_title()) )
        await self.say(await self.get_leaderboard(), embed=True)

    def get_wordcount(self, user_id):
        """
        Get the word count for a user on the event
        :param user_id:
        :return:
        """
        record = self.__db.get('user_events', {'user': user_id, 'event': self.get_id()})
        if record:
            return record['words']
        else:
            return 0

    def update_wordcount(self, user_id, amount):
        """
        Update the event word count for a user
        :param user_id:
        :param amount:
        :return:
        """
        record = self.__db.get('user_events', {'user': user_id, 'event': self.get_id()})
        if record:
            return self.__db.update('user_events', {'words': amount}, {'id': record['id']})
        else:
            return self.__db.insert('user_events', {
                'event': self.get_id(),
                'user': user_id,
                'words': amount
            })

    def add_words(self, user_id, amount):
        """
        Add to the user's word count for the event
        :param user_id:
        :param amount:
        :return:
        """
        amount = int(amount)
        record = self.__db.get('user_events', {'user': user_id, 'event': self.get_id()})
        if record:
            amount = int(record['words']) + amount

        return self.update_wordcount(user_id, amount)

    async def say(self, message, embed=False):
        """
        Send a message, either from the context or directly from the bot, depending on how it was called
        :param message:
        :return:
        """
        if self.__context is not None:
            if embed:
                return await self.__context.send(embed=message)
            else:
                return await self.__context.send(message)
        elif self.__bot is not None:
            channel = self.__bot.get_channel(self.get_channel())
            if embed:
                return await channel.send(embed=message)
            else:
                return await channel.send(message)

    def get_users(self, limit=None):
        """
        Get the users taking part in the event, ordered by words written descending
        :return:
        """
        records = self.__db.get_all('user_events', {'event': self.id}, '*', ['words DESC'])
        users = []
        x = 1

        for record in records:

            users.append({
                'user': record['user'],
                'words': record['words']
            })

            x += 1

            if limit is not None and x > limit:
                break

        return users

    def get_total_wordcount(self):
        """
        Get the total word count in this event
        :return:
        """
        record = self.__db.get('user_events', {'event': self.id}, ['SUM(words) as total'])
        return int(record['total']) if record['total'] is not None else 0

    async def get_leaderboard(self, limit=None):
        """
        Build the embedded leaderboard to display
        :return:
        """

        config = lib.get('./settings.json')
        users = self.get_users()

        # Build the embedded leaderboard message
        title = self.get_title() + ' - ' + lib.get_string('event:leaderboard', self.get_guild())
        description = lib.get_string('event:leaderboard:desc', self.get_guild()).format(limit, self.get_title())
        footer = lib.get_string('event:leaderboard:footer', self.get_guild()).format(limit)

        # If there is no limit, don't show the footer
        if limit is None:
            limit = self.DEFAULT_LEADERBOARD_LIMIT
            footer = None

        # If the event is finished, don't show the footer and adjust the description to take out 'so far'
        if self.is_ended():
            description = lib.get_string('event:leaderboard:desc:ended', self.get_guild()).format(self.get_title())
            footer = None

        image = self.get_image()
        if not image or len(image) == 0:
            image = config.avatar

        # We don't want to go over discord's character limit in a message
        character_count = 0

        embed = discord.Embed(title=title, color=self.get_colour(), description=description)

        character_count += lib.get_character_count(title + description)

        embed.set_thumbnail(url=image)
        if footer:
            embed.set_footer(text=footer, icon_url=config.avatar)
            character_count += lib.get_character_count(footer)

        # Get an array of all the user ids, so we can fetch them and make sure they still exist on the guild.
        user_ids = list(map(lambda row: row['user'], users))

        # Using those user_ids, look them all up and return a list of those which are still on the guild.
        if user_ids:
            members = await self.__guild.query_members(limit=100, cache=False, user_ids=user_ids)

            # Create a sub method to find a user in the members list by their id
            def find_member(id):
                for m in members:
                    if m.id == id:
                        return m
                return None

            # Loop through the users, filtering out any which are not on the guild and returning their name for display.
            position = 1

            for user in users:

                member = find_member(int(user['user']))
                if member is not None and position <= limit:

                    # Build the name and words variables to display in the list
                    name = str(position) + '. ' + member.display_name
                    words = str(user['words']) + ' ' + lib.get_string('words', self.get_guild())

                    # Embed this user result as a field
                    if lib.get_character_count(name + words) + character_count <= lib.MAXIMUM_MESSAGE_CHARACTER_LIMIT:
                        embed.add_field(name=name, value=words, inline=False)

                    # Increment position
                    position += 1
        return embed

    def _task_prechecks(self, bot):
        """
        Run pre-task checks before attempting to run whichever scheduled task it is
        :param bot:
        :return:
        """
        guild = bot.get_guild(int(self.guild))
        return guild is not None

    async def task_start(self, bot):
        """
        Run the event starting task
        :param bot:
        :return:
        """
        # Run pre-checks
        if not self._task_prechecks(bot):
            return True

        # If the event is already running, we don't need to do this.
        if self.is_running():
            return True

        # Beyond that, we don't do any checks. We have to assume that if the task is scheduled for this time, then so must the event start time be.

        # Set the bot into the object
        self.set_bot(bot)

        # Otherwise, run the start method.
        await self.start()
        return True

    async def task_end(self, bot):
        """
        Run the event ending task
        :param bot:
        :return:
        """
        # Run pre-checks
        if not self._task_prechecks(bot):
            return True

        # If the event is already running, we don't need to do this.
        if self.is_ended():
            return True

        # Beyond that, we don't do any checks. We have to assume that if the task is scheduled for this time, then so must the event end time be.

        # Set the bot into the object
        self.set_bot(bot)

        # Otherwise, run the start method.
        await self.end()
        return True

    @staticmethod
    def get_by_guild(guild_id, include_ended=False):
        """
        Get the event currently running on the specified guild
        :param guild_id:
        :param ended:
        :return:
        """
        db = Database.instance()

        # If we are including ones which have ended, just try and get the last one
        if include_ended:
            record = db.get('events', {'guild': guild_id}, ['id'], ['id DESC'])
        else:
            record = db.get('events', {'guild': guild_id, 'ended': 0})

        if record:
            return Event(record['id'])
        else:
            return None

    @staticmethod
    def create(guild, channel, title):
        """
        Create a new event
        :param guild:
        :param channel:
        :param title:
        :return:
        """
        db = Database.instance()
        return db.insert('events', {'guild': guild, 'channel': channel, 'title': title})