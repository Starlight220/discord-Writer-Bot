import discord, lib, re, pytz, time
from datetime import datetime, timezone, timedelta
from discord.ext import commands
from structures.reminder import Reminder
from structures.user import User
from structures.wrapper import CommandWrapper
from structures.guild import Guild

class Remind(commands.Cog, CommandWrapper):

    PROMPT_TIMEOUT = 60

    def __init__(self, bot):
        self.bot = bot
        self._supported_commands = ['create', 'edit', 'delete']
        self._reminder_intervals = {
            'hour': 60*60,
            'day': 60*60*24,
            'week': 60*60*24*7
        }
        self._arguments = [
            {
                'key': 'cmd',
                'prompt': 'remind:argument:cmd',
                'required': True,
                'check': lambda content: content in self._supported_commands,
                'error': 'remind:err:argument:cmd'
            }
        ]

    @commands.command(name="remind", aliases=['nag'])
    async def remind(self, context, *opts):
        """
        Set or configure a reminder
        @param opts:
        @param context:
        @return:
        """
        if not Guild(context.guild).is_command_enabled('remind'):
            return await context.send(lib.get_string('err:disabled', context.guild.id))

        user = User(context.message.author.id, context.guild.id, context)

        # Does the user have a timezone setup? If not, can't do anything.
        if not lib.is_valid_timezone(user.get_setting('timezone')):
            return await context.send(user.get_mention() + ', ' + lib.get_string('err:notimezone', user.get_guild()))

        # Convert the natural language of the command into variables.
        cmd = ' '.join(opts)

        # Check what we are trying to do with reminders.
        if cmd.lower() == 'list':
            return await self.run_list(context, user)
        elif cmd.lower() == 'delete':
            return await self.run_delete(context, user)
        else:
            return await self.run_remind(context, user, cmd)

    async def run_remind(self, context, user, cmd):
        """
        Set or configure a reminder
        @param context:
        @param user:
        @param cmd:
        @return:
        """
        now = int(time.time())

        remind_time = None
        message = None
        channel = None
        repeat = None

        # Check the first format: in x send y to #z. E.g. in 15 send Hi there everyone to #channel. Or: in 25 send Hey there
        regex = {
            'in': '^in\s(\d+)\ssend\s(.*?)(\sto\s\<\#([0-9]+)\>)?$',
            'at': '^at\s(\d{4}|\d{2}\:\d{2})(\son\s(.*?))?\ssend\s(.*?)(\sto\s\<\#([0-9]+)\>)?$',
            'every': '^every\s(day|hour|week)\s(from|at)\s(\d{4}|\d{2}\:\d{2})\ssend\s(.*?)(\sto\s\<\#([0-9]+)\>)?$'
        }
        if re.search(regex['in'], cmd, re.IGNORECASE):

            matches = re.findall(regex['in'], cmd, re.IGNORECASE)

            # Make sure the time in mins is valid.
            if int(matches[0][0]) <= 0:
                return await context.send(lib.get_string('remind:err:time', user.get_guild()))

            remind_time = now + (60 * int(matches[0][0]))

            message = matches[0][1]
            if lib.is_number(matches[0][3]):
                channel = int(matches[0][3])
            else:
                channel = context.message.channel.id

        # Next format to check: at hh:mm send y to #z. E.g. at 17:00 send Hello there to #channel.
        elif re.search(regex['at'], cmd, re.IGNORECASE):

            matches = re.findall(regex['at'], cmd, re.IGNORECASE)

            requested_time = matches[0][0]
            requested_date = matches[0][2] if matches[0][2] != '' else None

            # If they passed the time through with a colon, remove that.
            if ':' in requested_time:
                requested_time = requested_time.replace(':', '')

            # Now convert the time to an int.
            requested_time = int(requested_time)

            timezone = pytz.timezone(user.get_setting('timezone'))
            timezone_date = datetime.now(timezone).strftime('%d-%m-%Y') if requested_date is None else requested_date
            timezone_time = int(datetime.now(timezone).strftime('%H%M'))

            # Build the datetime object for the current date (in user's timezone) and the requested time.
            try:
                reminder_time = datetime.strptime(timezone_date + ' ' + str(requested_time), '%d-%m-%Y %H%M')
            except ValueError:
                return await context.send(lib.get_string('remind:err:date', user.get_guild()))

            # If they manually specified a date and it is in the past, send an error.
            if requested_date is not None and int(timezone.localize(reminder_time).timestamp()) <= now:
                return await context.send(lib.get_string('remind:err:date', user.get_guild()))

            # If the time they requested has already passed (but they did not specify a date), alter the date ahead by 1 day.
            if requested_time <= timezone_time:
                reminder_time += timedelta(days=1)

            # Convert it to a UTC timestamp.
            remind_time = int(timezone.localize(reminder_time).timestamp())

            message = matches[0][3]
            if lib.is_number(matches[0][5]):
                channel = int(matches[0][5])
            else:
                channel = context.message.channel.id

        elif re.search(regex['every'], cmd, re.IGNORECASE):

            matches = re.findall(regex['every'], cmd, re.IGNORECASE)

            interval = matches[0][0]
            requested_time = matches[0][2]
            message = matches[0][3]
            if lib.is_number(matches[0][5]):
                channel = int(matches[0][5])
            else:
                channel = context.message.channel.id

            # If they passed the time through with a colon, remove that.
            if ':' in requested_time:
                requested_time = requested_time.replace(':', '')

            # Check interval is valid.
            if interval not in list(self._reminder_intervals.keys()):
                return await context.send(lib.get_string('remind:err:interval', user.get_guild()))

            # Now convert the time to an int.
            requested_time = int(requested_time)

            timezone = pytz.timezone(user.get_setting('timezone'))
            timezone_date = datetime.now(timezone).strftime('%d-%m-%Y')
            timezone_time = int(datetime.now(timezone).strftime('%H%M'))

            # Build the datetime object for the current date (in user's timezone) and the requested time.
            try:
                reminder_time = datetime.strptime(timezone_date + ' ' + str(requested_time), '%d-%m-%Y %H%M')
            except ValueError:
                return await context.send(lib.get_string('remind:err:date', user.get_guild()))

            # If the time they requested has already passed (but they did not specify a date), alter the date ahead by 1 day.
            if requested_time <= timezone_time:
                reminder_time += timedelta(days=1)

            # Convert it to a UTC timestamp.
            remind_time = int(timezone.localize(reminder_time).timestamp())

            # Now get the interval time to add each time the reminder is set.
            repeat = self._reminder_intervals[interval]

        else:
            return await context.send(user.get_mention() + ', ' + lib.get_string('remind:err:format', user.get_guild()))

        # Check the channel is valid.
        if not context.guild.get_channel(channel):
            return await context.send(lib.get_string('remind:err:channel', user.get_guild()))

        # Check that the message is not too long?
        if len(message) > 255:
            return await context.send(lib.get_string('remind:err:message', user.get_guild()).format(len(message)))

        # If we get this far, we have parsed the command into variables.
        params = {
            'user': user.get_id(),
            'guild': user.get_guild(),
            'time': remind_time,
            'channel': channel,
            'message': message,
            'intervaltime': repeat
        }

        reminder = Reminder.create(params)
        if reminder:
            return await context.send(user.get_mention() + ', ' + lib.get_string('remind:created', user.get_guild()).format(
                lib.format_secs_to_days(remind_time - now))
            )


    async def run_delete(self, context, user):
        """
        Delete a reminder
        @param context:
        @param user:
        @return:
        """
        reminders = user.get_reminders()
        message = lib.get_string('remind:list', user.get_guild())

        map = {}

        x = 1
        for reminder in reminders:
            message += '**' + str(x) + '.** ' + reminder.info(context) + '\n'
            map[x] = reminder
            x += 1

        await self.split_send(context, user, message)

        # Prompt for reminder numbers to delete
        answer = await self.delete_wait_for_response(context)
        if not answer:
            return

        delete = [x.strip() for x in answer.split(',')]
        deleted = 0

        # If we say 'all' we want to delete all of them so get all of the numbers
        if answer.lower() == 'all':
            delete = range(x)

        for d in delete:
            number = lib.is_number(d)
            if number and number in list(map.keys()):
                map[number].delete()
                deleted += 1

        return await context.send(user.get_mention() + ', ' + lib.get_string('remind:deleted', user.get_guild()).format(deleted))


    async def delete_wait_for_response(self, context):
        """
        Wait for the delete response saying which reminders to delete
        @return:
        """

        argument = {'prompt': lib.get_string('remind:delete', context.guild.id)}
        response = await self.prompt(context, argument, True, self.PROMPT_TIMEOUT)
        if not response:
            return False

        response = response.content.lower()

        # If there response was one of the exit commands, then stop.
        if response in ('exit', 'quit', 'cancel'):
            return False

        return response

    async def run_list(self, context, user):
        """
        List the user's reminders
        @param context:
        @param user:
        @return:
        """
        reminders = user.get_reminders()
        message = lib.get_string('remind:list', user.get_guild())

        x = 1
        for reminder in reminders:
            message += '**' + str(x) + '.** ' + reminder.info(context) + '\n'
            x += 1

        return await self.split_send(context, user, message)


def setup(bot):
    bot.add_cog(Remind(bot))