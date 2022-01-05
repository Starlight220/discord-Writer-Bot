import discord, lib, time
from datetime import datetime
from discord.ext import commands
from structures.generator import NameGenerator
from structures.project import Project
from structures.sprint import Sprint
from structures.guild import Guild
from structures.task import Task
from structures.user import User
from structures.wrapper import CommandWrapper

class SprintCommand(commands.Cog, CommandWrapper):

    DEFAULT_LENGTH = 20 # 20 minutes
    DEFAULT_DELAY = 2 # 2 minutes
    MAX_LENGTH = 60 # 1 hour
    MAX_DELAY = 60 * 24 # 24 hours
    WPM_CHECK = 150 # If WPM exceeds this amount, check that the user meant to submit that many words

    def __init__(self, bot):
        self.bot = bot
        self._supported_commands = ['start', 'for', 'time', 'cancel', 'end', 'join', 'leave', 'wc', 'declare', 'pb', 'notify', 'forget', 'project', 'status', 'in', 'purge']
        self._arguments = [
            {
                'key': 'cmd',
                'prompt': 'sprint:argument:cmd',
                'required': True,
                'check': lambda content : content in self._supported_commands,
                'error': 'sprint:err:cmd'
            },
            {
                'key': 'opt1',
                'required': False,
            },
            {
                'key': 'opt2',
                'required': False,
            },
            {
                'key': 'opt3',
                'required': False,
            }
        ]

    @commands.command(name="sprint", aliases=['spring'])
    @commands.guild_only()
    async def sprint(self, context, cmd=None, opt1=None, opt2=None, opt3=None):
        """
        Write with your friends and see who can write the most in the time limit!
        When choosing a length and start delay, there are maximums of 60 minutes length of sprint, and 24 hours delay until sprint begins.
        NOTE: The bot checks for sprint changes every 30 seconds, so your start/end times might be off by +-30 seconds or so.

        Run `help sprint` for more extra information, including any custom server settings related to sprints.

        Examples:
            `sprint start` - Quickstart a sprint with the default settings.
            `sprint for 20 in 3` - Schedules a sprint for 20 minutes, to start in 3 minutes.
            `sprint cancel` - Cancels the current sprint. This can only be done by the person who created the sprint, or any users with the MANAGE_MESSAGES permission.
            `sprint join` - Joins the current sprint.
            `sprint join 100` - Joins the current sprint, with a starting word count of 100.
            `sprint join 100 sword` - Joins the current sprint, with a starting word count of 100 and sets your sprint to count towards your Project with the shortname "sword" (See: Projects for more info).
            `sprint join same` - Use the keyword `same` to join the sprint using the same Project and Final Word Count from your most recent sprint.
            `sprint leave` - Leaves the current sprint.
            `sprint project sword` - Sets your sprint to count towards your Project with the shortname "sword" (See: Projects for more info).
            `sprint wc 250` - Declares your final word count at 250.
            `sprint time` - Displays the time left in the current sprint.
            `sprint pb` - Displays your personal best wpm from sprints on this server. Run sprint pb reset to reset your personal best to 0 on the current server.
            `sprint notify` - You will be notified when someone starts a new sprint.
            `sprint forget` - You will no longer be notified when someone starts a new sprint.
            `sprint status` - Shows you your current word count on the sprint.

        **Sprint Tips**
        If you join the sprint with a starting word count, remember to declare your total word count at the end, not just the amount of words you wrote in the sprint.
        e.g. If you joined with 1000 words, and during the sprint you wrote another 500 words, the final word count you should declare would be 1500
        """
        user = User(context.message.author.id, context.guild.id, context)

        if not Guild(context.guild).is_command_enabled('sprint'):
            return await context.send(lib.get_string('err:disabled', context.guild.id))

        # Check the arguments are valid
        args = await self.check_arguments(context, cmd=cmd, opt1=opt1, opt2=opt2, opt3=opt3)
        if not args:
            return

        # Convert cmd to lowercase
        cmd = args['cmd'].lower()

        # Start a sprint
        if cmd == 'start':
            return await self.run_start(context)

        elif cmd == 'for':

            length = opt1

            # If the second option is invalid, display an error message
            if opt2 is not None and opt2.lower() not in ['now', 'in', 'at']:
                return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:for:unknown', user.get_guild()))

            # If they left off the last argument and just said `sprint for 20` then assume they mean now.
            if opt2 is None:
                opt2 = 'now'

            # Get the delay they want before starting the sprint.
            if opt2.lower() == 'now':
                delay = 0
            elif opt2.lower() == 'in':
                delay = opt3
            elif opt2.lower() == 'at':

                # Make sure the user has set their timezone, otherwise we can't calculate it.
                timezone = user.get_setting('timezone')
                user_timezone = lib.get_timezone(timezone)
                if not user_timezone:
                    return await context.send(user.get_mention() + ', ' + lib.get_string('err:notimezone', user.get_guild()))

                # If they are doing `sprint for 20 at :15` for example, then opt3 must be set in the format '.00'.
                start = int(opt3[1:]) if (isinstance(opt3, str) and opt3.startswith('.') and len(opt3) == 3) else opt3
                if not isinstance(start, int) or start < 0 or start >= 60:
                    return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:for:at', user.get_guild()))

                # Now using their timezone and the minute they requested, calculate when that should be.
                user_timezone = lib.get_timezone(timezone)
                delay = (60 + start - datetime.now(user_timezone).minute) % 60

            return await self.run_start(context, length, delay)

        elif cmd == "in":

            delay = opt1

            # If the second option is invalid, display an error message
            if opt2 is not None and opt2.lower() != "for":
                return await context.send(
                    user.get_mention()
                    + ", "
                    + lib.get_string("sprint:err:in:unknown", user.get_guild())
                )

            # Get the length they want before starting the sprint.
            # If they left off the last argument and just said `sprint for 20` then assume they mean now.
            if opt2 is None:
                length = self.DEFAULT_LENGTH
            elif opt2.lower() == "for":
               length = opt3

            return await self.run_start(context, length, delay)

        elif cmd == 'cancel':
            return await self.run_cancel(context)

        elif cmd == 'notify':
            return await self.run_notify(context)

        elif cmd == 'forget':
            return await self.run_forget(context)

        elif cmd == 'time':
            return await self.run_time(context)

        elif cmd == 'leave':
            return await self.run_leave(context)

        elif cmd == 'join':
            return await self.run_join(context, opt1, opt2)

        elif cmd == 'pb':
            return await self.run_pb(context)

        elif cmd == 'status':
            return await self.run_status(context)

        elif cmd == 'wc' or cmd == 'declare':
            return await self.run_declare(context, opt1)

        elif cmd == 'end':
            return await self.run_end(context)

        elif cmd == 'project':
            return await self.run_project(context, opt1)

        elif cmd == 'purge':
            return await self.run_purge(context)

    async def run_purge(self, context):
        """
        Purge any users who asked for notifications but aren't on the server any more.
        @param context:
        @return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        purged = await Sprint.purge_notifications(context)
        if purged > 0:
            return await context.send(lib.get_string('sprint:purged', user.get_guild()).format(purged))
        else:
            return await context.send(lib.get_string('sprint:purged:none', user.get_guild()))

    async def run_project(self, context, shortname):
        """
        Set the project the user wants to sprint in.
        :param context:
        :param shortname:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        sprint = Sprint(user.get_guild())

        # If there is no active sprint, then just display an error
        if not sprint.exists():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:noexists', user.get_guild()))

        # If the user is not sprinting, then again, just display that error
        if not sprint.is_user_sprinting(user.get_id()):
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:notjoined', user.get_guild()))

        # Make sure the project exists.
        shortname = shortname.lower() if shortname is not None else None
        project = user.get_project(shortname)
        if not project:
            return await context.send(user.get_mention() + ', ' + lib.get_string('project:err:noexists', user.get_guild()).format(shortname))

        sprint.set_project(project.get_id(), user.get_id())
        return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:project', user.get_guild()).format(project.get_title()))

    async def run_end(self, context):
        """
        Manually force the sprint to end (if the cron hasn't posted the message) and ask for final word counts
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        sprint = Sprint(user.get_guild())

        # If there is no active sprint, then just display an error
        if not sprint.exists():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:noexists', user.get_guild()))

        # If they do not have permission to cancel this sprint, display an error
        if int(sprint.get_createdby()) != user.get_id() and context.message.author.permissions_in(context.message.channel).manage_messages is not True:
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:cannotend', user.get_guild()))

        # If the sprint hasn't started yet, it can't be ended.
        if not sprint.has_started():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:notstarted', user.get_guild()))

        # Change the end reference to now, otherwise wpm calculations will be off, as it will use the time in the future when it was supposed to end.
        sprint.update_end_reference(int(time.time()))

        # Since we are forcing the end, we should cancel any pending tasks for this sprint
        Task.cancel('sprint', sprint.get_id())

        # We need to set the bot into the sprint object, as we will need it when trying to get the guild object
        sprint.set_bot(self.bot)
        return await sprint.end(context)

    async def run_declare(self, context, amount=None):
        """
        Declare user's current word count for the sprint
        :param context:
        :param amount:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        sprint = Sprint(user.get_guild())

        # If there is no active sprint, then just display an error
        if not sprint.exists():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:noexists', user.get_guild()))

        # If the user is not sprinting, then again, just display that error
        if not sprint.is_user_sprinting(user.get_id()):
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:notjoined', user.get_guild()))

        # If the sprint hasn't started yet, display error
        if not sprint.has_started():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:notstarted', user.get_guild()))

        # Get the user's sprint info
        user_sprint = sprint.get_user_sprint(user.get_id())

        # If they joined without a word count, they can't add one.
        if user_sprint['sprint_type'] == Sprint.SPRINT_TYPE_NO_WORDCOUNT:
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:nonwordcount', user.get_guild()))

        # Did they enter something for the amount?
        if amount is None:
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:amount', user.get_guild()))

        # Are they trying to do a calculation instead of declaring a number?
        if amount[0] == '+' or amount[0] == '-':

            # Set the calculation variable to True so we know later on that it was not a proper declaration
            calculation = True

            # Convert the amount string to an int
            amount = int(amount)

            # Add that to the current word count, to get the new value
            new_amount = user_sprint['current_wc'] + amount

        else:
            calculation = False
            new_amount = amount

        # Make sure the amount is now a valid number
        if not lib.is_number(new_amount):
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:amount', user.get_guild()))

        # Just make sure the new_amount is defintely an int
        new_amount = int(new_amount)

        # If the declared value is less than they started with and it is not a calculation, then that is an error.
        if new_amount < int(user_sprint['starting_wc']) and not calculation:
            diff = user_sprint['current_wc'] - new_amount
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:wclessthanstart', user.get_guild()).format(new_amount, user_sprint['starting_wc'], diff))

        # Is the sprint finished? If so this will be an ending_wc declaration, not a current_wc one.
        col = 'ending' if sprint.is_finished() else 'current'

        # Before we actually update it, if the WPM is huge and most likely an error, just check with them if they meant to put that many words.
        written = new_amount - int(user_sprint['starting_wc'])
        seconds = int(sprint.get_end_reference()) - user_sprint['timejoined']
        wpm = Sprint.calculate_wpm(written, seconds)

        # Does the user have a configured setting for max wpm to check?
        max_wpm = user.get_setting('maxwpm')
        if not max_wpm:
            max_wpm = self.WPM_CHECK

        if wpm > int(max_wpm):

            # Make a fake prompt to wait for confirmation.
            argument = {'prompt': lib.get_string('sprint:wpm:sure', user.get_guild()).format(written, wpm),
                        'check': lambda resp: resp.lower() in ('y', 'yes', 'n', 'no')}

            response = await self.adhoc_prompt(context, argument, True)

            # If they confirm, then delete the event.
            if response is False or response.content.lower() in ('n', 'no'):
                return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:declareagain', user.get_guild()))

        sprint.lock.acquire()
        # Update the user's sprint record
        arg = {col: new_amount}
        sprint.update_user(user.get_id(), **arg)

        # Reload the user sprint info
        user_sprint = sprint.get_user_sprint(user.get_id())

        # Which value are we displaying?
        wordcount = user_sprint['ending_wc'] if sprint.is_finished() else user_sprint['current_wc']
        written = int(wordcount) - int(user_sprint['starting_wc'])

        await context.send(user.get_mention() + ', ' + lib.get_string('sprint:declared', user.get_guild()).format(wordcount, written))

        # Is the sprint now over and has everyone declared?
        if sprint.is_finished() and sprint.is_declaration_finished():
            Task.cancel('sprint', sprint.get_id())
            sprint.lock.release()
            await sprint.complete(context)
        else:
            sprint.lock.release()

    async def run_status(self, context):
        """
        Get the user's status in this sprint
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        sprint = Sprint(user.get_guild())

        # If there is no active sprint, then just display an error
        if not sprint.exists():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:noexists', user.get_guild()))

        # If the user is not sprinting, then again, just display that error
        if not sprint.is_user_sprinting(user.get_id()):
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:notjoined', user.get_guild()))

        # If the sprint hasn't started yet, display error
        if not sprint.has_started():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:notstarted', user.get_guild()))

        # If they are sprinting, then display their current status.
        user_sprint = sprint.get_user_sprint(user.get_id())

        # Build the variables to be passed into the status string
        now = int(time.time())
        current = user_sprint['current_wc']
        written = current - user_sprint['starting_wc']
        seconds = now - user_sprint['timejoined']
        elapsed = round(seconds / 60, 1)
        wpm = Sprint.calculate_wpm(written, seconds)
        left = round((sprint.get_end() - now) / 60, 1)

        return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:status', user.get_guild()).format(current, written, elapsed, wpm, left))

    async def run_pb(self, context):
        """
        Get the user's personal best for sprinting
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        record = user.get_record('wpm')

        if record is None:
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:pb:none', user.get_guild()))
        else:
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:pb', user.get_guild()).format(int(record)))


    async def run_leave(self, context):
        """
        Leave the sprint
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        sprint = Sprint(user.get_guild())

        # If there is no active sprint or the user is not joined to it, display an error
        if not sprint.exists() or not sprint.is_user_sprinting(user.get_id()):
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:notjoined', user.get_guild()))

        # Remove the user from the sprint
        sprint.leave(user.get_id())

        await context.send(user.get_mention() + ', ' + lib.get_string('sprint:leave', user.get_guild()))

        # If there are now no users left, cancel the whole sprint
        if len(sprint.get_users()) == 0:

            # Cancel the sprint
            sprint.cancel(context)

            # Decrement sprints_started stat for whoever started this one
            creator = User(sprint.get_createdby(), sprint.get_guild())
            creator.add_stat('sprints_started', -1)

            # Display a message letting users know
            return await context.send( lib.get_string('sprint:leave:cancelled', user.get_guild()) )


    async def run_join(self, context, arg1=None, arg2=None):
        """
        Join the sprint, with an optional starting word count and project shortname
        :param opt1: Argument 1 of the join command
        :param opt2: Argument 2 of the join command
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        sprint = Sprint(user.get_guild())
        project_id = None
        starting_wc = None
        sprint_type = None

        # If there is no active sprint, then just display an error
        if not sprint.exists():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:noexists', user.get_guild()))

        # Are we using the `same` keyword?
        if arg1 == "same":

            # Okay, check for their most recent sprint record
            most_recent = user.get_most_recent_sprint(sprint)
            if most_recent is not None:
                starting_wc = most_recent['ending_wc']
                project_id = most_recent['project']
                sprint_type = most_recent['sprint_type']

            # Can't use the second argument in this case.
            arg2 = None

        # Are we doing a no wordcount sprint? E.g. we are sprinting or using the functionality for something else.
        elif arg1 in ["edit", "non-wc"]:

            sprint_type = Sprint.SPRINT_TYPE_NO_WORDCOUNT

            # Can't use the second argument in this case.
            arg2 = None

        else:
            # Convert starting_wc to int if we can
            starting_wc = lib.is_number(arg1)

        # If the starting_wc is still False at this point, just set it to 0
        if not starting_wc:
            starting_wc = 0

        # If the user is already sprinting, then just update their starting wordcount
        if sprint.is_user_sprinting(user.get_id()):

            # Update the sprint_users record. We set their current_wc to the same as starting_wc here, otherwise if they join with, say 50 and their current remains 0
            # then if they run a status, or in the ending calculations, it will say they wrote -50.
            sprint.update_user(user.get_id(), start=starting_wc, current=starting_wc, sprint_type=sprint_type)

            # If it's a non-wordcount sprint, send a different message.
            if sprint_type == Sprint.SPRINT_TYPE_NO_WORDCOUNT:
                await context.send(
                    user.get_mention() + ', ' + lib.get_string('sprint:join:update:no_wordcount', user.get_guild()))
            else:
                # Send message back to channel letting them know their starting word count was updated
                await context.send(user.get_mention() + ', ' + lib.get_string('sprint:join:update', user.get_guild()).format(starting_wc))

        else:

            # Join the sprint
            sprint.join(user.get_id(), starting_wc=starting_wc, sprint_type=sprint_type)

            if sprint_type == Sprint.SPRINT_TYPE_NO_WORDCOUNT:
                await context.send(
                    user.get_mention() + ', ' + lib.get_string('sprint:join:update:no_wordcount', user.get_guild()))
            else:
                # Send message back to channel letting them know their starting word count was updated
                await context.send(user.get_mention() + ', ' + lib.get_string('sprint:join', user.get_guild()).format(starting_wc))

        # Currently this is the only usage of argument 2.
        shortname = arg2

        # If a project shortname is supplied, try to set that as what the user is sprinting for.
        if shortname is not None or project_id is not None:

            # Did we supply the project by name?
            if shortname is not None:

                # Convert to lowercase for searching.
                shortname = shortname.lower()

                # Make sure the project exists.
                project = user.get_project(shortname)

            # Or do we already have the ID from using 'same' and getting from previous sprint?
            elif project_id is not None:
                project = Project(project_id)

            # If that did not yield a valid project, send an error message.
            if not project:
                return await context.send(
                    user.get_mention() + ', ' + lib.get_string('project:err:noexists', user.get_guild()).format(
                        shortname))

            sprint.set_project(project.get_id(), user.get_id())
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:project', user.get_guild()).format(project.get_title()))

    async def run_time(self, context):
        """
        Get how long is left in the sprint
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        sprint = Sprint(user.get_guild())

        # If there is no active sprint, then just display an error
        if not sprint.exists():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:noexists', user.get_guild()))

        now = int(time.time())

        # If the sprint has not yet started, display the time until it starts
        if not sprint.has_started():
            left = lib.secs_to_mins(sprint.get_start() - now)
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:startsin', user.get_guild()).format(left['m'], left['s']))

        # If it's currently still running, display how long is left
        elif not sprint.is_finished():
            left = lib.secs_to_mins(sprint.get_end() - now)
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:timeleft', user.get_guild()).format(left['m'], left['s']))

        # If it's finished but not yet marked as completed, we must be waiting for word counts
        elif sprint.is_finished():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:waitingforwc', user.get_guild()))


    async def run_notify(self, context):
        """
        Set a user to be notified of upcoming sprints on this server.
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        user.set_guild_setting('sprint_notify', 1)
        return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:notified', user.get_guild()))

    async def run_forget(self, context):
        """
        Set a user to no longer be notified of upcoming sprints on this server.
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        user.set_guild_setting('sprint_notify', 0)
        return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:forgot', user.get_guild()))

    async def run_cancel(self, context):
        """
        Cancel a running sprint on the server
        :param context:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        sprint = Sprint(user.get_guild())

        # If there is no active sprint, then just display an error
        if not sprint.exists():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:noexists', user.get_guild()))

        # If they do not have permission to cancel this sprint, display an error
        if int(sprint.get_createdby()) != user.get_id() and context.message.author.permissions_in(context.message.channel).manage_messages is not True:
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:cannotcancel', user.get_guild()))

        # Get the users sprinting and create an array of mentions
        users = sprint.get_users()
        notify = sprint.get_notifications(users)

        # Cancel the sprint
        sprint.cancel(context)

        # Display the cancellation message
        message = lib.get_string('sprint:cancelled', user.get_guild())
        message = message + ', '.join(notify)
        return await context.send(message)

    async def run_start(self, context, length=None, start=None):
        """
        Try to start a sprint on the server
        :param context
        :param length: Length of time (in minutes) the sprint should last
        :param start: Time in minutes from now, that the sprint should start
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        sprint = Sprint(user.get_guild())

        # Check if sprint is finished but not marked as completed, in which case we can mark it as complete
        if sprint.is_finished() and sprint.is_declaration_finished():
            # Mark the sprint as complete
            await sprint.complete(context)
            # Reload the sprint object, as now there shouldn't be a pending one
            sprint = Sprint(user.get_guild())

        # If a sprint is currently running, we cannot start a new one
        if sprint.exists():
            return await context.send(user.get_mention() + ', ' + lib.get_string('sprint:err:alreadyexists', user.get_guild()))

        # Must be okay to continue #

        # If the length argument is not valid, use the default
        if length is None or lib.is_number(length) is False or lib.is_number(length) <= 0 or lib.is_number(length) > self.MAX_LENGTH:
            length = self.DEFAULT_LENGTH

        # Same goes for the start argument
        if start is None or lib.is_number(start) is False or lib.is_number(start) < 0 or lib.is_number(start) > self.MAX_DELAY:
            start = self.DEFAULT_DELAY

        # Make sure we are using ints and not floats passed through in the command
        length = int(length)
        start = int(start)

        # Calculate the start and end times based on the current timestamp
        now = int(time.time())
        start_time = now + (start * 60)
        end_time = start_time + (length * 60)

        # Create the sprint
        sprint = Sprint.create(guild=user.get_guild(), channel=context.message.channel.id, start=start_time, end=end_time, end_reference=end_time, length=length, createdby=user.get_id(), created=now)

        # Join the sprint
        sprint.join(user.get_id())

        # Increment the user's stat for sprints created
        user.add_stat('sprints_started', 1)

        # Are we starting immediately or after a delay?
        if start == 0:
            # Immediately. That means we need to schedule the end task.
            Task.schedule(sprint.TASKS['end'], end_time, 'sprint', sprint.get_id())
            return await sprint.post_start(context)
        else:
            # Delay. That means we need to schedule the start task, which will in turn schedule the end task once it's run.
            Task.schedule(sprint.TASKS['start'], start_time, 'sprint', sprint.get_id())
            return await sprint.post_delayed_start(context)


def setup(bot):
    bot.add_cog(SprintCommand(bot))
