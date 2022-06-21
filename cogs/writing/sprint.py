import time
from asyncio import sleep
from datetime import datetime
from typing import Optional, Union

from interactions import Client, Option, OptionType, CommandContext, Choice, ComponentContext, \
    extension_component, ComponentType
from interactions.ext.enhanced import EnhancedExtension, ext_subcommand_base

import lib
from structures.guild import Guild
from structures.project import Project
from structures.sprint import Sprint
from structures.task import Task
from structures.user import User

PROJECT_SELECTOR_ID = 'sprint_select_project'


class SprintCommand(EnhancedExtension):
    # 20 minutes
    DEFAULT_LENGTH = 20
    # 2 minutes
    DEFAULT_DELAY = 2
    # 1 hour
    MAX_LENGTH = 60
    # 24 hours
    MAX_DELAY = 60 * 24
    # If WPM exceeds this amount, check that the user meant to submit that many words
    WPM_CHECK = 150

    def __init__(self, bot: Client):
        self.bot: Client = bot

    sprint_base = ext_subcommand_base(
        base="sprint",
        description="TODO",
        scope=894554679143464960
    )

    @sprint_base.subcommand(
        name="for",
        description="Start a sprint",
        options=[
            Option(
                name="length",
                description="length",
                type=OptionType.INTEGER,
                required=True
            ),
            Option(
                name="in_",
                description="start the sprint in x time from now. NOTE: `in` and `at` are "
                            "mutually exclusive!",
                type=OptionType.INTEGER,
                required=False
            ),
            Option(
                name="at",
                description="start the sprint at a given time past the hour. NOTE: `in` and `at` "
                            "are mutually exclusive!",
                type=OptionType.INTEGER,
                required=False
            )
        ],
    )
    async def sprint_for(self, context: CommandContext, length: int, in_: int = None,
                         at: int = None):
        """
        Try to start a sprint on the server.

        :param CommandContext context: Context in which this command was called.
        :param int length: Length of time (in minutes) the sprint should last.
        :param int in_: Time in minutes from now, that the sprint should start.
        :param int at: Time in minutes past the hour, that the sprint should start.
        """
        # in case that the command takes a lot of time
        await context.defer()

        if not Guild(context.guild).is_command_enabled('sprint'):
            return await context.send(
                lib.get_string('err:disabled', context.guild_id),
                hidden=True
            )

        user = User(context.author.id, context.guild_id, context)
        sprint = Sprint(context.guild_id)

        # Check if sprint is finished but not marked as completed, in which case we can mark it as complete
        if sprint.is_finished() and sprint.is_declaration_finished():
            # Mark the sprint as complete
            await sprint.complete()
            # Reload the sprint object, as now there shouldn't be a pending one
            sprint = Sprint(context.guild_id)

        # If a sprint is currently running, we cannot start a new one
        if sprint.exists():
            return await context.send(context.author.mention + ', ' + lib.get_string('sprint:err:alreadyexists', context.guild_id))

        # Check sprint length
        # If the length argument is not valid, use the default
        if 0 > length or self.MAX_LENGTH < length:
            length = self.DEFAULT_LENGTH

        # Figure out when sprint starts
        delay: int = 0

        # Make sure that the user didn't enter both `at` and `in`
        if in_ is not None and at is not None:
            return context.send(context.author.mention + ', ' + lib.get_string('sprint:err:for:exclusive', context.guild_id))

        # ensure that delay is in valid range
        if in_ is not None:
            if in_ < 0 or in_ > self.MAX_DELAY:
                delay = self.DEFAULT_DELAY
            else:
                delay = in_

        if at is not None:
            # Make sure the user has set their timezone, otherwise we can't calculate it.
            timezone = user.get_setting('timezone')
            user_timezone = lib.get_timezone(timezone)
            if not user_timezone:
                return await context.send(context.author.mention + ', ' + lib.get_string('err:notimezone', context.guild_id))

            if 0 > at or at > 60:
                return await context.send(context.author.mention + ', ' + lib.get_string('sprint:err:for:at', context.guild_id))

            # Now using their timezone and the minute they requested, calculate when that should be.
            delay = (60 + at - datetime.now(user_timezone).minute) % 60

        # Calculate the start and end times based on the current timestamp
        now = int(time.time())
        start_time = now + (delay * 60)
        end_time = start_time + (length * 60)

        # Create the sprint
        sprint = Sprint.create(
            guild=context.guild_id,
            channel=context.channel.id,
            start=start_time,
            end=end_time,
            end_reference=end_time,
            length=length,
            createdby=context.author.id,
            created=now
        )

        # Join the sprint
        sprint.join(context.author.id)

        # Increment the user's stat for sprints created
        user.add_stat('sprints_started', 1)

        if delay != 0:
            # Delay. That means we need to schedule the start task, which will in turn schedule the end task once it's run.
            # await sprint.post_delayed_start(context)
            await context.send("Started!")
            await sleep(delay=delay*60)
            Task.schedule(sprint.TASKS['start'], start_time, 'sprint', sprint.get_id())
            return await (await context.get_channel()).send("After Delay!")
        # Are we starting immediately or after a delay?
        else:
            # Immediately. That means we need to schedule the end task.
            # Task.schedule(sprint.TASKS['end'], end_time, 'sprint', sprint.get_id())
            pass
            # return await sprint.post_start(context)

    @sprint_base.subcommand(
        name="join",
        description="Join sprint",
        options=[
            Option(
                name="initial",
                type=OptionType.INTEGER,
                required=True,
                description="Initial word count"
            ),
            Option(
                name="shortname",
                type=OptionType.STRING,
                required=False,
                description="Project to sprint in"
            )
        ]
    )
    async def sprint_join(self, context: CommandContext, initial: int, shortname: str = None):
        user: User
        sprint: Sprint
        err: bool
        user, sprint, err = await SprintCommand._common_init(context)
        if err:
            return

        if sprint.is_user_sprinting(context.author.id):

            # Update the sprint_users record. We set their current_wc to the same as starting_wc here, otherwise if they join with, say 50 and their current remains 0
            # then if they run a status, or in the ending calculations, it will say they wrote -50.
            sprint.update_user(context.author.id, start=initial, current=initial, sprint_type=None)
            # Send message back to channel letting them know their starting word count was updated
            await context.send(context.author.mention + ', ' + lib.get_string('sprint:join:update', context.guild_id).format(initial))

        else:
            # Join the sprint
            sprint.join(context.author.id, starting_wc=initial, sprint_type=None)

            # Send message back to channel letting them know their starting word count was updated
            await context.send(context.author.mention + ', ' + lib.get_string('sprint:join', context.guild_id).format(initial))

        # If they are sprinting in a project, send that message as well.
        if shortname is not None:
            await self._set_project(context, shortname)

    @sprint_base.subcommand(
        name="join-no-wc",
        description="Join a sprint without counting words",
        options=[
            Option(
                name="shortname",
                type=OptionType.STRING,
                required=False,
                description="Project to sprint in"
            )
        ],
    )
    async def sprint_join_no_wc(self, context: CommandContext, shortname: str = None):
        """
        Join a sprint without counting words

        :param CommandContext context: context this command was invoked in.
        :param str shortname: Project shortname
        """
        user: User
        sprint: Sprint
        err: bool
        user, sprint, err = await SprintCommand._common_init(context)
        if err:
            return

        if sprint.is_user_sprinting(context.author.id):
            sprint.update_user(context.author.id, start=0, current=0,
                               sprint_type=Sprint.SPRINT_TYPE_NO_WORDCOUNT)
        else:
            sprint.join(context.author.id, starting_wc=0,
                        sprint_type=Sprint.SPRINT_TYPE_NO_WORDCOUNT)

        await context.send(
            context.author.mention + ', ' + lib.get_string('sprint:join:update:no_wordcount', context.guild_id))

        # If they are sprinting in a project, send that message as well.
        if shortname is not None:
            await self._set_project(context, shortname)

    @sprint_base.subcommand(
        name="join-same",
        description="Join a sprint from where you left off last sprint"
    )
    async def sprint_join_same(self, context: CommandContext):
        """
        Join this sprint with the same project as last sprint and with the ending wc.

        :param CommandContext context: context this command was invoked in.
        """
        user: User
        sprint: Sprint
        err: bool
        user, sprint, err = await SprintCommand._common_init(context)
        if err:
            return

        # Okay, check for their most recent sprint record
        most_recent = user.get_most_recent_sprint(sprint)
        if most_recent is None:
            return await self.sprint_join.func(context, 0)

        starting_wc = most_recent['ending_wc']
        project_id = most_recent['project']
        sprint_type = most_recent['sprint_type']

        if sprint_type == Sprint.SPRINT_TYPE_NO_WORDCOUNT:
            return await self.sprint_join_no_wc.func(self=self, context=context)

        await self.sprint_join.func(self=self, context=context, initial=starting_wc)
        return await self._set_project(context, project_id=project_id)

    @sprint_base.subcommand(
        name="wc",
        description="Declare total word count",
        options=[
            Option(
                name="amount",
                description="How many words do you have written at the end of this sprint? (including initial wc)",
                type=OptionType.INTEGER,
                required=True)
        ]
    )
    async def sprint_wc(self, context: CommandContext, amount: int):
        """
        Declare user's current word count for the sprint
        :param CommandContext context: context this command was invoked in.
        :param int amount: how many words the user has
        """
        user: User
        sprint: Sprint
        err: bool
        user, sprint, err = await SprintCommand._common_init(context)
        if err:
            return

        # If the user is not sprinting, then again, just display that error
        if not await self._check_is_in_sprint(context, sprint):
            return

        # If the sprint hasn't started yet, display error
        if not sprint.has_started():
            return await context.send(
                context.author.mention + ', ' +
                lib.get_string('sprint:err:notstarted', context.guild_id))

        # Get the user's sprint info
        user_sprint = sprint.get_user_sprint(context.author.id)

        # If they joined without a word count, they can't add one.
        if user_sprint['sprint_type'] == Sprint.SPRINT_TYPE_NO_WORDCOUNT:
            return await context.send(
                context.author.mention + ', ' +
                lib.get_string('sprint:err:nonwordcount', context.guild_id))

        # If the declared value is less than they started with, then that is an error.
        if amount < int(user_sprint['starting_wc']):
            diff = user_sprint['current_wc'] - amount
            return await context.send(
                context.author.mention + ', ' +
                lib.get_string('sprint:err:wclessthanstart', context.guild_id)
                .format(amount, user_sprint['starting_wc'], diff))

        return await self._increment_words(context, sprint, user, amount)

    @sprint_base.subcommand(
        name="wrote",
        description="Declare words written this sprint",
        options=[
            Option(
                name="amount",
                description="How many words did you write *in this sprint*? (not including your starting wc)",
                type=OptionType.INTEGER,
                required=True)
        ]
    )
    async def sprint_wrote(self, context: CommandContext, amount: int):
        """
        Declare how many words you wrote this sprint (ie a calculation)

        :param CommandContext context: context this command was invoked in.
        :param int amount: how many words you wrote.
        """
        user: User
        sprint: Sprint
        err: bool
        user, sprint, err = await SprintCommand._common_init(context)
        if err:
            return

        # If the user is not sprinting, then again, just display that error
        # If the sprint hasn't started yet, display error
        if not (await
                self._check_is_in_sprint(context, sprint) and await
                self._check_sprint_started(context, sprint)):
            return

        # Get the user's sprint info
        user_sprint = sprint.get_user_sprint(context.author.id)

        # If they joined without a word count, they can't add one.
        if user_sprint['sprint_type'] == Sprint.SPRINT_TYPE_NO_WORDCOUNT:
            return await context.send(
                context.author.mention + ', ' + lib.get_string('sprint:err:nonwordcount', context.guild_id))

        # Add that to the current word count, to get the new value
        new_amount: int = int(user_sprint['current_wc']) + amount

        return await self._increment_words(context, sprint, user, new_amount)

    @sprint_base.subcommand(
        name="cancel",
        description="Cancel a sprint"
    )
    async def sprint_cancel(self, context: CommandContext):
        """
        Cancel a running sprint on the server
        :param CommandContext context: context this command was invoked in.
        """
        user: User
        sprint: Sprint
        err: bool
        user, sprint, err = await SprintCommand._common_init(context)
        if err:
            return

        # If they do not have permission to cancel this sprint, display an error
        if int(sprint.get_createdby()) != context.author.id and context.author.permissions_in(
                context.channel).manage_messages is not True:
            return await context.send(
                context.author.mention + ', ' + lib.get_string('sprint:err:cannotcancel', context.guild_id))

        # Get the users sprinting and create an array of mentions
        users = sprint.get_users()
        notify = sprint.get_notifications(users)

        # Cancel the sprint
        sprint.cancel(context)

        # Display the cancellation message
        message = lib.get_string('sprint:cancelled', context.guild_id)
        message = message + ', '.join(notify)
        return await context.send(message)

    @sprint_base.subcommand(
        name="end",
        description="End a sprint"
    )
    async def sprint_end(self, context: CommandContext):
        """
        Manually force the sprint to end (if the cron hasn't posted the message) and ask for final word counts
        :param CommandContext context: context this command was invoked in.
        """
        user: User
        sprint: Sprint
        err: bool
        user, sprint, err = await SprintCommand._common_init(context)
        if err:
            return

        # If they do not have permission to cancel this sprint, display an error
        if int(sprint.get_createdby()) != context.author.id and context.author.permissions_in(
                context.channel).manage_messages is not True:
            return await context.send(
                context.author.mention + ', ' + lib.get_string('sprint:err:cannotend', context.guild_id))

        # If the sprint hasn't started yet, it can't be ended.
        if not await self._check_sprint_started(context, sprint):
            return

        # Change the end reference to now, otherwise wpm calculations will be off,
        # as it will use the time in the future when it was supposed to end.
        sprint.update_end_reference(int(time.time()))

        # Since we are forcing the end, we should cancel any pending tasks for this sprint
        Task.cancel('sprint', sprint.get_id())

        # We need to set the bot into the sprint object,
        # as we will need it when trying to get the guild object
        sprint.set_bot(self.bot)
        return await sprint.end(context)

    @sprint_base.subcommand(
        name="leave",
        description="Leave a sprint"
    )
    async def sprint_leave(self, context: CommandContext):
        """
        Leave the sprint
        :param CommandContext context: context this command was invoked in.
        """
        user: User
        sprint: Sprint
        err: bool
        user, sprint, err = await SprintCommand._common_init(context)
        if err:
            return

        # Remove the user from the sprint
        sprint.leave(context.author.id)

        await context.send(
            context.author.mention + ', ' + lib.get_string('sprint:leave', context.guild_id))

        # If there are now no users left, cancel the whole sprint
        if len(sprint.get_users()) == 0:
            # Cancel the sprint
            sprint.cancel(context)

            # Decrement sprints_started stat for whoever started this one
            creator = User(sprint.get_createdby(), sprint.get_guild())
            creator.add_stat('sprints_started', -1)

            # Display a message letting users know
            return await context.send(lib.get_string('sprint:leave:cancelled', context.guild_id))

    @sprint_base.subcommand(
        name="time",
        description="Get how long is left in the sprint"
    )
    async def sprint_time(self, context: CommandContext):
        """
        Get how long is left in the sprint
        :param CommandContext context: context this command was invoked in.
        """
        # in case that the command takes a lot of time
        await context.defer()

        if not Guild(context.guild).is_command_enabled('sprint'):
            return await context.send(
                lib.get_string('err:disabled', context.guild_id),
                ephemeral=True
            )

        sprint = Sprint(context.guild_id)

        # If there is no active sprint, then just display an error
        if not sprint.exists():
            return await context.send(
                context.author.mention + ', ' + lib.get_string('sprint:err:noexists', context.guild_id))

        now = int(time.time())

        # If the sprint has not yet started, display the time until it starts
        if not sprint.has_started():
            left = lib.secs_to_mins(sprint.get_start() - now)
            return await context.send(
                context.author.mention + ', ' +
                lib.get_string('sprint:startsin', context.guild_id).format(left['m'], left['s']))

        # If it's currently still running, display how long is left
        elif not sprint.is_finished():
            left = lib.secs_to_mins(sprint.get_end() - now)
            return await context.send(
                context.author.mention + ', ' +
                lib.get_string('sprint:timeleft', context.guild_id).format(left['m'], left['s']))

        # If it's finished but not yet marked as completed, we must be waiting for word counts
        elif sprint.is_finished():
            return await context.send(
                context.author.mention + ', ' + lib.get_string('sprint:waitingforwc', context.guild_id))

    @sprint_base.subcommand(
        name="status",
        description="Get your status in the current sprint"
    )
    async def sprint_status(self, context: CommandContext):
        """
        Get the user's status in this sprint
        :param CommandContext context: context this command was invoked in.
        """
        user: User
        sprint: Sprint
        err: bool
        user, sprint, err = await SprintCommand._common_init(context)
        if err:
            return

        # If the user is not sprinting, then again, just display that error
        if not sprint.is_user_sprinting(context.author.id):
            return await context.send(
                context.author.mention + ', ' + lib.get_string('sprint:err:notjoined', context.guild_id))

        # If the sprint hasn't started yet, display error
        if not await self._check_sprint_started(context, sprint):
            return

        # If they are sprinting, then display their current status.
        user_sprint = sprint.get_user_sprint(context.author.id)

        # Build the variables to be passed into the status string
        now = int(time.time())
        current = user_sprint['current_wc']
        written = current - user_sprint['starting_wc']
        seconds = now - user_sprint['timejoined']
        elapsed = round(seconds / 60, 1)
        wpm = Sprint.calculate_wpm(written, seconds)
        left = round((sprint.get_end() - now) / 60, 1)

        return await context.send(
            context.author.mention + ', ' +
            lib.get_string('sprint:status', context.guild_id)
            .format(current, written, elapsed, wpm, left)
        )

    @sprint_base.subcommand(
        name="pb",
        description="Get the user's personal best for sprinting"
    )
    async def sprint_pb(self, context: CommandContext):
        """
        Get the user's personal best for sprinting
        :param CommandContext context: context this command was invoked in.
        :return:
        """
        # in case that the command takes a lot of time
        await context.defer()

        if not Guild(context.guild).is_command_enabled('sprint'):
            return await context.send(
                lib.get_string('err:disabled', context.guild_id),
                hidden=True
            )

        user = User(context.author.id, context.guild_id, context)
        record = user.get_record('wpm')

        if record is None:
            return await context.send(
                context.author.mention + ', ' + lib.get_string('sprint:pb:none', context.guild_id))
        else:
            return await context.send(
                context.author.mention + ', ' + lib.get_string('sprint:pb', context.guild_id).format(int(record)))

    @sprint_base.subcommand(
        name="notify",
        description="Set whether you will be notified of upcoming sprints on this server",
        options=[
            Option(
                name="notify",
                description="Whether or not to notify",
                type=OptionType.INTEGER,
                required=True,
                choices=[
                    Choice(
                        name="Notify",
                        value=1
                    ),
                    Choice(
                        name="Do not notify",
                        value=0
                    )
                ]
            )
        ]
    )
    async def sprint_notify(self, context: CommandContext, notify: int):
        """
        Set a user to be notified of upcoming sprints on this server.
        :param CommandContext context: context this command was invoked in.
        """
        # in case that the command takes a lot of time
        await context.defer()

        if not Guild(context.guild).is_command_enabled('sprint'):
            return await context.send(
                lib.get_string('err:disabled', context.guild_id),
                hidden=True
            )

        user = User(context.author.id, context.guild_id, context)
        user.set_guild_setting('sprint_notify', str(notify))
        message = context.author.mention + ', '
        if notify == 1:
            message += lib.get_string('sprint:notified', context.guild_id)
        else:
            message += lib.get_string('sprint:forgot', context.guild_id)
        return await context.send(message)

    @sprint_base.subcommand(
        name="purge",
        description="Purge any users who asked for notifications but aren't in the server any more."
    )
    async def sprint_purge(self, context: CommandContext):
        """
        Purge any users who asked for notifications but aren't on the server anymore.
        :param CommandContext context: context this command was invoked in.
        """
        # in case that commands take a long time
        await context.defer(ephemeral=True)

        if not Guild(context.guild).is_command_enabled('sprint'):
            return await context.send(
                lib.get_string('err:disabled', context.guild_id),
                hidden=True
            )

        if context.channel.permissions_for(context.author).manage_messages is not True:
            return await context.send(context.author.mention + ', ' +
                                      lib.get_string('sprint:err:purgeperms', context.guild_id))
        purged = await Sprint.purge_notifications(context)
        if purged > 0:
            return await context.send(
                lib.get_string('sprint:purged', context.guild_id).format(purged))
        else:
            return await context.send(lib.get_string('sprint:purged:none', context.guild_id))

    @extension_component(
        components=PROJECT_SELECTOR_ID,
        component_type=ComponentType.SELECT
    )
    async def component_set_project(self, context: ComponentContext):
        # in case that the command takes a lot of time
        await context.defer()

        return await self._set_project(context, shortname=context.selected_options[0])

    @classmethod
    async def _set_project(cls, context: Union[CommandContext, ComponentContext], shortname: str = None,
                           project_id: int = None):
        """
        Internal utility function: Set the project the user wants to sprint in.
        :param CommandContext context: context this command was invoked in.
        """
        user = User(context.author.id, context.guild_id, context)
        sprint = Sprint(context.guild_id)

        project: Optional[Project]

        # If there is no active sprint, then just display an error
        if not sprint.exists():
            return await context.send(
                context.author.mention + ', ' + lib.get_string('sprint:err:noexists', context.guild_id))

        # If the user is not sprinting, then again, just display that error
        if not sprint.is_user_sprinting(context.author.id):
            return await context.send(
                context.author.mention + ', ' + lib.get_string('sprint:err:notjoined', context.guild_id))

        if project_id is None:
            # Did we supply the project by name?
            if shortname is None:
                return
            # If a project shortname is supplied, try to set that as what the user is sprinting for.
            # Convert to lowercase for searching.
            shortname = shortname.lower()

            # Make sure the project exists.
            project = Project.get(user.get_id(), shortname)

            # If that did not yield a valid project, send an error message.
            if project is None:
                return await context.send(
                    context.author.mention + ', ' + lib.get_string('project:err:noexists', context.guild_id).format(shortname))
        else:
            project = Project(project_id)

        sprint.set_project(project.get_id(), context.author.id)
        return await context.send(
            context.author.mention + ', ' +
            lib.get_string('sprint:project', context.guild_id).format(project.name))

    @classmethod
    async def _common_init(cls, context: CommandContext, hidden: bool = False) -> (User, Sprint, bool):
        if not Guild(context.guild).is_command_enabled('sprint'):
            return await context.send(
                lib.get_string('err:disabled', context.guild_id),
                hidden=True
            )
        if not context.deferred:
            await context.defer(ephemeral=hidden)

        user = User(context.author.id, context.guild_id, context)
        sprint = Sprint(context.guild_id)

        # If there is no active sprint, then just display an error
        if not sprint.exists():
            await context.send(context.author.mention + ', ' + lib.get_string(
                'sprint:err:noexists', context.guild_id))
            return None, None, True
        else:
            return user, sprint, False

    @classmethod
    async def _increment_words(cls, context: CommandContext, sprint: Sprint, user: User,
                               amount: int):
        user_sprint = sprint.get_user_sprint(context.author.id)

        # Is the sprint finished? If so this will be an ending_wc declaration, not a current_wc one.
        col = 'ending' if sprint.is_finished() else 'current'

        # Before we actually update it, if the WPM is huge and most likely an error,
        # just check with them if they meant to put that many words.
        written = amount - int(user_sprint['starting_wc'])
        seconds = int(sprint.get_end_reference()) - user_sprint['timejoined']
        wpm = Sprint.calculate_wpm(written, seconds)

        # Does the user have a configured setting for max wpm to check?
        max_wpm = user.get_setting('maxwpm')
        if not max_wpm:
            max_wpm = cls.WPM_CHECK

        if wpm > int(max_wpm):
            return await context.send(
                context.author.mention + ', ' +
                lib.get_string('sprint:wpm:redeclare', context.guild_id).format(written, wpm),
                hidden=True
            )

        # Update the user's sprint record
        arg = {col: amount}
        sprint.update_user(context.author.id, **arg)

        # Reload the user sprint info
        user_sprint = sprint.get_user_sprint(context.author.id)

        # Which value are we displaying?
        wordcount = user_sprint['ending_wc'] if sprint.is_finished() else user_sprint['current_wc']
        written = int(wordcount) - int(user_sprint['starting_wc'])

        await context.send(
            context.author.mention + ', ' + lib.get_string('sprint:declared', context.guild_id).format(
                wordcount, written))

        # Is the sprint now over and has everyone declared?
        if sprint.is_finished() and sprint.is_declaration_finished():
            Task.cancel('sprint', sprint.get_id())
            await sprint.complete(context)

    @classmethod
    async def _check_sprint_started(cls, context: CommandContext, sprint: Sprint) -> bool:
        """
        Check that the sprint started
        :param CommandContext context: context this command was invoked in.
        :param Sprint sprint: the sprint on this server.
        :return: True if sprint has started
        """
        if sprint.has_started():
            return True

        await context.send(context.author.mention + ', ' + lib.get_string('sprint:err:notstarted', context.guild_id))
        return False

    @classmethod
    async def _check_is_in_sprint(cls, context: CommandContext, sprint: Sprint) -> bool:
        if sprint.is_user_sprinting(context.author.id):
            return True

        await context.send(
            context.author.mention + ', ' + lib.get_string('sprint:err:notjoined', context.guild_id))
        return False

    sprint_base.finish()


def setup(bot: Client):
    return SprintCommand(bot)
