import discord, lib, pytz, time
from datetime import datetime, timezone, timedelta
from discord.ext import commands
from structures.db import Database
from structures.event import Event
from structures.project import Project
from structures.task import Task
from structures.user import User
from structures.wrapper import CommandWrapper
from structures.guild import Guild

from pprint import pprint

class EventCommand(commands.Cog, CommandWrapper):

    PROMPT_TIMEOUT = 60

    def __init__(self, bot):
        self.bot = bot
        self.__db = Database.instance()
        self._supported_commands = ['create', 'rename', 'desc', 'description', 'img', 'image', 'delete', 'schedule', 'unschedule', 'start', 'end', 'time', 'left', 'update', 'me', 'top', 'leaderboard', 'info']
        self._arguments = [
            {
                'key': 'cmd',
                'prompt': 'event:argument:cmd',
                'required': True,
                'check': lambda content : content in self._supported_commands,
                'error': 'event:err:argument:cmd'
            }
        ]

    @commands.command(name="event")
    @commands.guild_only()
    async def event(self, context, cmd=None, *opts):
        """
        event create My Event Title - Create an event called "My Event Title" | Permissions required: [MANAGE_MESSAGES],
        event rename My New Event Title - Rename event to "My New Event Title" | Permissions required: [MANAGE_MESSAGES],
        event description This is the description - Set the description of the event to "This is the description" | Permissions required: [MANAGE_MESSAGES],
        event image https://i.imgur.com/tJtAdNs.png - Set the thumbnail image for the event to the image URL specified | Permissions required: [MANAGE_MESSAGES],
        event delete - Deletes the current event | Permissions required: [MANAGE_MESSAGES],
        event schedule - Starts the event scheduling wizard. Please pay attention to the date/time formats, they must be entered exactly as the bot expects | Permissions required: [MANAGE_MESSAGES],
        event unschedule - Removes the schedule from the event
        event start - Manually starts the current event | Permissions required: [MANAGE_MESSAGES],
        event end - Manually ends the current event | Permissions required: [MANAGE_MESSAGES],
        event time - Checks how long until the event ends or starts,
        event update 500 - Updates your event word count to 500 total words,
        event me - Checks your current event word count,
        event top - Checks the word count leaderboard for the current event
        event info - Checks the information/status of the event
        """
        if not Guild(context.guild).is_command_enabled('event'):
            return await context.send(lib.get_string('err:disabled', context.guild.id))

        # Check the arguments were all supplied and get a dict list of them and their values, after any prompts
        args = await self.check_arguments(context, cmd=cmd)
        if not args:
            return

        # Overwrite the variables passed in, with the values from the prompt and convert to lowercase
        cmd = args['cmd'].lower()

        if cmd == 'create':
            return await self.run_create(context, opts)
        elif cmd == 'delete':
            return await self.run_delete(context)
        elif cmd == 'rename':
            return await self.run_rename(context, opts)
        elif cmd == 'desc' or cmd == 'description':
            return await self.run_set(context, 'description', opts)
        elif cmd == 'img' or cmd == 'image':
            return await self.run_set(context, 'image', opts)
        elif cmd == 'colour' or cmd == 'color':
            return await self.run_set(context, 'colour', opts)
        elif cmd == 'start':
            return await self.run_start(context)
        elif cmd == 'end':
            return await self.run_end(context)
        elif cmd == 'time' or cmd == 'left':
            return await self.run_time(context)
        elif cmd == 'update':
            return await self.run_update(context, opts)
        elif cmd == 'me':
            return await self.run_me(context)
        elif cmd == 'schedule':
            return await self.run_schedule(context)
        elif cmd == 'unschedule':
            return await self.run_unschedule(context)
        elif cmd == 'info':
            return await self.run_info(context)
        elif cmd == 'top' or cmd == 'leaderboard':
            return await self.run_top(context, opts)

    async def run_top(self, context, number_of_users):
        """
        Get the leaderboard of words written for this event for up to {number} of users
        :param context:
        :param number_of_users:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)

        # First try and get the event as if its running
        event = Event.get_by_guild(user.get_guild())

        # If that fails, get the last run one
        if event is None:
            event = Event.get_by_guild(user.get_guild(), include_ended=True)

        # If there is still not one, then just stop
        if event is None:
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        if not number_of_users:
            number_of_users = event.DEFAULT_LEADERBOARD_LIMIT
        else:
            number_of_users = lib.is_number(number_of_users[0])
        if number_of_users is False or number_of_users <= 0 or number_of_users > event.UPPER_LEADERBOARD_LIMIT:
            return await context.send(user.get_mention() + ', ' + lib.get_string('err:validnumberofusers', user.get_guild()))

        event.set_context(context)
        event.set_guild_object(context.guild)

        return await context.send(embed=await event.get_leaderboard(number_of_users))

    async def run_unschedule(self, context):
        """
        Unschedule the event
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        event = Event.get_by_guild(user.get_guild())

        # Do they have the permissions to rename an event?
        self.check_permissions(context)

        # Make sure the event is running
        if event is None:
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        # Unschedule the event
        event.set_startdate(None)
        event.set_enddate(None)
        event.save()

        # Remove any tasks we already had saved for this event.
        Task.cancel('event', event.get_id())

        return await context.send(user.get_mention() + ', ' + lib.get_string('event:unscheduled', user.get_guild()).format(event.get_title()))

    async def run_schedule(self, context):
        """
        Schedule the event to start and end at a specific datetime
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        event = Event.get_by_guild(user.get_guild())

        # Do they have the permissions to rename an event?
        self.check_permissions(context)

        # Make sure the event is running
        if event is None:
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        # Make sure the event is running
        if event.is_running():
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:alreadyrunning', user.get_guild()))

        # Do they have a timezone set in their user settings?
        user_timezone = user.get_setting('timezone')
        if user_timezone is None:
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:timezonenotset', user.get_guild()))

        timezone = pytz.timezone(user_timezone)
        time = datetime.now(timezone).strftime('%H:%M:%S')
        offset = datetime.now(timezone).strftime('%z')

        # Print the pre-schedule information to check their timezone is correct.
        await context.send(user.get_mention() + ', ' + lib.get_string('event:preschedule', user.get_guild()).format(user_timezone, time, offset))

        # We now have various stages to go through, so we loop through the stages, ask the question and store the user input as the answer.
        answers = []

        # Stage 1 - Start date
        answer = await self.run_stage_one(context)
        if not answer:
            return
        answers.append({'stage': 1, 'answer': answer})

        # Stage 2 - Start time
        answer = await self.run_stage_two(context)
        if not answer:
            return
        answers.append({'stage': 2, 'answer': answer})

        # Stage 3 - End date
        answer = await self.run_stage_three(context)
        if not answer:
            return
        answers.append({'stage': 3, 'answer': answer})

        # Stage 4 - End time
        answer = await self.run_stage_four(context)
        if not answer:
            return
        answers.append({'stage': 4, 'answer': answer})

        # Stage 5 - Confirmation
        answer = await self.run_stage_five(context, answers)
        if not answer:
            return
        answers.append({'stage': 5, 'answer': answer})

        # Now run the checks to make sure the end date is later than start date, etc...
        check = await self.check_answers(context, answers)
        if not check:
            return

        # Now convert those start and end times to UTC timestamps
        start = datetime.strptime(lib.find(answers, 'stage', 1)['answer'] + ' ' + lib.find(answers, 'stage', 2)['answer'], '%d-%m-%Y %H:%M')
        end = datetime.strptime(lib.find(answers, 'stage', 3)['answer'] + ' ' + lib.find(answers, 'stage', 4)['answer'], '%d-%m-%Y %H:%M')

        adjusted_start = int(timezone.localize(start).timestamp())
        adjusted_end = int(timezone.localize(end).timestamp())

        # Schedule the event with those timestamps
        event.set_startdate(adjusted_start)
        event.set_enddate(adjusted_end)
        event.set_channel(context.message.channel.id)
        event.save()

        # Remove any tasks we already had saved for this event.
        Task.cancel('event', event.get_id())

        # Schedule the tasks to run at those times.
        Task.schedule(Event.TASKS['start'], event.get_start_time(), 'event', event.get_id())
        Task.schedule(Event.TASKS['end'], event.get_end_time(), 'event', event.get_id())

        return await context.send(user.get_mention() + ', ' + lib.get_string('event:scheduled', user.get_guild()).format(event.get_title(), start, end))


    async def check_answers(self, context, answers):
        """
        Run the checks on their answers to make sure their values are valid
        :param answers:
        :return:
        """
        now = datetime.today()
        start = datetime.strptime(lib.find(answers, 'stage', 1)['answer'] + ' ' + lib.find(answers, 'stage', 2)['answer'], '%d-%m-%Y %H:%M')
        end = datetime.strptime(lib.find(answers, 'stage', 3)['answer'] + ' ' + lib.find(answers, 'stage', 4)['answer'], '%d-%m-%Y %H:%M')

        # Check that the end date is later than the start date.
        if start > end:
            await context.send( context.message.author.mention + ', ' + lib.get_string('event:err:dates', context.guild.id))
            return False

        # Check that dates are in the future
        if start < now or end < now:
            await context.send(context.message.author.mention + ', ' + lib.get_string('event:err:dates:past', context.guild.id))
            return False

        return True

    async def run_stage_one(self, context):
        """
        Ask the stage 1 question - Start date
        :param context:
        :return:
        """
        argument = {'prompt': lib.get_string('event:schedule:question:1', context.guild.id), 'check': lambda resp: lib.is_valid_datetime(resp, '%d-%m-%Y'), 'error': 'event:err:invaliddate'}
        response = await self.prompt(context, argument, True, self.PROMPT_TIMEOUT)
        if not response:
            return False

        response = response.content.lower()

        # If there response was one of the exit commands, then stop.
        if response in ('exit', 'quit', 'cancel'):
            return False

        # We got a response, now do we need to check the type or do any extra content checks?
        if not await self.check_content(argument, response, context):
            # If it didn't meet the check conditions, try again.
            return await self.run_stage_one(context)

        return response

    async def run_stage_two(self, context):
        """
        Ask the stage 2 question - Start time
        :param context:
        :return:
        """
        argument = {'prompt': lib.get_string('event:schedule:question:2', context.guild.id), 'check': lambda resp: lib.is_valid_datetime(resp, '%H:%M'), 'error': 'event:err:invalidtime'}
        response = await self.prompt(context, argument, True, self.PROMPT_TIMEOUT)
        if not response:
            return False

        response = response.content.lower()

        # If there response was one of the exit commands, then stop.
        if response in ('exit', 'quit', 'cancel'):
            return False

        # We got a response, now do we need to check the type or do any extra content checks?
        if not await self.check_content(argument, response, context):
            # If it didn't meet the check conditions, try again.
            return await self.run_stage_two(context)

        return response

    async def run_stage_three(self, context):
        """
        Ask the stage 3 question - End date
        :param context:
        :return:
        """
        argument = {'prompt': lib.get_string('event:schedule:question:3', context.guild.id), 'check': lambda resp: lib.is_valid_datetime(resp, '%d-%m-%Y'), 'error': 'event:err:invaliddate'}
        response = await self.prompt(context, argument, True, self.PROMPT_TIMEOUT)
        if not response:
            return False

        response = response.content.lower()

        # If there response was one of the exit commands, then stop.
        if response in ('exit', 'quit', 'cancel'):
            return False

        # We got a response, now do we need to check the type or do any extra content checks?
        if not await self.check_content(argument, response, context):
            # If it didn't meet the check conditions, try again.
            return await self.run_stage_three(context)

        return response

    async def run_stage_four(self, context):
        """
        Ask the stage 4 question - End time
        :param context:
        :return:
        """
        argument = {'prompt': lib.get_string('event:schedule:question:4', context.guild.id), 'check': lambda resp: lib.is_valid_datetime(resp, '%H:%M'), 'error': 'event:err:invalidtime'}
        response = await self.prompt(context, argument, True, self.PROMPT_TIMEOUT)
        if not response:
            return False

        response = response.content.lower()

        # If there response was one of the exit commands, then stop.
        if response in ('exit', 'quit', 'cancel'):
            return False

        # We got a response, now do we need to check the type or do any extra content checks?
        if not await self.check_content(argument, response, context):
            # If it didn't meet the check conditions, try again.
            return await self.run_stage_four(context)

        return response

    async def run_stage_five(self, context, answers):
        """
        Ask the stage 5 question - Confirmation
        :param context:
        :return:
        """
        prompt = lib.get_string('event:schedule:question:5', context.guild.id).format(
            lib.find(answers, 'stage', 1)['answer'] + ', ' + lib.find(answers, 'stage', 2)['answer'],
            lib.find(answers, 'stage', 3)['answer'] + ', ' + lib.find(answers, 'stage', 4)['answer']
        )

        argument = {'prompt': prompt, 'check': lambda resp: resp in ('yes', 'y', 'no', 'n'),
                    'error': 'err:yesorno'}
        response = await self.prompt(context, argument, True, self.PROMPT_TIMEOUT)
        if not response:
            return False

        response = response.content.lower()

        # If there response was one of the exit commands, then stop.
        if response in ('exit', 'quit', 'cancel'):
            return False

        # We got a response, now do we need to check the type or do any extra content checks?
        if not await self.check_content(argument, response, context):
            # If it didn't meet the check conditions, try again.
            return await self.run_stage_five(context)

        # If they said no, tell them to start it again.
        if response in ('no', 'n'):
            await context.send(lib.get_string('event:schedule:restart', context.guild.id))
            return False

        return response in ('yes', 'y')

    async def run_info(self, context):
        """
        Get the event information embedded message
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        event = Event.get_by_guild(user.get_guild())
        config = lib.get('./settings.json')

        # Make sure there is an event
        if event is None:
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        # Work out which timezone to use when displaying the start and end dates.
        start_date = lib.get_string('na', user.get_guild())
        end_date = lib.get_string('na', user.get_guild())
        user_timezone = user.get_setting('timezone')
        if not user_timezone:
            user_timezone = 'UTC'

        timezone = pytz.timezone(user_timezone)

        # Is it scheduled with start and end dates?
        if event.is_scheduled():
            start = datetime.fromtimestamp(event.get_start_time())
            end = datetime.fromtimestamp(event.get_end_time())
            start_date = start.astimezone(timezone).strftime('%d-%m-%Y %H:%M:%S') + ' ('+user_timezone+')'
            end_date = end.astimezone(timezone).strftime('%d-%m-%Y %H:%M:%S') + ' ('+user_timezone+')'

        # Get the running status
        if event.is_running():
            status = lib.get_string('event:started', user.get_guild())
        else:
            status = lib.get_string('event:notyetstarted', user.get_guild())

        # Get the number of users in the event and how many words they have written in it so far
        writers = len(event.get_users())
        words = event.get_total_wordcount()

        # Get the description of the event and add to the end of the status, or just display the status if the description is empty
        description = event.get_description()
        if description and len(description) > 0:
            description = status + '\n\n' + description
        else:
            description = status

        # Get the thumbnail image to use
        image = event.get_image()
        if not image or len(image) == 0:
            image = config.avatar

        # Build the embedded message.
        embed = discord.Embed(title=event.get_title(), color=event.get_colour(), description=description)
        embed.set_thumbnail(url=image)
        embed.add_field(name=lib.get_string('event:startdate', user.get_guild()), value=start_date, inline=False)
        embed.add_field(name=lib.get_string('event:enddate', user.get_guild()), value=end_date, inline=False)
        embed.add_field(name=lib.get_string('event:numwriters', user.get_guild()), value=str(writers), inline=True)
        embed.add_field(name=lib.get_string('event:numwords', user.get_guild()), value=str(words), inline=True)

        # Send the message
        return await context.send(embed=embed)

    async def run_me(self, context):
        """
        Check your own word count for the event so far
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        event = Event.get_by_guild(user.get_guild())

        # Make sure the event is running
        if event is None or not event.is_running():
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        words = event.get_wordcount(user.get_id())
        return await context.send(user.get_mention() + ', ' + lib.get_string('event:wordcount', user.get_guild()).format(event.get_title(), words))

    async def run_update(self, context, amount):
        """
        Update the user's word count on the event
        :param context:
        :param amount:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        event = Event.get_by_guild(user.get_guild())

        amount = lib.is_number(amount[0])
        if amount is False or amount < 0:
            return await context.send(user.get_mention() + ', ' + lib.get_string('err:validamount', user.get_guild()))

        # Make sure the event is running
        if event is None or not event.is_running():
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        event.update_wordcount(user.get_id(), amount)
        return await context.send(user.get_mention() + ', ' + lib.get_string('event:updated', user.get_guild()).format(event.get_title(), amount))

    async def run_time(self, context):
        """
        Check how much time is left in the event
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        event = Event.get_by_guild(user.get_guild())
        now = int(time.time())

        # Make sure the event exists
        if event is None or not event.is_valid():
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        # Is the event scheduled to start, but has not yet started?
        if not event.is_running() and event.is_scheduled():
            left = lib.format_secs_to_days(event.get_start_time() - now)
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:timetostart', user.get_guild()).format(left))

        # If the event is not running and it is NOT scheduled, then we don't know what time it will start.
        elif not event.is_running():
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        # At this point, the event must be running. If it is scheduled, then we can get the time left from the end time. Otherwise, we don't know.
        elif event.is_scheduled():
            left = lib.format_secs_to_days(event.get_end_time() - now)
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:timeleft', user.get_guild()).format(left))

        else:
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:noendtime', user.get_guild()))


    async def run_end(self, context):
        """
        End the event now
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)

        # Do they have the permissions to end an event?
        self.check_permissions(context)

        event = Event.get_by_guild(user.get_guild())
        if event is None or not event.is_running():
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        event.set_context(context)
        event.set_guild_object(context.guild)

        # Remove any tasks we already had saved for this event.
        Task.cancel('event', event.get_id())

        return await event.end()

    async def run_start(self, context):
        """
        Start the event now
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)

        # Do they have the permissions to start an event?
        self.check_permissions(context)

        event = Event.get_by_guild(user.get_guild())
        if event is None or event.is_running():
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:cannotstart', user.get_guild()))

        event.set_context(context)
        return await event.start()

    async def run_set(self, context, type, opts):
        """
        Set the value of something for the event, such as description or image url
        :param context:
        :param type:
        :param opts:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)

        # Do they have the permissions to set an event option?
        self.check_permissions(context)

        # Check if there is an event running
        event = Event.get_by_guild(user.get_guild())
        if event is None or not event.is_valid():
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        value = " ".join(opts[0:])

        if type == 'description':
            event.set_description(value)
        elif type == 'image':
            if len(value) > 255:
                return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:img', user.get_guild()))
            event.set_image(value)
        elif type == 'colour':
            event.set_colour(value)

        # Save the changes
        event.save()

        return await context.send(user.get_mention() + ', ' + lib.get_string('event:set', user.get_guild()).format(type, value))

    async def run_rename(self, context, opts):
        """
        Rename the event
        :param context:
        :param opts:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)

        # Do they have the permissions to rename an event?
        self.check_permissions(context)

        # Check if there is an event running
        event = Event.get_by_guild(user.get_guild())
        if event is None or not event.is_valid():
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        # Get the title out of the arguments
        title = " ".join(opts[0:])

        # Make sure they specified a title.
        if len(title) == 0 or len(title) > 255:
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:rename:title', user.get_guild()))

        # Create the event
        event.set_title(title)
        event.save()
        return await context.send(user.get_mention() + ', ' + lib.get_string('event:renamed', user.get_guild()).format(title))

    async def run_delete(self, context):
        """
        Delete the event on this server
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)

        # Do they have the permissions to delete an event?
        self.check_permissions(context)

        # Check if there is an event running
        event = Event.get_by_guild(user.get_guild())
        if event is None or not event.is_valid():
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:noexists', user.get_guild()))

        # Make a fake prompt to wait for confirmation.
        argument = {'prompt': lib.get_string('event:deletesure', user.get_guild()), 'check': lambda resp: resp.lower() in ('y', 'yes', 'n', 'no')}

        response = await self.prompt(context, argument, True)
        if not response:
            return

        response = response.content

        # If they confirm, then delete the event.
        if response.lower() in ('y', 'yes'):

            event.delete()

            # Remove any tasks we already had saved for this event.
            Task.cancel('event', event.get_id())

            output = lib.get_string('event:deleted', user.get_guild()).format(event.get_title())

        else:
            # Otherwise, just print 'OK'
            output = 'OK'

        await context.send(context.message.author.mention + ', ' + output)


    async def run_create(self, context, opts):
        """
        Create an event on the server
        :param context:
        :param opts:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)

        # Do they have the permissions to create an event?
        self.check_permissions(context)

        # Get the title out of the arguments
        title = " ".join(opts[0:])

        # Check if there is already an event running
        event = Event.get_by_guild(user.get_guild())
        if event is not None:
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:alreadyexists', user.get_guild()))

        # Make sure they specified a title.
        if len(title) == 0 or len(title) > 255:
            return await context.send(user.get_mention() + ', ' + lib.get_string('event:err:title', user.get_guild()))

        # Create the event
        Event.create(guild=user.get_guild(), channel=context.message.channel.id, title=title)
        return await context.send(user.get_mention() + ', ' + lib.get_string('event:created', user.get_guild()).format(title))

    def check_permissions(self, context):
        """
        Reusable method to check the user has the correct permissions, depending on what they are trying to do
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context=context, bot=self.bot)
        permissions = context.message.author.permissions_in(context.message.channel)
        if permissions.manage_messages is not True and not user.is_owner():
            raise commands.errors.MissingPermissions(['manage_messages'])

def setup(bot):
    bot.add_cog(EventCommand(bot))