import discord
from discord.ext import commands
import discord.context_managers
import os
from base.logging import Logger
from services.config_handler import ConfigHandler
from services.boss_handler import BossHandler
from services.player_handler import PlayerHandler
from services.session_handler import StateHandler
from services.vote_handler import VoteHandler
from modules.objects.boss import LocalBoss, Boss
from modules.dtos.boss_emoji_data import BossEmoji
from modules.logic.image_gen import combine_images
from modules.objects.player import Player
from modules.state.session import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from modules.state.event_state import EventState
from services.async_timer import AsyncTimer

class DiscordHandler(Logger):
    def __init__(self,config_handler:ConfigHandler,state_hanlder:StateHandler):
        super().__init__()
        # Create Bot
        intents = discord.Intents.default()
        intents.presences = True
        intents.message_content = True
        intents.members = True
        self.bot:commands.Bot = commands.Bot(command_prefix="!", intents=intents)
        # initialize handlers ---------------------------------
        self.__config_handler:ConfigHandler = config_handler
        self.__boss_handler:BossHandler = BossHandler(config_handler.paths.filepath_boss_data)
        self.__player_handler:PlayerHandler = PlayerHandler(config_handler.paths.filepath_player_data,self.__config_handler.api_state)
        self.__session_handler:StateHandler = state_hanlder
        self.__vote_handler:VoteHandler = None #vote handler will be created when needed, and deleted when not in use
        self.__valid_emojis:list[str] = ['🇦', '🇧', '🇨', '🇩']
        # scheduled events -------------------------------------
        self.grace_seconds:int = 60
        event_schedule:EventState = self.__config_handler.get_event_state()
        self.scheduler:AsyncIOScheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.open_voting_logic, 'cron', day_of_week=event_schedule.vote_open_day, hour=event_schedule.vote_open_hour, minute=event_schedule.vote_open_minute,misfire_grace_time=self.grace_seconds)
        self.scheduler.add_job(self.close_voting_logic, 'cron', day_of_week=event_schedule.vote_close_day, hour=event_schedule.vote_close_hour, minute=event_schedule.vote_close_minute,misfire_grace_time=self.grace_seconds)
        self.scheduler.add_job(self.open_tracking_logic, 'cron', day_of_week=event_schedule.tracking_start_day, hour=event_schedule.tracking_start_hour, minute=event_schedule.tracking_start_minute,misfire_grace_time=self.grace_seconds)
        self.scheduler.add_job(self.close_tracking_logic, 'cron', day_of_week=event_schedule.tracking_stop_day, hour=event_schedule.tracking_stop_hour, minute=event_schedule.tracking_stop_minute,misfire_grace_time=self.grace_seconds)
        # scheduled updates for active tracking handler
        self.update_timer:AsyncTimer = None
        # events
        @self.bot.event
        async def on_ready():
            await self.dlog(f"Bot is ready.  Logged in as {self.bot.user.name}")
            #if tracking is active, start the periodic updates
            if self.__session_handler.get_current_session().tracking_active:
                await self.dlog("Bot was (re)started during tracking active phase. Starting periodic updates...")
                await self.start_periodic_updates()
            #if voting is active, restart the voting phase
            if self.__session_handler.get_current_session().voting_active:
                await self.dlog("Bot was (re)started during voting active phase. Restarting voting phase...")
                await self.open_voting_logic()

        @self.bot.event
        async def on_reaction_add(reaction:discord.Reaction,user:discord.User):
            #ignore bot and check channel
            # if not in a voting session, ignore
            if user.bot: return
            if not self.check_channel(self.__config_handler.get_discord_state().voting_channel_id,reaction.message.channel.id): return
            if not self.__session_handler.get_current_session().voting_active: return
            if not self.__vote_handler:
                self.dlog(f"Error: vote handler not set but voting is open.  Ignoring reaction.")
                return
            if not self.reaction_valid(reaction.emoji):
                #remove it
                await reaction.remove(user)
                return
            #check if user has already been linked to an osrs name
            if not self.__player_handler.discord_name_exists(user.name):
                #remove it
                await reaction.remove(user)
                await self.dlog(f"Could not add vote for {user.name}: user has not been linked to an OSRS name.")
                return
            previous_reaction:str = self.__vote_handler.get_previous_reaction(user.name)
            if previous_reaction:
                #remove previous reaction
                await reaction.message.remove_reaction(previous_reaction,user)
            #add the vote
            if not self.__vote_handler.add_vote(user.name,reaction.emoji):
                await self.dlog(f"Error adding vote for {user.name} with emoji {reaction.emoji}")
                return
        
        @self.bot.event
        async def on_reaction_remove(reaction:discord.Reaction,user:discord.User):
            #ignore bot and check channel
            # if not in a voting session, ignore
            if user.bot: return
            if not self.check_channel(self.__config_handler.get_discord_state().voting_channel_id,reaction.message.channel.id): return
            if not self.__session_handler.get_current_session().voting_active: return
            if not self.__vote_handler:
                self.dlog(f"Error: vote handler not set but voting is open.  Ignoring reaction.")
                return
            if not self.reaction_valid(reaction.emoji):
                return
            if not self.__player_handler.discord_name_exists(user.name):
                return
            #remove the vote
            if not self.__vote_handler.remove_vote(user.name,reaction.emoji):
                await self.dlog(f"Error removing vote for {user.name} with emoji {reaction.emoji}.  The vote did not exist.")
                return

        @self.bot.event
        async def on_message(message:discord.Message):
            await self.bot.process_commands(message)
            channel:int = message.channel.id
            if self.check_channel(self.__config_handler.get_discord_state().console_channel_id,channel) or self.check_channel(self.__config_handler.get_discord_state().set_name_channel_id):
                print(f"message: {message.author.name} | {message.content}")

        # commands --------------------------------------------------------------------------------------------------
        # commands --------------------------------------------------------------------------------------------------
        # commands --------------------------------------------------------------------------------------------------
        @self.bot.command(help="!set_name <osrs name> - link osrs name to user.")
        async def set_name(ctx:commands.Context, *name:str):
            #ignore bot and check channel
            if ctx.author.bot: return
            if not self.check_channel(self.__config_handler.get_discord_state().set_name_channel_id,ctx.channel.id): return
            #see if the discord author is already linked
            existing_osrs_name:str = self.__player_handler.get_osrs_name(ctx.author.name)
            if existing_osrs_name:
                await self.send_message(ctx.channel.id,f"Discord name '{ctx.author.name}' is already linked to {existing_osrs_name}")
                return
            #set the name
            desired_name = " ".join(name).strip().lower()
            response:int = await self.__player_handler.add(ctx.author.name,desired_name,self.__boss_handler.get_bosses())
            if response == -2: #save error occurred
                await self.send_message(ctx.channel.id,f"Error saving player to disc: {ctx.author.name} | {desired_name}")
            elif response == -1: #no response from api check (likely invalid username)
                await self.send_message(ctx.channel.id,f"No response from API check for {desired_name}.  Either the service is down, or the username is invalid.  Player not added")
            elif response == 0: #player already exists
                discord_linked_osrs_name:str = self.__player_handler.get_osrs_name(ctx.author.name)
                osrs_linked_discord_name:str = self.__player_handler.get_discord_name(desired_name)
                if discord_linked_osrs_name:
                    await self.send_message(ctx.channel.id,f"Discord name '{ctx.author.name}' is linked to {discord_linked_osrs_name}")
                if osrs_linked_discord_name:
                    await self.send_message(ctx.channel.id,f"OSRS name '{desired_name}' is linked to {osrs_linked_discord_name}")
            elif response == 1: #player added
                await self.send_message(ctx.channel.id,f"Added player: '{ctx.author.name}' linked to '{desired_name}'")
        
        @self.bot.command(help="!clear_name <osrs name> - remove osrs name link.")
        async def clear_name(ctx:commands.Context, *name:str):
            # ignore bot and check channel and check for admin
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            desired_name:str = " ".join(name).strip().lower()
            response:bool = self.__player_handler.remove(desired_name)
            if response:
                await self.dlog(f"Removed player {desired_name}")
            else:
                await self.dlog(f"Player {desired_name} does not exist")

        @self.bot.command(help="Admin command to clear the link between a discord name and an OSRS name.  Usage: !clear_name <osrs name>")
        async def remove(ctx:commands.Context, *name:str):
            await clear_name(ctx,name)

        @self.bot.command(help="Clear console channel of message.")
        async def clear_console(ctx:commands.Context):
            # ignore bot and check channel and check for admin
            print(f"Clear console command {ctx.author.name}")
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            await self.clear_messages(ctx.channel.id)
            
        @self.bot.command(help="Clear voting channel.")
        async def clear_voting(ctx:commands.Context):
            # ignore bot and check channel and check for admin
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            await self.clear_messages(self.__config_handler.get_discord_state().voting_channel_id)

        @self.bot.command(help="Clear leaderboard channel.")
        async def clear_leaderboard(ctx:commands.Context):
            # ignore bot and check channel and check for admin
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            await self.clear_messages(self.__config_handler.get_discord_state().leaderboard_channel_id)

        @self.bot.command(help="Clear set-name channel.")
        async def clear_set_name(ctx:commands.Context):
            # ignore bot and check channel and check for admin
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            await self.clear_messages(self.__config_handler.get_discord_state().set_name_channel_id)

        @self.bot.command(help="!clear_channel <channel_id:int> - clear a channel.")
        async def clear_channel(ctx:commands.Context,channel_id:str):
            # ignore bot and check channel and check for admin
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            await self.clear_messages(int(channel_id.strip()))

        @self.bot.command(help="Clear bot channels.")
        async def clear_channels(ctx:commands.Context):
            # ignore bot and check channel and check for admin
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            await self.clear_messages(self.__config_handler.get_discord_state().voting_channel_id)
            await self.clear_messages(self.__config_handler.get_discord_state().leaderboard_channel_id)
            await self.clear_messages(self.__config_handler.get_discord_state().set_name_channel_id)
            await self.clear_messages(self.__config_handler.get_discord_state().console_channel_id)

        @self.bot.command(help="Force set session to 'none'.")
        async def no_session(ctx:commands.Context):
            # ignore bot and check channel and check for admin
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            if self.__session_handler.reset_session():
                await self.update_leaderboard()
                await self.dlog("Successfully set session to 'no session'")
            else:
                await self.dlog("Erro setting session to 'no session'")

        @self.bot.command(help="Force-open voting session.")
        async def open_voting(ctx:commands.Context):
            # ignore bot and check channel and check for admin
            print(f"ctx.author.bot: {ctx.author.bot} open_voting")
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            await self.open_voting_logic()
            
        @self.bot.command(help="Force-close voting session.")
        async def close_voting(ctx:commands.Context):
            # ignore bot and check channel and check for admin
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            await self.close_voting_logic()

        @self.bot.command(help="View bot/session status.")
        async def status(ctx:commands.Context):
            # ignore bot and check channel and check for admin
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            session:Session = self.__session_handler.get_current_session()
            message:str = f"Session Status:\n"
            if session.voting_active: 
                message += f"Voting Active\n"
                message += f"Boss Pool:\n"
                for boss in session.boss_pool: message += f"\t{boss.name} | {boss.level} | {boss.location}\n"
            if session.tracking_active: 
                message += f"Tracking Active\n"
                message += f"Current Boss: {session.current_boss.name} | {session.current_boss.level} | {session.current_boss.location}\n" if session.current_boss else "Current Boss: None\n"
            if not session.voting_active and not session.tracking_active: 
                message += f"No Session Active\n"
                if session.current_boss:
                    message += f"Current boss: {session.current_boss.name} | {session.current_boss.level} | {session.current_boss.location}\n" if session.current_boss else "Current Boss: None\n"
                else:
                    message += "Current boss: None\n"
                if session.last_boss:
                    message += f"Last boss: {session.last_boss.name} | {session.last_boss.level} | {session.last_boss.location}\n"
                else:
                    message += "Last boss: None\n"
                message += "Boss Pool:\n"
                if len(session.boss_pool) == 0:
                    message += "\tNone\n"
                else:
                    for boss in session.boss_pool: message += f"\t{boss.name} | {boss.level} | {boss.location}\n"
            await self.dlog(message)

        @self.bot.command(help="Force-start tracking current boss.")
        async def start_tracking(ctx:commands.Context):
            # ignore bot and check channel and check for admin
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            await self.open_tracking_logic()

        @self.bot.command(help="Force-stop tracking current boss.")
        async def stop_tracking(ctx:commands.Context):
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            await self.close_tracking_logic()

        @self.bot.command(help="View session details.")
        async def session_details(ctx:commands.Context):
            # ignore bot and check channel and check for admin
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            session:Session = self.__session_handler.get_current_session()
            message:str = f"Session Details:\n"
            message += f"Tracking Active: {session.tracking_active}\n"
            message += f"Voting Active: {session.voting_active}\n"
            message += f"Current Boss: {session.current_boss.name} | {session.current_boss.level} | {session.current_boss.location}\n" if session.current_boss else "Current Boss: None\n"
            message += f"Last Boss: {session.last_boss.name} | {session.last_boss.level} | {session.last_boss.location}\n" if session.last_boss else "Last Boss: None\n"
            message += f"Boss Pool:\n"
            if len(session.boss_pool) == 0:
                message += "\tNone\n"
            else:
                for boss in session.boss_pool: message += f"\t{boss.name} | {boss.level} | {boss.location}\n"
            message += f"Start Time: {session.start_time}\n"
            message += f"Used Bosses:\n"
            if len(session.used_boss_list) == 0:
                message += "\tNone\n"
            else:
                for boss in session.used_boss_list: message += f"\t{boss.name}\n"
            await self.dlog(message)

        @self.bot.command(help="!set_boss <boss_name:str> - Force-set current boss.")
        async def set_boss(ctx:commands.Context, *boss:str):
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            await self.send_message("NOT IMPLEMENTED YET. discord_handler.py")

        @self.bot.command(help="!stats <osrs name:str> or !stats <discord name:str> - view player stats.")
        async def stats(ctx:commands.Context, *username:str):
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            check_name_str:str = " ".join(username)
            osrs_name:str = self.__player_handler.get_osrs_name(check_name_str)
            discord_name:str = self.__player_handler.get_discord_name(check_name_str)
            player_list:list[Player] = self.__player_handler.get_players()
            player:Player = None
            for p in player_list:
                if p.osrs_name == osrs_name or p.discord_name == discord_name:
                    player = p
                    break
            if not player:
                await self.dlog(f"Error viewing player: player {check_name_str} does not exist")
                return
            message_lines:list[str] = []
            message_lines.append(f"Player: {player.osrs_name} | {player.discord_name}")
            for boss in player.boss_list:
                message_lines.append(f"{boss.name} | {boss.kills} | {boss.tracked_kills}")
            messages:list[str] = []
            #split the message into 2000 character chunks
            message:str = ""
            for line in message_lines:
                if len(message + line) > 2000:
                    messages.append(message)
                    message = ""
                message += line + "\n"
            messages.append(message)
            for message in messages:
                await self.dlog(message)

        @self.bot.command(help="!update <osrs name:str> or !update <discord name:str> - update player API data.")
        async def update(ctx:commands.Context, *username:str):
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            check_name_str:str = " ".join(username)
            osrs_name:str = self.__player_handler.get_osrs_name(check_name_str)
            discord_name:str = self.__player_handler.get_discord_name(check_name_str)
            if not osrs_name and not discord_name:
                await self.dlog(f"Error updating player: player {check_name_str} does not exist")
                return
            player:Player = None
            player_list:list[Player] = self.__player_handler.get_players()
            for p in player_list:
                if p.osrs_name == osrs_name or p.discord_name == discord_name:
                    player = p
                    break
            if not player:
                await self.dlog(f"Error updating player: player {check_name_str} does not exist")
                return
            await self.dlog(f"Updating player {check_name_str}. this may take a moment depending on rate limits and last update time...")
            if not await self.__player_handler.update_player(player.osrs_name,not self.__session_handler.get_current_session().tracking_active):
                await self.dlog(f"Error updating player: player {check_name_str} does not exist")
                return
            await self.dlog(f"Successfully updated player {check_name_str}")

        @self.bot.command(help="List all bosses.")
        async def list_bosses(ctx:commands.Context):
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            message:str = "Bosses:\n"
            if not self.__boss_handler.get_bosses():
                message += "\tNone"
            else:
                for boss in self.__boss_handler.get_bosses():
                    message += f"\t{boss.name} | {boss.level} | {boss.location}\n"

        @self.bot.command(help="List all player associations.")
        async def list_users(ctx:commands.Context):
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            message:str = "User Associations (Discord | OSRS):\n"
            if not self.__player_handler.get_players():
                message += "\tNone"
            else:
                for player in self.__player_handler.get_players():
                    message += f"\t{player.discord_name} | {player.osrs_name}\n"
            await self.dlog(message)

        @self.bot.command(help="Clear previously used bosses (allow them to be used again).")
        async def clear_used_bosses(ctx:commands.Context):
            if ctx.author.bot: return
            if not self.__is_admin(ctx.author.name): return
            if not self.check_channel(self.__config_handler.get_discord_state().console_channel_id,ctx.channel.id): return
            if self.__session_handler.clear_used_bosses():
                await self.dlog("Cleared used bosses")
            else:
                await self.dlog("Error clearing used bosses")

    async def run(self):
        self.scheduler.start()
        await self.bot.start(self.__config_handler.get_discord_state().bot_token)


    # logic functions for open/close voting, and open/close tracking.  to be used with both commands and scheduler: ----------------
    async def open_voting_logic(self):
        # check if voting is already open
        if self.__session_handler.get_current_session().voting_active:
            await self.dlog("Error opening voting: voting is already open")
            return
        # set session to open voting
        if self.__session_handler.open_voting(self.__boss_handler.get_bosses()):
            await self.dlog("Successfully set session to voting. generating message...")
        else:
            await self.dlog("Error opening voting")
        # get the boss pool for this vote
        boss_pool:list[LocalBoss] = self.__session_handler.get_current_session().boss_pool
        #check we have 4 reactions and 4 bosses in the pool
        if len(boss_pool) != 4 or len(self.__valid_emojis) != 4:
            await self.dlog("Error opening voting: boss pool or emojis not set correctly")
            return
        boss_emoji_list:list[BossEmoji] = []
        for int in range(4):
            boss_emoji_list.append(BossEmoji(boss_pool[int],self.__valid_emojis[int]))
        self.__vote_handler = VoteHandler(boss_emoji_list)
        # clear the voting channel
        await self.clear_messages(self.__config_handler.get_discord_state().voting_channel_id)
        # generate an image for the voting message
        image_paths:list[str] = []
        for boss_emoji in boss_emoji_list:
            image_paths.append(os.path.join(self.__config_handler.paths.filepath_image_folder,boss_emoji.boss.image))
        image_path:str = combine_images(image_paths,self.__config_handler.paths.folder_path_generated_image)
        # send a voting message
        message:str = "Boss Pool:"
        for boss_emoji in boss_emoji_list:
            message += f"\n{boss_emoji.emoji} : {boss_emoji.boss.name} | {boss_emoji.boss.level} | {boss_emoji.boss.location}"
        if message[:-1] == "\n": message = message[:-1]
        last_message:discord.Message = await self.send_embed(
            channel_id=self.__config_handler.get_discord_state().voting_channel_id,
            title="Voting is now Open! Vote for the next boss!",
            message=message,
            image_path=image_path
        )
        if not last_message:
            await self.dlog("Error sending voting message")
            return
        # add reactions to the message
        for emoji in self.__valid_emojis:
            await last_message.add_reaction(emoji)
        await self.dlog("Voting is now open! Vote for the next boss!")
        await self.update_leaderboard()

    async def close_voting_logic(self):
        # check if voting is open
        if not self.__session_handler.get_current_session().voting_active:
            await self.dlog("Error closing voting: voting is not open")
            return
        # tally the votes
        winning_boss:LocalBoss = self.__vote_handler.tally_votes() if self.__vote_handler and self.__vote_handler.tally_votes() else self.__session_handler.get_current_session().boss_pool[0]
        
        # clear the voting channel
        await self.clear_messages(self.__config_handler.get_discord_state().voting_channel_id)
        if self.__session_handler.close_voting(winning_boss):
            await self.dlog("Successfully closed voting.  Generating message...")
        else:
            await self.dlog("Error closing voting")
        # create an embed for the winning boss
        await self.send_embed(
            channel_id=self.__config_handler.get_discord_state().voting_channel_id,
            title="Voting is now Closed! The winning boss is...",
            message=f"{winning_boss.name} | {winning_boss.level} | {winning_boss.location}",
            image_path=os.path.join(self.__config_handler.paths.filepath_image_folder,winning_boss.image)
        )
        # update the leaderboard
        await self.update_leaderboard()
        await self.dlog(f"Voting is now closed! Boss set to {winning_boss.name}")
    
    async def open_tracking_logic(self):
        # check if we have everything to start tracking
        current_session:Session = self.__session_handler.get_current_session()
        if current_session.tracking_active:
            await self.dlog("Error starting tracking: tracking is already active")
            return
        if current_session.voting_active:
            await self.dlog("Error starting tracking: voting is still active")
            return
        #update leaderboard
        await self.dlog(f"Updating player baseline data...")
        await self.update_leaderboard()
        if not self.__session_handler.open_tracking(self.__session_handler.get_current_session().current_boss):
            await self.dlog(f"Could not open tracking with session data.  attempting to use vote handler data...")
            if self.__vote_handler and self.__vote_handler.selected_boss:
                if not self.__session_handler.open_tracking(self.__vote_handler.selected_boss):
                    await self.dlog("Error starting tracking")
                    return
            else:
                await self.dlog("Error starting tracking: No session data or vote handler data to start tracking with.")
                return
        await self.dlog(f"Successfully started tracking for {current_session.current_boss.name} | {current_session.current_boss.level} | {current_session.current_boss.location}")
        #update leaderboard during active tracking session
        await self.update_leaderboard()
        #start periodic updates
        await self.start_periodic_updates()

    async def close_tracking_logic(self):
        #stop periodic updates
        await self.stop_periodic_updates()
        #update leaderboard
        await self.dlog("Updating leaderboard for final results before closing tracking...")
        await self.update_leaderboard()
        await self.dlog("Final leaderboard update complete. Closing tracking...")
        if not self.__session_handler.close_tracking():
            await self.dlog("Error stopping tracking")
        else:
            await self.dlog("Successfully stopped tracking")
        # update leaderboard without resetting baseline data
        await self.update_leaderboard(False)

    async def start_periodic_updates(self):
        """This will be called by open_tracking_logic to start the periodic updates for the current boss."""
        update_interval_seconds:int = self.__config_handler.api_state.bulk_update_frequency_minutes * 60
        self.update_timer = AsyncTimer(update_interval_seconds,self.update_leaderboard)
        await self.dlog(f"Periodic updates should now be running for the active tracking session every {str(self.__config_handler.api_state.bulk_update_frequency_minutes)} minutes.")

    async def stop_periodic_updates(self):
        """This will be called by close_tracking_logic to stop the periodic updates for the current boss."""
        self.update_timer.stop()
        self.update_timer = None
        await self.dlog("Periodic updates have been stopped.")
    # end logic functions -----------------------------------------

    # discord functions -----------------------------------------
    async def send_message(self,channel_id:int,message:str) -> discord.Message:
        """Send a message to a channel.  channel_id is the id of the channel to send the message to.  message is the text to send."""
        channel:discord.TextChannel = self.bot.get_channel(channel_id)
        return await channel.send(message)

    async def send_embed(self,channel_id:int, title:str, message:str, image_path:str) -> discord.Message:
        """Send an embed with an image to a channel.  title displayed at top.  message is text body.
        image_path is the path to the image file"""
        # check if image exists
        if not os.path.exists(image_path):
            self.warn(self,f"Image path does not exist: {image_path}",self.send_embed)
            return None
        # create image file
        try:
            image = discord.File(image_path, filename=os.path.basename(image_path))
        except Exception as e:
            self.error(self,f"Bot.send_embed() : Failed to create image file: {e}",self.send_embed)
            return None
        # get channel
        channel = self.bot.get_channel(channel_id)
        # create embed
        embed = discord.Embed(title=title, description=message)
        return await channel.send(embed=embed, file=image)
    
    async def remove_message(self,channel_id:int,message_id:int):
        """Remove a message from a channel.  channel_id is the id of the channel to remove the message from.  message_id is the id of the message to remove."""
        channel:discord.TextChannel = self.bot.get_channel(channel_id)
        message:discord.Message = await channel.fetch_message(message_id)
        await message.delete()

    async def clear_messages(self,channel_id:int,limit:int=None):
        """Clear all messages from a channel.  channel_id is the id of the channel to clear."""
        channel:discord.TextChannel = self.bot.get_channel(channel_id)
        async for message in channel.history(limit=limit):
            await message.delete()

    def __is_admin(self,discord_name:str):
        """Check if a discord user is an admin.  discord_name is the name of the user to check."""
        for admin in self.__config_handler.get_discord_state().discord_admin_list:
            if discord_name.lower() == admin.lower():
                return True
        return False
    
    async def dlog(self,message:str):
        """Log a message to the console channel.  message is the message to log."""
        await self.send_message(self.__config_handler.get_discord_state().console_channel_id,message)

    def check_channel(self,desired_channel_id:int,channel_id:int) -> bool:
        """Checks to see if the desired channel id is set (from discord state ideally) and if so, if it matches the channel id provided (from ctx channel ideally)
        If the desired channel is none, -1, 0, or matches the channel_id, returns True. False otherwise."""
        if desired_channel_id is None or desired_channel_id == -1 or desired_channel_id == 0 or desired_channel_id == channel_id:
            return True
        return False

    def reaction_valid(self,reaction_emoji:str) -> bool:
        """Checks if a reaction emoji is valid.  Returns True if it is, False otherwise."""
        if reaction_emoji in self.__valid_emojis:
            return True
        return False
    
    async def update_leaderboard(self,update_players:bool=True):
        """Update the leaderboard channel with updated api player data, and an embed of relevant data."""
        session:Session = self.__session_handler.get_current_session()
        channel_id:int = self.__config_handler.get_discord_state().leaderboard_channel_id
        players:list[Player] = self.__player_handler.get_players()
        tracking_status:bool = session.tracking_active
        current_boss:LocalBoss = session.current_boss or None
        last_boss:LocalBoss = session.last_boss or None
        boss_to_show:LocalBoss = None
        boss_title:str = ""
        if session.tracking_active:
            boss_to_show = current_boss
            boss_title = "Current Boss:"
        else:
            boss_to_show = last_boss
            boss_title = "Last Boss:"
        if not boss_to_show and not tracking_status:
            boss_to_show = current_boss
            boss_title = "Next Boss:"
        if not boss_to_show:
            await self.clear_messages(channel_id)
            await self.dlog("Error updating leaderboard: no boss to show")
            await self.send_message(channel_id, "Leaderboard:\nNo current or previous boss data")
            return
        title:str = "Tracking is Active" if tracking_status else "Tracking is Inactive"
        title += f"\n{boss_title} {boss_to_show.name} | {boss_to_show.level} | {boss_to_show.location}" if boss_to_show else "No Current Boss"
        #update players from api
        if update_players:
            await self.send_message(channel_id,"Updating all players...")
            await self.__player_handler.update_all_players(not tracking_status)
            await self.send_message(channel_id,"Players updated.  Generating leaderboard...")
        #create message lines
        data_lines:list[dict] = []
        #grab data from players and put it in data_lines to be sorted by kills before displaying
        for player in players:
            active_boss:Boss = None
            for boss in player.boss_list:
                if boss.name == boss_to_show.api_name:
                    active_boss = boss
                    break
            if active_boss:
                data:dict = {
                    "discord_name":player.discord_name,
                    "osrs_name":player.osrs_name,
                    "tracked_kills":active_boss.tracked_kills,
                    "kills":active_boss.kills
                }
                data_lines.append(data)
            else:
                self.dlog(f"Error updating leaderboard: player {player.osrs_name} does not have boss {boss_to_show.api_name}")
        #sort data lines and create messsage
        message:str = "Leaderboard:\n"
        if data_lines:
            data_lines.sort(key=lambda x: x["tracked_kills"],reverse=True)
            for data in data_lines:
                kills:str = str(data["tracked_kills"])
                while len(kills) < 2:
                    kills = "0" + kills
                message += f"     Kills: {kills} -- {data['discord_name']} | {data['osrs_name']}"
        else:
            message += "No data to display"
        #clear channel
        await self.clear_messages(channel_id)
        #send message
        await self.send_embed(
            channel_id=channel_id,
            title=title,
            message=message,
            image_path=os.path.join(self.__config_handler.paths.filepath_image_folder,boss_to_show.image)
        )