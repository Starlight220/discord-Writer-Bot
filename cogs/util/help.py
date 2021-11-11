import discord
import lib
from discord.ext import commands
from structures.user import User
from structures.wrapper import CommandWrapper

class Help(commands.Cog, CommandWrapper):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    @commands.guild_only()
    async def help(self, context, command="help"):
        """
        Help command and subcommands
        """

        user = User(context.message.author.id, context.guild.id, context)

        command = command.lower()

        config = lib.get('./settings.json')

        if command == "help":

            url = config.src + '/wiki/Commands' if config.src != "" else None

            help_embed = discord.Embed(title="Help with Writer Bot", description="For more help with a command run `help [command]`", color=discord.Color.blurple(), url=url)
            help_embed.add_field(name='`about`', value=lib.get_string('help:about', user.get_guild()), inline=True)
            help_embed.add_field(name='`ask`', value=lib.get_string('help:ask', user.get_guild()), inline=True)
            help_embed.add_field(name='`challenge`', value=lib.get_string('help:challenge', user.get_guild()), inline=True)
            help_embed.add_field(name='`8ball`', value=lib.get_string('help:8ball', user.get_guild()), inline=True)
            help_embed.add_field(name='`event`', value=lib.get_string('help:event', user.get_guild()), inline=True)
            help_embed.add_field(name='`flip`', value=lib.get_string('help:flip', user.get_guild()), inline=True)
            help_embed.add_field(name='`goal`', value=lib.get_string('help:goal', user.get_guild()), inline=True)
            help_embed.add_field(name='`mysetting`', value=lib.get_string('help:mysetting', user.get_guild()), inline=True)
            help_embed.add_field(name='`ping`', value=lib.get_string('help:ping', user.get_guild()), inline=True)
            help_embed.add_field(name='`profile`', value=lib.get_string('help:profile', user.get_guild()), inline=True)
            help_embed.add_field(name='`project`', value=lib.get_string('help:project', user.get_guild()), inline=True)
            help_embed.add_field(name='`quote`', value=lib.get_string('help:quote', user.get_guild()), inline=True)
            help_embed.add_field(name='`reassure`', value=lib.get_string('help:reassure', user.get_guild()), inline=True)
            help_embed.add_field(name='`reset`', value=lib.get_string('help:reset', user.get_guild()), inline=True)
            help_embed.add_field(name='`remind`', value=lib.get_string('help:remind', user.get_guild()), inline=True)
            help_embed.add_field(name='`roll`', value=lib.get_string('help:roll', user.get_guild()), inline=True)
            help_embed.add_field(name='`sprint`', value=lib.get_string('help:sprint', user.get_guild()), inline=True)
            help_embed.add_field(name='`wrote`', value=lib.get_string('help:wrote', user.get_guild()), inline=True)
            help_embed.add_field(name='`xp`', value=lib.get_string('help:xp', user.get_guild()), inline=True)
            help_embed.add_field(name='`help`', value=lib.get_string('help:help', user.get_guild()), inline=True)

            return await context.send(embed=help_embed)

        elif command == 'about':
            about_embed=discord.Embed(title="Help with `about` command.", color=3897943)
            about_embed.add_field(name="`about`", value=lib.get_string("help:aboutSub", user.get_guild()), inline=True)

            return await context.send(embed=about_embed)

        elif command == 'ask':
            ask_embed=discord.Embed(title="Help with `ask` command.", color=3897943)
            ask_embed.add_field(name='`ask char`', value=lib.get_string('help:askCharSub', user.get_guild()), inline=True)
            ask_embed.add_field(name='`ask world`', value=lib.get_string('help:askWorldSub', user.get_guild()), inline=True)
            ask_embed.set_footer(text=lib.get_string('help:askFooter', user.get_guild()))

            return await context.send(embed=ask_embed)

        elif command == 'challenge':
            challenge_embed=discord.Embed(title="Help with `challenge` command.", color=3897943)
            challenge_embed.add_field(name='`challenge`', value=lib.get_string('help:challengeSub', user.get_guild()), inline=True)
            challenge_embed.add_field(name='`challenge easy`', value=lib.get_string('help:challengeEasySub', user.get_guild()), inline=True)
            challenge_embed.add_field(name='`challenge normal`', value=lib.get_string('help:challengeNormalSub', user.get_guild()), inline=True)
            challenge_embed.add_field(name='`challenge hard`', value=lib.get_string('help:challengeHardSub', user.get_guild()), inline=True)
            challenge_embed.add_field(name='`challenge hardcore`', value=lib.get_string('help:challengeHardcoreSub', user.get_guild()), inline=True)
            challenge_embed.add_field(name='`challenge insane`', value=lib.get_string('help:challengeInsaneSub', user.get_guild()), inline=True)
            challenge_embed.add_field(name='`challenge 10wpm`', value=lib.get_string('help:challenge10wpmSub', user.get_guild()), inline=True)
            challenge_embed.add_field(name='`challenge 15m`', value=lib.get_string('help:challenge15Sub', user.get_guild()), inline=True)
            challenge_embed.add_field(name='`challenge normal 18m`', value=lib.get_string('help:challengeNormal18Sub', user.get_guild()), inline=True)
            challenge_embed.add_field(name='`challenge cancel`', value=lib.get_string('help:challengeCancelSub', user.get_guild()), inline=True)
            challenge_embed.add_field(name='`challenge complete`', value=lib.get_string('help:challengeCompleteSub', user.get_guild()), inline=True)
            challenge_embed.set_footer(text=lib.get_string('help:challengeFooter', user.get_guild()))

            return await context.send(embed=challenge_embed)

        elif command == '8ball':
            ball_embed=discord.Embed(title='Help with `8ball` command.', color=3897943)
            ball_embed.add_field(name='`8ball`', value=lib.get_string('help:8ballSub', user.get_guild()), inline=True)

            return await context.send(embed=ball_embed)

        elif command == 'event':
            event_embed=discord.Embed(title="Help with `event` command.", color=3897943)
            event_embed.add_field(name='`event create My event title`', value=lib.get_string('help:eventCreateSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event rename My New event title`', value=lib.get_string('help:eventRenameSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event description This is the description`', value=lib.get_string('help:eventDescSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event image https://i.imgur.com/tJtAdNs.png`', value=lib.get_string('help:eventImageSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event delete`', value=lib.get_string('help:eventDeleteSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event schedule`', value=lib.get_string('help:eventScheduleSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event unschedule`', value=lib.get_string('help:eventUnSchSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event start`', value=lib.get_string('help:eventStartSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event end`', value=lib.get_string('help:eventEndSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event time`', value=lib.get_string('help:eventTimeSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event update 500`', value=lib.get_string('help:eventUpdateSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event me`', value=lib.get_string('help:eventMeSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event top 20`', value=lib.get_string('help:eventTopSub', user.get_guild()), inline=True)
            event_embed.add_field(name='`event info`', value=lib.get_string('help:eventInfoSub', user.get_guild()), inline=True)
            event_embed.set_footer(text=lib.get_string('help:eventFooter', user.get_guild()))

            return await context.send(embed=event_embed)

        elif command == 'flip':
            flip_embed=discord.Embed(title="Help with `flip` command.", color=3897943)
            flip_embed.add_field(name='`flip`', value=lib.get_string('help:flipSub', user.get_guild()), inline=True)

            return await context.send(embed=flip_embed)

        elif command == 'generate':
            gen_embed=discord.Embed(title="Help with `generate` command.", color=3897943)
            gen_embed.add_field(name='`generate char`', value=lib.get_string('help:generateCharSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate place`', value=lib.get_string('help:generatePlaceSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate land`', value=lib.get_string('help:generateLandSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate book`', value=lib.get_string('help:generateBookSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate book_fantasy`', value=lib.get_string('help:generateBookFanSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate book_sf`', value=lib.get_string('help:generateBookSFSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate book_horror`', value=lib.get_string('help:generateBookHorrorSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate book_rom`', value=lib.get_string('help:generateBookRomSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate book_mystery`', value=lib.get_string('help:generateBookMysSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate book_hp`', value=lib.get_string('help:generateBookHPSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate idea`', value=lib.get_string('help:generateIdeaSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate prompt`', value=lib.get_string('help:generatePromptSub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate place 20`', value=lib.get_string('help:generatePlace20Sub', user.get_guild()), inline=True)
            gen_embed.add_field(name='`generate face`', value=lib.get_string('help:generateFace', user.get_guild()), inline=True)
            gen_embed.set_footer(text=lib.get_string('help:generateFooter', user.get_guild()))

            return await context.send(embed=gen_embed)

        elif command == 'goal':
            goal_embed=discord.Embed(title='Help with `goal` command.', color=3897943)
            goal_embed.add_field(name='`goal`', value=lib.get_string('help:goalSub', user.get_guild()), inline=True)
            goal_embed.add_field(name='`goal check daily`', value=lib.get_string('help:goalCheckSub', user.get_guild()), inline=True)
            goal_embed.add_field(name='`goal set weekly 500`', value=lib.get_string('help:goalSetSub', user.get_guild()), inline=True)
            goal_embed.add_field(name='`goal cancel monthly`', value=lib.get_string('help:goalCancelSub', user.get_guild()), inline=True)
            goal_embed.add_field(name='`goal time yearly`', value=lib.get_string('help:goalTimeSub', user.get_guild()), inline=True)
            goal_embed.add_field(name='`goal history monthly`', value=lib.get_string('help:goalHistorySub', user.get_guild()), inline=True)
            goal_embed.add_field(name='`goal update yearly 12350`', value=lib.get_string('help:goalUpdateSub', user.get_guild()), inline=True)

            return await context.send(embed=goal_embed)

        elif command == 'mysetting' or command == 'myset':
            setting_embed=discord.Embed(title='Help with `mysetting` command.', color= 3897943, url=lib.get_string('help:mysettingUrlSub', user.get_guild()))
            setting_embed.add_field(name='`mysetting timezone America/New_York`', value=lib.get_string('help:mysettingTzSub', user.get_guild()), inline=True)
            setting_embed.set_footer(text=lib.get_string('help:mysetting:footer', user.get_guild()))

            return await context.send(embed=setting_embed)

        elif command == 'ping':
            ping_embed=discord.Embed(title='Help with `ping` command.', color=3897943)
            ping_embed.add_field(name='`ping`', value=lib.get_string('help:pingSub', user.get_guild()), inline=True)

            return await context.send(embed=ping_embed)

        elif command == 'profile':
            profile_embed=discord.Embed(title='Help with `profile` command.', color=3897943)
            profile_embed.add_field(name='`profile`', value=lib.get_string('help:profileSub', user.get_guild()), inline=True)

            return await context.send(embed=profile_embed)

        elif command == 'project':
            project_embed=discord.Embed(title='Help with `project` command.',  color=3897943)
            project_embed.add_field(name='`project create sword The Sword in the Stone`', value=lib.get_string('help:projectCreateSub', user.get_guild()), inline=True)
            project_embed.add_field(name='`project delete sword`', value=lib.get_string('help:projectDeleteSub', user.get_guild()), inline=True)
            project_embed.add_field(name='`project rename sword sword2 The Sword in the Stone Two`', value=lib.get_string('help:projectRenameSub', user.get_guild()), inline=False)
            project_embed.add_field(name='`project update sword 6500`', value=lib.get_string('help:projectUpdateSub', user.get_guild()), inline=True)
            project_embed.add_field(name='`project list`', value=lib.get_string('help:projectListSub', user.get_guild()), inline=True)
            project_embed.add_field(name='`project view sword`', value=lib.get_string('help:projectViewShortnameSub', user.get_guild()), inline=True)
            project_embed.add_field(name='`project status sword finished`', value=lib.get_string('help:projectStatusSub', user.get_guild()), inline=True)
            project_embed.add_field(name='`project genre sword fantasy`', value=lib.get_string('help:projectGenreSub', user.get_guild()), inline=True)
            project_embed.add_field(name='`project link sword http://yourwebsite.com/your-book`', value=lib.get_string('help:projectLinkSub', user.get_guild()), inline=True)
            project_embed.add_field(name='`project image sword http://yourwebsite.com/your-image.png`', value=lib.get_string('help:projectImageSub', user.get_guild()), inline=True)
            project_embed.add_field(name='`project description sword Boy finds sword. Boy becomes king.`', value=lib.get_string('help:projectDescSub', user.get_guild()), inline=True)

            return await context.send(embed=project_embed)

        elif command == 'quote':
            quote_embed=discord.Embed(title='Help with `quote` command.', color=387943)
            quote_embed.add_field(name='`quote`', value=lib.get_string('help:quoteSub', user.get_guild()), inline=True)

            return await context.send(embed=quote_embed)

        elif command == 'reassure':
            reassure_embed=discord.Embed(title='Help with `reassure` command.', color=3897943)
            reassure_embed.add_field(name='`reassure`', value=lib.get_string('help:reassureSub', user.get_guild()), inline=True)
            reassure_embed.add_field(name='`reassure @CMR`', value=lib.get_string('help:reassureUserSub', user.get_guild()), inline=True)

            return await context.send(embed=reassure_embed)

        elif command == 'reset':
            reset_embed=discord.Embed(title='Help with `reset` command.', color=3897943)
            reset_embed.add_field(name='`reset pb`', value=lib.get_string('help:resetPbSub', user.get_guild()), inline=True)
            reset_embed.add_field(name='`reset wc`', value=lib.get_string('help:resetWcSub', user.get_guild()), inline=True)
            reset_embed.add_field(name='`reset xp`', value=lib.get_string('help:resetXpSub', user.get_guild()), inline=True)
            reset_embed.add_field(name='`reset projects`', value=lib.get_string('help:reset:projects', user.get_guild()), inline=True)
            reset_embed.add_field(name='`reset all`', value=lib.get_string('help:resetAllSub', user.get_guild()), inline=True)

            return await context.send(embed=reset_embed)

        elif command == 'roll':
            roll_embed=discord.Embed(title='Help with `roll` command.', color=3897943)
            roll_embed.add_field(name='`roll`', value=lib.get_string('help:rollSub', user.get_guild()), inline=True)
            roll_embed.add_field(name='`roll 1d8`', value=lib.get_string('help:roll8Sub', user.get_guild()), inline=True)
            roll_embed.add_field(name='`roll 3d20`', value=lib.get_string('help:roll3d20Sub', user.get_guild()), inline=True)

            return await context.send(embed=roll_embed)

        elif command == 'sprint':
            sprint_embed=discord.Embed(title='Help with `sprint` Command.', color=3897943)
            sprint_embed.add_field(name='`sprint start`', value=lib.get_string('help:sprintStartSub', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint for 20 in 3`', value=lib.get_string('help:sprint20in3Sub', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint for 20 at .30`', value=lib.get_string('help:sprintForAt', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint cancel`', value=lib.get_string('help:sprintCancelSub', user.get_guild()), inline=False)
            sprint_embed.add_field(name='`sprint join`', value=lib.get_string('help:sprintJoinSub', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint join 100`', value=lib.get_string('help:sprintJoin100Sub', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint join 100 sword`', value=lib.get_string('help:sprintJoin100SwordSub', user.get_guild()), inline=False)
            sprint_embed.add_field(name='`sprint join edit`', value=lib.get_string('help:sprintJoinEdit', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint join same`', value=lib.get_string('help:sprintJoinSame', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint leave`', value=lib.get_string('help:sprintLeaveSub', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint project sword`', value=lib.get_string('help:sprintProjectSwordSub', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint time`', value=lib.get_string('help:sprintTimeSub', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint wc 250`', value=lib.get_string('help:sprintWc250Sub', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint pb`', value=lib.get_string('help:sprintPbSub', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint notify`', value=lib.get_string('help:sprintNotifySub', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint forget`', value=lib.get_string('help:sprintForgetSub', user.get_guild()), inline=True)
            sprint_embed.add_field(name='`sprint status`', value=lib.get_string('help:sprintStatusSub', user.get_guild()), inline=True)
            sprint_embed.set_footer(text=lib.get_string('help:sprintFooter', user.get_guild()))

            return await context.send(embed=sprint_embed)

        elif command == 'wrote':
            wrote_embed=discord.Embed(title='Help with `wrote` command', color=3897943)
            wrote_embed.add_field(name='`wrote 500`', value=lib.get_string('help:wroteSub', user.get_guild()), inline=True)
            wrote_embed.add_field(name='`wrote 500 sword`', value=lib.get_string('help:wroteprojectSub', user.get_guild()), inline=True)

            await context.send(content=None, embed=wrote_embed)

        elif command == 'xp':
            xp_embed=discord.Embed(title='Help with `xp` command.', color=3897943)
            xp_embed.add_field(name='`xp`', value=lib.get_string('help:xpSub', user.get_guild()), inline=True)
            xp_embed.add_field(name='`xp top`', value=lib.get_string('help:xpTopSub', user.get_guild()), inline=True)
            
            return await context.send(embed=xp_embed)

        elif command == 'remind':
            xp_embed = discord.Embed(title='Help with `remind` command.', color=3897943)
            xp_embed.add_field(name='`remind list`', value=lib.get_string('help:remind:list', user.get_guild()), inline=True)
            xp_embed.add_field(name='`remind delete`', value=lib.get_string('help:remind:delete', user.get_guild()), inline=True)
            xp_embed.add_field(name='`remind in 5 send hello everyone to #channel-name`', value=lib.get_string('help:remind:set:in', user.get_guild()), inline=True)
            xp_embed.add_field(name='`remind at 12:00 send hello everyone to #channel-name`', value=lib.get_string('help:remind:set:at', user.get_guild()), inline=True)
            xp_embed.add_field(name='`remind every hour from 16:05 send hello everyone to #channel-name`', value=lib.get_string('help:remind:set:every:hour', user.get_guild()), inline=True)
            xp_embed.add_field(name='`remind every day at 16:05 send hello everyone to #channel-name`', value=lib.get_string('help:remind:set:every:day', user.get_guild()), inline=True)
            xp_embed.add_field(name='`remind every week at 16:05 send hello everyone to #channel-name`', value=lib.get_string('help:remind:set:every:week', user.get_guild()), inline=True)
            return await context.send(embed=xp_embed)



def setup(bot):
    bot.add_cog(Help(bot))
