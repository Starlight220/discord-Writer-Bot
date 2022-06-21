import lib
from operator import itemgetter
from structures.db import Database
from structures.user import User


class Guild:

    TOP_LIMIT = 10

    def __init__(self, guild):

        # Initialise the database instance
        self.__db = Database.instance()
        self._guild = guild
        self._id = guild.id
        self._members = [member.id for member in self._guild.members]
        self._settings = None
        self._disabled = None

    def get_id(self):
        return self._id

    def get_members_in_sql(self):
        return ', '.join(str(m) for m in self._members)

    def get_settings(self):

        # If the settings property is None, then load it up first
        if self._settings is None:
            self.load_settings()

        return self._settings

    def get_setting(self, setting):

        # If the settings property is None, then load it up first
        if self._settings is None:
            self.load_settings()

        # Now check if the key exists in the dictionary
        if setting in self._settings:
            return self._settings[setting]
        else:
            return None

    def load_settings(self):

        # Get the user_settings records
        records = self.__db.get_all('guild_settings', {'guild': self._id})

        # Reset the stats property
        self._settings = {}

        # Loop through the results and add to the stats property
        for row in records:
            self._settings[row['setting']] = row['value']

    def update_setting(self, setting, value):

        # If the user already has a value for this setting, we want to update
        user_setting = self.get_setting(setting)

        if user_setting:
            return self.__db.update('guild_settings', {'value': value}, {'guild': self._id, 'setting': setting})

        # Otherwise, we want to insert a new one
        else:
            return self.__db.insert('guild_settings', {'guild': self._id, 'setting': setting, 'value': value})

    def __load_disabled(self):
        raw = self.get_setting('disabled')
        if raw == None:
            self._disabled = set()
        else:
            self._disabled = set(raw.split(','))

    def disable_enable_command(self, command, disable: bool):
        """
        Disable or enable a command.
        """
        if self._disabled == None:
            self.__load_disabled()
        if disable:
            self._disabled.add(command)
        else:
            self._disabled.discard(command)
        self.update_setting('disabled', ','.join(self._disabled))

    def is_command_enabled(self, command):
        """
        Check is a command is enabled for this server.
        """
        if self._disabled == None:
            self.__load_disabled()
        return not (command in self._disabled)

    def get_top_xp(self):
        """
        Get the top {self.TOP_LIMIT} users in a guild, ordered by their XP
        :return: array
        """

        # Build the SQL query using the IDs of the guild members
        sql = 'SELECT user FROM user_xp WHERE user IN (' + self.get_members_in_sql() + ') ORDER BY xp DESC LIMIT ' + str(self.TOP_LIMIT)
        self.__db.cursor.execute(sql)
        results = self.__db.cursor.fetchall()

        users = []
        for user in results:
            guild_member = self._guild.get_member( int(user['user']) )
            usr = User(user['user'], self._id, None, guild_member.display_name)
            users.append( usr )

        return users

    def get_from_bot(bot, guild_id):
        """
        Load the guild object from the bot.
        This is used if we are in a cron, so we don't have a context we can get the guild object from
        :return:
        """
        bot_guild = bot.get_guild(int(guild_id))
        return Guild(bot_guild)
