import discord, lib, time, math
from discord.ext import commands
from structures.db import Database
from structures.user import User
from structures.wrapper import CommandWrapper
from structures.guild import Guild

class Goal(commands.Cog, CommandWrapper):

    GOAL_TYPE_DAILY = 'daily'
    GOAL_TYPE_WEEKLY = 'weekly'
    GOAL_TYPE_MONTHLY = 'monthly'
    GOAL_TYPE_YEARLY = 'yearly'

    def __init__(self, bot):
        self.bot = bot
        self.__db = Database.instance()
        self._arguments = [
            {
                'key': 'option',
                'prompt': 'goal:argument:option',
                'required': True
            },
            {
                'key': 'value',
                'required': False
            }
        ]
        self.types = [self.GOAL_TYPE_DAILY, self.GOAL_TYPE_WEEKLY, self.GOAL_TYPE_MONTHLY, self.GOAL_TYPE_YEARLY]

    @commands.command(name="goal", aliases=['goals'])
    @commands.guild_only()
    async def goal(self, context, option=None, type=None, value=None):
        """
        Sets a daily goal which resets every 24 hours at midnight in your timezone.

        Examples:
            !goal - Print a table of all your goals, with their progress and next reset time.
            !goal check daily - Checks how close you are to your daily goal
            !goal set weekly 500 - Sets your weekly goal to be 500 words per day
            !goal cancel monthly - Deletes your monthly goal
            !goal time daily - Checks how long until your daily goal resets
        """
        if not Guild(context.guild).is_command_enabled('goal'):
            return await context.send(lib.get_string('err:disabled', context.guild.id))

        user = User(context.message.author.id, context.guild.id, context)

        # If no option is sent and we just do `goal` then display a table of all their goals.
        if option is None:
            return await self.run_check_all(context)

        # Otherwise, we must specify a type.
        if type is None or type not in self.types:
            return await context.send(user.get_mention() + ', ' + lib.get_string('goal:invalidtype', user.get_guild()))

        if option == 'set':
            return await self.run_set(context, type, value)
        elif option == 'cancel' or option == 'delete' or option == 'reset':
            return await self.run_cancel(context, type)
        elif option == 'time':
            return await self.run_time(context, type)
        elif option == 'check':
            return await self.run_check(context, type)
        elif option == 'history':
            return await self.run_history(context, type)
        elif option == 'update':
            return await self.run_update(context, type, value)
        else:
            return await context.send(user.get_mention() + ', ' + lib.get_string('goal:invalidoption', user.get_guild()))

    async def run_update(self, context, type, amount):
        """
        Update the value of a goal, without affecting the others or updating XP, etc...
        Useful for if you want to record the writing you have done, before you started using Writer-Bot.
        @param context:
        @param type:
        @param amount:
        @return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        type_string = lib.get_string('goal:' + type, user.get_guild())
        user_goal = user.get_goal(type)

        # Check if we can convert the amount to an int
        amount = lib.is_number(amount)
        if not amount:
            return await context.send(user.get_mention() + ', ' + lib.get_string('err:validamount', user.get_guild()))

        # Set the goal's current amount.
        if user_goal and user.update_goal(type, amount):
            return await context.send(user.get_mention() + ', ' + lib.get_string('goal:updated', user.get_guild()).format(type_string, amount))
        else:
            return await context.send(user.get_mention() + ', ' + lib.get_string('goal:nogoal', user.get_guild()).format(type_string, type))

    async def run_history(self, context, type):
        """
        Get the user's goal history, so they can look back and see how they did for previous goals
        @param context:
        @param type:
        @return:
        """
        user = User(context.message.author.id, context.guild.id, context)
        type_string = lib.get_string('goal:' + type, user.get_guild()).lower()
        history = user.get_goal_history(type)

        # Build embedded response.
        embed = discord.Embed(title=lib.get_string('goal:history', user.get_guild()).format(type_string), color=10038562)

        # Loop through each history record.
        for record in history:

            title = record['date']
            text = str(record['result']) + '/' + str(record['goal'])
            text += ' :white_check_mark:' if record['completed'] else ''
            embed.add_field(name=title, value=text, inline=False)

        await context.send(embed=embed)

    async def run_check_all(self, context):
        """
        Print a table of all the user's goals.
        @param context:
        @return:
        """

        now = int(time.time())
        user = User(context.message.author.id, context.guild.id, context)
        embed = discord.Embed(title=lib.get_string('goals', user.get_guild()), color=10038562)

        for type in self.types:

            type_string = lib.get_string('goal:'+type, user.get_guild())
            goal = user.get_goal(type)
            if goal is not None:
                progress = user.get_goal_progress(type)
                seconds_left = goal['reset'] - now
                left = lib.secs_to_days(seconds_left)
                current_wordcount = progress['current']
                goal_wordcount = progress['goal']
                words_remaining = goal_wordcount - current_wordcount

                # If someone has already met their goal, we don't want to calculate how many words they have left
                if words_remaining <= 0:
                    words_remaining = 0

                text = lib.get_string('goal:yourgoal', user.get_guild()).format(type_string, goal['goal']) +  "\n"
                text += lib.get_string('goal:status', user.get_guild()).format(progress['percent'], type_string, current_wordcount, goal_wordcount) + "\n"
                text += lib.get_string('goal:timeleft', user.get_guild()).format(lib.format_secs_to_days(seconds_left), type_string)
                if type != self.GOAL_TYPE_DAILY:
                    days = left['days']
                    # if someone has, for instance, 3 days 2 hours, count that as 4 days (remainder of today + 3 days)
                    hours = left['hours']
                    days = days + (1 if hours > 0 else 0)
                    if words_remaining > 0:
                        average_wordcount_needed = math.ceil(words_remaining / days)
                        text += "\n" + lib.get_string('goal:rate', user.get_guild()).format(average_wordcount_needed, type_string)
                if words_remaining == 0:
                    # They met their goal!
                    text += "\n" + lib.get_string('goal:met:noxp', user.get_guild()).format(type_string, goal_wordcount)
            else:
                text = None

            embed.add_field(name=type_string, value=text, inline=False)

        # Send the message
        await context.send(embed=embed)

    async def run_time(self, context, type):
        """
        Check how long until the goal resets
        :param context:
        :param type:
        :return:
        """
        user = User(context.message.author.id, context.guild.id, context)

        # Get the goal of this type for this user
        goal = user.get_goal(type)
        if goal:

            now = int(time.time())
            reset = goal['reset']
            left = lib.format_secs_to_days(reset - now)
            return await context.send(user.get_mention() + ', ' + lib.get_string('goal:timeleft', user.get_guild()).format(left, type))

        else:
            return await context.send(user.get_mention() + ', ' + lib.get_string('goal:nogoal', user.get_guild()).format(type, type))



    async def run_cancel(self, context, type):

        user = User(context.message.author.id, context.guild.id, context)
        user.delete_goal(type)
        return await context.send(user.get_mention() + ', ' + lib.get_string('goal:givenup', user.get_guild()))

    async def run_set(self, context, type, amount):

        user = User(context.message.author.id, context.guild.id, context)

        # Check if we can convert the amount to an int
        amount = lib.is_number(amount)
        if not amount:
            return await context.send(user.get_mention() + ', ' + lib.get_string('err:validamount', user.get_guild()))

        # Set the user's goal
        user.set_goal(type, amount)
        timezone = user.get_setting('timezone') or 'UTC'

        reset_every = lib.get_string('goal:set:'+type, user.get_guild())
        return await context.send(user.get_mention() + ', ' + lib.get_string('goal:set', user.get_guild()).format(type, amount, reset_every, timezone))

    async def run_check(self, context, type):

        user = User(context.message.author.id, context.guild.id, context)
        type_string = lib.get_string('goal:' + type, user.get_guild())

        user_goal = user.get_goal(type)
        if user_goal:
            progress = user.get_goal_progress(type)
            return await context.send(user.get_mention() + ', ' + lib.get_string('goal:status', user.get_guild()).format(progress['percent'], type_string, progress['current'], progress['goal']))
        else:
            return await context.send(user.get_mention() + ', ' + lib.get_string('goal:nogoal', user.get_guild()).format(type_string, type))


def setup(bot):
    bot.add_cog(Goal(bot))