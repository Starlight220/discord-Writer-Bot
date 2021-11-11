import lib, pytz, time
from structures.db import Database

class Reminder:

    OLD_CUTOFF = 60*59 # Cut off time for old reminders which were not sent for whatever reason - 59 minutes

    def __init__(self, id = None):
        self.__db = Database.instance()
        self.id = None
        self.user = None
        self.guild = None
        self.time = None
        self.channel = None
        self.message = None
        self.intervaltime = None

        record = self.__db.get('reminders', {'id': id})
        if record:
            self.load(record)


    def load(self, record):
        """
        Load data from the database onto the object
        @param record:
        @return:
        """
        for key in record:
            setattr(self, key, record[key])

    def info(self, context):
        """
        Return basic info for the list of reminders
        @return:
        """
        now = int(time.time())
        left = self.time - now

        if self.channel:
            channel = context.guild.get_channel(int(self.channel)).mention
        else:
            channel = '???'

        message = '`' + self.message + '`' + ' (' + channel + ')\t\t'
        if left > 0:
            message += lib.format_secs_to_days(left)
        else:
            message += lib.get_string('remind:anytimenow', self.guild)

        # Is there a repeating interval?
        if self.intervaltime is not None:
            message += '\t\t**(' + lib.get_string('remind:interval', self.guild).format(lib.format_secs_to_days(self.intervaltime)) + ')**'

        return message

    def delete(self):
        """
        Delete this reminder
        @return:
        """
        return self.__db.delete('reminders', {'id' : self.id})

    async def task_send(self, bot) -> bool:
        """
        Scheduled task to send any pending reminders
        :param task:
        :return: bool
        """

        now = int(time.time())

        # Find all reminders which are pending.
        records = self.__db.get_all_sql('SELECT id FROM reminders WHERE time <= %s', [now])
        for record in records:

            reminder = Reminder(record['id'])

            # If for some reason an old one didn't get sent, just skip it without sending if it's too late.
            if (now - int(reminder.time)) > self.OLD_CUTOFF:
                reminder.delete_or_reschedule()
                continue

            # Otherwise, try and send it, then delete it.
            await reminder.send(bot)

        return True

    async def send(self, bot):
        """
        Send the reminder to the relevant channel
        @return:
        """
        channel = bot.get_channel(int(self.channel))
        if channel:

            # Note: If this causes slow down problems, if too many are getting sent, may have to re-do this
            # to get an array of all user ids per guild id and query those together.
            member = await bot.get_guild(int(self.guild)).fetch_member(int(self.user))
            if member:

                # Try and send the message to the specified channel.
                try:
                    await channel.send(self.message)
                except Exception:
                    # If the bot doesn't have permissions to post there, we can't do it.
                    pass

        # Now delete the reminder, or reschedule its next run time if it's an interval one.
        self.delete_or_reschedule()

    def delete_or_reschedule(self):
        """
        Either delete the reminder or change its next run time if it's an interval one
        @return:
        """
        if self.intervaltime is not None:
            self.__db.update('reminders', {'time': int(self.time) + int(self.intervaltime)}, {'id': self.id})
        else:
            self.delete()

    def all(user = None, guild = None):
        """
        Get all reminders for the user/guild
        @return:
        """
        db = Database.instance()
        reminders = []
        records = db.get_all('reminders', {'user': user, 'guild': guild}, sort=['id ASC'])
        for record in records:
            reminders.append(Reminder(record['id']))
        return reminders

    def create(params):
        """
        Create a reminder in the database
        @return:
        """
        db = Database.instance()
        return db.insert('reminders', params)

