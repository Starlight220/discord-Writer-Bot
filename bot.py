import os, datetime, time, lib, traceback, discord
from discord.ext import tasks
from discord.ext import commands
from discord.ext.commands import AutoShardedBot
from structures.db import *
from structures.guild import Guild
from structures.task import Task
from structures.user import User

class WriterBot(AutoShardedBot):

    COMMAND_GROUPS = ['util', 'fun', 'writing']
    SCHEDULED_TASK_LOOP = 30.0 # Seconds
    CLEANUP_TASK_LOOP = 1.0 # Hours

    def __init__(self, *args, **kwargs):
        super().__init__(help_command=commands.DefaultHelpCommand(dm_help=True), *args, **kwargs)
        self.config = lib.get('./settings.json')
        self.start_time = time.time()
        self.app_info = None
        self.setup()

    async def on_message(self, message):
        """
        Run any checks we need to, before processing the messages.
        :param message:
        :return:
        """
        # If the bot is not logged in yet, don't try to run any commands.
        if not self.is_ready():
            return

        await self.process_commands(message)

    async def on_ready(self):
        """
        Method run once the bot has logged in as is ready to be used.
        :return:
        """
        lib.debug('Logged on as: ' + str(self.user))

        # Show the help command on the status
        await self.change_presence(activity=discord.Game(self.config.prefix + 'help'))

        # Retrieve app info.
        self.app_info = await self.application_info()

        # Start running the scheduled tasks.
        self.scheduled_tasks.start()
        self.cleanup_tasks.start()

    async def on_command_error(self, context, error):
        """
        Method to run if there is an exception thrown by a command
        :param error:
        :param context:
        :return:
        """

        ignore = (commands.errors.CommandNotFound, commands.errors.UserInputError)

        if isinstance(error, ignore):
            return
        elif isinstance(error, commands.errors.NoPrivateMessage):
            return await context.send('Commands cannot be used in Private Messages.')
        elif isinstance(error, commands.errors.MissingPermissions):
            user = User(context.message.author.id, context.guild.id, context)
            return await context.send(user.get_mention() + ', ' + str(error))
        elif isinstance(error, commands.errors.CommandInvokeError) and ('Broken pipe' in str(error) or 'Connection reset by peer' in str(error)):
            lib.error(traceback.format_exception(type(error), error, error.__traceback__), 'NETWORK')
            return await context.send('Sorry, I am currently experiencing network issues. Please wait a moment and try again.')
        elif isinstance(error, commands.errors.CommandInvokeError):
            code = lib.error('CommandInvokeError in command `{}`: {}'.format(context.command, str(error)))
            lib.error(traceback.format_exception(type(error), error, error.__traceback__), code)
            user = User(context.message.author.id, context.guild.id, context)
            return await context.send(lib.get_string('err:commandinvoke', user.get_guild()).format(code))
        else:
            code = lib.error('Exception in command `{}`: {}'.format(context.command, str(error)))
            lib.error( traceback.format_exception(type(error), error, error.__traceback__), code )
            user = User(context.message.author.id, context.guild.id, context)
            return await context.send(lib.get_string('err:unknown', user.get_guild()).format(code))

    def load_commands(self):
        """
        Load all the commands from the cogs/ directory.
        :return: void
        """
        # Find all the command groups in the cogs/ directory
        for dir in self.COMMAND_GROUPS:

            # Then all the files inside the command group directory
            for file in os.listdir(f'cogs/{dir}'):

                # If it ends with .py then try to load it.
                if file.endswith(".py"):

                    cog = file[:-3]

                    try:
                        self.load_extension(f"cogs.{dir}.{cog}")
                        lib.out(f'[EXT][{dir}.{cog}] loaded')
                    except Exception as e:
                        lib.out(f'[EXT][{dir}.{cog}] failed to load')
                        lib.out(e)

    def update(self):
        """
        Run any database updates which are required
        :return:
        """
        db = Database.instance()

        version = lib.get('./version.json')
        version = version.db_version

        db_version = db.get('bot_settings', {'setting': 'version'})
        current_version = db_version['value'] if db_version else 0

        version = int(version)
        current_version = int(current_version)

        # Find all update files
        for file in os.listdir(f'data/updates'):

            # If it ends with .update then try to use it.
            if file.endswith(".update"):

                # Get the update version from the file name and convert to int for comparison.
                update_version = int(file[:-7])

                # Is this update due to run?
                if update_version > current_version:

                    # Load the file and the SQL to run.
                    update = lib.get('./data/updates/' + file)

                    # Loop through the array of SQL statements to run.
                    for sql in update:
                        lib.out('[UPDATE] Running query `' + sql + '`')
                        db.execute(sql, [])

        # Once it's done, update the version in the database.
        setting = db.get('bot_settings', {'setting': 'version'})
        if setting:
            db.update('bot_settings', {'value': version}, {'setting': 'version'})
        else:
            db.insert('bot_settings', {'setting': 'version', 'value': version})

    def setup(self):
        """
        Run the bot setup
        :return:
        """
        lib.out('[BOT] Beginning boot process')

        # Install the database.
        db = Database.instance()
        db.install()
        lib.out('[DB] Database tables installed')

        # Run any database updates.
        self.update()

        # Setup the recurring tasks which need running.
        self.setup_recurring_tasks()
        lib.out('[TASK] Recurring tasks inserted')

        # Restart all tasks which are marked as processing, in case the bot dropped out during the process.
        db.update('tasks', {'processing': 0})

        # Remove the default 'help' command.
        self.remove_command('help')

    def setup_recurring_tasks(self):
        """
        Create the recurring tasks for the first time.
        :return:
        """
        db = Database.instance()

        # Delete the recurring tasks in case they got stuck in processing, and then re-create them.
        db.delete('tasks', {'object': 'goal', 'type': 'reset'})
        db.insert('tasks', {'object': 'goal', 'time': 0, 'type': 'reset', 'recurring': 1, 'runeveryseconds': 900})
        db.delete('tasks', {'object': 'reminder', 'type': 'send'})
        db.insert('tasks', {'object': 'reminder', 'time': 0, 'type': 'send', 'recurring': 1, 'runeveryseconds': 30})

    @staticmethod
    def load_prefix(bot, message):
        """
        Get the prefix to use for the guild
        :param bot:
        :param message:
        :return:
        """
        db = Database.instance()
        prefixes = {}
        config = lib.get('./settings.json')

        # Get the guild_settings for prefix and add to a dictionary, with the guild id as the key.
        settings = db.get_all('guild_settings', {'setting': 'prefix'})
        for setting in settings:
            prefixes[int(setting['guild'])] = setting['value']

        # If the guild id exists in this dictionary return that, otherwise return the default.
        if message.guild is not None:
            prefix = prefixes.get(message.guild.id, config.prefix)
        else:
            prefix = config.prefix

        return commands.when_mentioned_or(prefix)(bot, message)

    @tasks.loop(seconds=SCHEDULED_TASK_LOOP)
    async def scheduled_tasks(self):
        """
        Execute the scheduled tasks.
        (I believe) this is going to happen for each shard, so if we have 5 shards for example, this loop will be running simultaneously on each of them.
        :return:
        """
        lib.debug('['+str(self.shard_id)+'] Checking for scheduled tasks...')

        try:
            await Task.execute_all(self)
        except Exception as e:
            lib.error( traceback.format_exception(type(e), e, e.__traceback__), 'TASK' )

    @tasks.loop(hours=CLEANUP_TASK_LOOP)
    async def cleanup_tasks(self):
        """
        Clean up any old tasks which are still in the database and got stuck in processing
        :return:
        """
        db = Database.instance()

        lib.debug('['+str(self.shard_id)+'] Running task cleanup...')

        hour_ago = int(time.time()) - (60*60)
        db.execute('DELETE FROM tasks WHERE processing = 1 AND time < %s AND time <> 0', [hour_ago])

