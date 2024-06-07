from base.logging import Logger
from modules.dtos.wise_old_man_data import WiseOldManPlayerData, WiseOldManBossData
from modules.objects.player import Player
from modules.objects.boss import Boss, LocalBoss
from modules.state.session import Session
from modules.state.discord_state import DiscordState
from modules.state.event_state import EventState
from modules.state.api_state import ApiState
import datetime
import json

class TimeParser(Logger):
    def __init__(self):
        super().__init__()

    def datetime_to_str(self,time:datetime.datetime) -> str:
        """Converts a datetime object to a string in the format YYYY-MM-DD HH:MM:SS. Returns an empty string if the time is None."""
        if not time:
            self.warn(self,"No time to convert to string",self.datetime_to_str)
            return ""
        self.log(self,f"Converting datetime to string",self.datetime_to_str)
        return time.strftime("%Y-%m-%d %H:%M:%S")
    
    def str_to_datetime(self,time_str:str) -> datetime.datetime:
        """Converts a string in the format YYYY-MM-DD HH:MM:SS to a datetime object. Returns None if the string is empty."""
        if not time_str:
            self.warn(self,"No time string to convert to datetime",self.str_to_datetime)
            return None
        self.log(self,f"Converting string to datetime",self.str_to_datetime)
        return datetime.datetime.strptime(time_str,"%Y-%m-%d %H:%M:%S")

class WiseOldManParser(Logger):
    def __init__(self):
        super().__init__()

    def json_to_object(self,player_data:dict) -> WiseOldManPlayerData:
        """Parses the player data from the WiseOldMan API into a WiseOldManPlayerData object. Returns None if the player data is invalid."""
        if not player_data:
            self.warn(self,"No player data to parse",self.json_to_object)
            return None
        try:
            username:str = player_data["username"]
            display_name:str = player_data["displayName"]
            snapshot_creation:str = player_data["latestSnapshot"]["createdAt"]
            boss_data:list[WiseOldManBossData] = []
            boss_names:dict = player_data["latestSnapshot"]["data"]["bosses"]
            for boss_name in boss_names:
                boss:dict = boss_names[boss_name]
                kills = boss["kills"]
                if kills < 0: kills = 0
                boss_data.append(WiseOldManBossData(boss["metric"],kills,boss["rank"],boss["ehb"]))
            self.log(self,f"Parsed player data for {username}",self.json_to_object)
            return WiseOldManPlayerData(username,display_name,snapshot_creation,boss_data)
        except Exception as e:
            self.error(self,f"Error parsing player data: {e}",self.json_to_object)

class PlayerParser(Logger):
    def __init__(self):
        super().__init__()

    def __player_boss_to_json(self,boss:Boss) -> dict:
        """Internal function to convert Boss object to a dictionary"""
        if not boss:
            self.warn(self,"No boss to convert to JSON",self.__player_boss_to_json)
            return {}
        #self.log(self,f"Converting boss {boss.name} to JSON",self.__player_boss_to_json)
        return {
            "name":boss.name,
            "kills":boss.kills,
            "tracked_kills":boss.tracked_kills,
            "kill_offset":boss.kill_offset
        }
    
    def __player_boss_json_to_object(self,boss_data:dict) -> Boss:
        """Internal function to convert a dictionary to a Boss object"""
        if not boss_data:
            self.warn(self,"No boss data to convert to object",self.__player_boss_json_to_object)
            return None
        #self.log(self,f"Converting boss data to object",self.__player_boss_json_to_object)
        boss:Boss = Boss(boss_data["name"],boss_data["kills"])
        boss.tracked_kills = boss_data["tracked_kills"]
        boss.kill_offset = boss_data["kill_offset"]
        return boss
    
    def player_to_json(self,player:Player) -> dict:
        """Converts a Player object to a dictionary for JSON serialization."""
        if not player:
            self.warn(self,"No player to convert to JSON",self.player_to_json)
            return {}
        self.log(self,f"Converting player {player.discord_name} to JSON",self.player_to_json)
        player_data:dict = {
            "discord_name":player.discord_name,
            "osrs_name":player.osrs_name,
            "bosses":[self.__player_boss_to_json(boss) for boss in player.boss_list]
        }
        return player_data
    
    def json_to_player(self,player_data:dict) -> Player:
        """Converts a dictionary to a Player object."""
        if not player_data:
            self.warn(self,"No player data to convert to object",self.json_to_player)
            return None
        self.log(self,f"Converting player data to object",self.json_to_player)
        return Player(player_data["discord_name"],player_data["osrs_name"],[self.__player_boss_json_to_object(boss_data) for boss_data in player_data["bosses"]])
    
    def combine_player_data(self,player:Player,player_data:WiseOldManPlayerData,update_baseline:bool) -> Player:
        """Combines the player data from the WiseOldMan API with the player data from the Player object."""
        if not player or not player_data:
            self.warn(self,"No player or player data to combine",self.combine_player_data)
            return None
        self.log(self,f"Combining player data for {player.osrs_name}",self.combine_player_data)
        for boss in player.boss_list:
            for wise_boss in player_data.boss_data:
                if boss.name == wise_boss.name:
                    boss.kills = wise_boss.kills
                    if update_baseline:
                        boss.kill_offset = wise_boss.kills
                    boss.tracked_kills = wise_boss.kills - boss.kill_offset
                    break
        return player
        
class LocalBossParser(Logger):
    def __init__(self):
        super().__init__()

    def local_boss_to_json(self,boss:LocalBoss) -> dict:
        """Internal function to convert LocalBoss object to a dictionary"""
        if not boss:
            self.warn(self,"No boss to convert to JSON",self.local_boss_to_json)
            return None
        #self.log(self,f"Converting boss {boss.name} to JSON",self.local_boss_to_json)
        return {
            "name":boss.name,
            "api_name":boss.api_name,
            "level":boss.level,
            "location":boss.location,
            "image":boss.image
        }
    
    def local_boss_json_to_object(self,boss_data:dict) -> LocalBoss:
        """Internal function to convert a dictionary to a LocalBoss object"""
        if not boss_data:
            self.warn(self,"No boss data to convert to object",self.local_boss_json_to_object)
            return None
        #self.log(self,f"Converting boss data to object",self.local_boss_json_to_object)
        return LocalBoss(boss_data["name"],boss_data["api_name"],boss_data["level"],boss_data["location"],boss_data["image"])
    
class SessionParser(Logger):
    def __init__(self):
        super().__init__()
        self.__boss_parser:LocalBossParser = LocalBossParser()
        self.__time_parser:TimeParser = TimeParser()

    def session_to_json(self,session:Session) -> dict:
        """Converts a session object to a dictionary for JSON serialization.  Returns a dict, or an empty dict if the session is None."""
        if not session:
            self.warn(self,"No session to convert to JSON",self.session_to_json)
            return {}
        self.log(self,f"Converting session {session.session_name} to JSON",self.session_to_json)
        return {
            "session_name":session.session_name,
            "tracking_active":session.tracking_active,
            "voting_active":session.voting_active,
            "last_boss":self.__boss_parser.local_boss_to_json(session.last_boss) if session.last_boss else None,
            "current_boss": self.__boss_parser.local_boss_to_json(session.current_boss) if session.current_boss else None,
            "boss_pool":[self.__boss_parser.local_boss_to_json(boss) for boss in session.boss_pool] if session.boss_pool else [],
            "start_time":self.__time_parser.datetime_to_str(session.start_time),
            "used_boss_list":[self.__boss_parser.local_boss_to_json(boss) for boss in session.used_boss_list] if session.used_boss_list else []
        }
    
    def json_to_session(self,session_data:dict) -> Session:
        """Converts a dictionary to a session object.  Returns a Session object, or None if the session_data is invalid."""
        if not session_data:
            self.warn(self,"No session data to convert to object",self.json_to_session)
            return None
        self.log(self,f"Converting session data to object",self.json_to_session)
        session:Session = Session()
        session.session_name = session_data["session_name"]
        session.tracking_active = session_data["tracking_active"]
        session.voting_active = session_data["voting_active"]
        session.last_boss = self.__boss_parser.local_boss_json_to_object(session_data["last_boss"])
        session.current_boss = self.__boss_parser.local_boss_json_to_object(session_data["current_boss"])
        session.boss_pool = [self.__boss_parser.local_boss_json_to_object(boss_data) for boss_data in session_data["boss_pool"]] if session_data["boss_pool"] else []
        session.start_time = self.__time_parser.str_to_datetime(session_data["start_time"])
        session.used_boss_list = [self.__boss_parser.local_boss_json_to_object(boss_data) for boss_data in session_data["used_boss_list"]] if session_data["used_boss_list"] else []
        return session
    
class DiscordParser(Logger):
    def __init__(self):
        super().__init__()

    def json_to_discord(self,config_json:dict) -> DiscordState:
        """Takes the config dictionary and returns a DiscordState object. Returns None if the config_json is invalid."""
        if not config_json:
            self.warn(self,"No config JSON to convert to DiscordState",self.__json_to_discord)
            return None
        discord_data:dict = config_json["discord"]
        discord_state:DiscordState = DiscordState()
        discord_state.bot_token = discord_data["bot token"]
        discord_state.voting_channel_id = discord_data["voting channel id"]
        discord_state.leaderboard_channel_id = discord_data["leaderboard channel id"]
        discord_state.set_name_channel_id = discord_data["set name channel id"]
        discord_state.console_channel_id = discord_data["console channel id"]
        discord_state.discord_admin_list = discord_data["admin list"]
        return discord_state
    
    def discord_to_json(self,discord_state:DiscordState) -> dict:
        """Takes the DiscordState object and returns a dictionary for JSON serialization. Returns an empty dictionary if the DiscordState is invalid."""
        if not discord_state:
            self.warn(self,"No DiscordState to convert to JSON",self.__discord_to_json)
            return {}
        discord_data:dict = {
            "bot token":discord_state.bot_token,
            "voting channel id":discord_state.voting_channel_id,
            "leaderboard channel id":discord_state.leaderboard_channel_id,
            "set name channel id":discord_state.set_name_channel_id,
            "console channel id":discord_state.console_channel_id,
            "admin list":discord_state.discord_admin_list
        }
        return discord_data
    
    def update_config(self,config_json:dict,discord_state:DiscordState) -> dict:
        """Combines the DiscordState object with the config dictionary. Returns the updated config file (dictionary), or an empty dictionary if the DiscordState is invalid."""
        if not config_json or not discord_state:
            self.warn(self,"No config JSON or DiscordState to combine",self.update_config)
            return {}
        config_json["discord"] = self.discord_to_json(discord_state)
        return config_json
    
class EventParser(Logger):
    def __init__(self):
        super().__init__()

    def datetime_generator(self,day:str, time:str) -> datetime.datetime:
        """Takes the day 'monday' 'tuesday' etc and time '00:00' '01:00' and generates the next occurance of this time. Returns None if the day or time is invalid."""
        days:list[str] = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        if day.lower() not in days:
            self.warn(self,"Invalid day for datetime generator",self.datetime_generator)
            return None
        numbers:list[int] = [0,1,2,3,4,5,6,7,8,9]
        if not len(time.split(":")) == 2:
            self.warn(self,"Invalid time for datetime generator",self.datetime_generator)
            return None
        hr:str = time.split(":")[0]
        minute:str = time.split(":")[1]
        invalid:bool = False
        for char in hr:
            if char not in [str(num) for num in numbers]:
                invalid = True
                break
        for char in minute:
            if char not in [str(num) for num in numbers]:
                invalid = True
                break
        if invalid:
            self.warn(self,"Invalid time for datetime generator",self.datetime_generator)
            return None
        today:datetime.date = datetime.date.today()
        target_day:str = days.index(day.lower())
        target_time:datetime.datetime = datetime.datetime.strptime(time, "%H:%M").time()
        days_ahead = (target_day - today.weekday() + 7) % 7
        next_date:datetime.datetime = today + datetime.timedelta(days_ahead)
        return datetime.datetime.combine(next_date,target_time)

    def json_to_event(self,config_json:dict) -> EventState:
        """Converts the config dictionary to an EventState object. Returns None if the config_json is invalid."""
        if not config_json:
            self.warn(self,"No config JSON to convert to EventState",self.__json_to_event)
            return None
        event_data:dict = config_json["event"]
        vote_open_day:dict = {"day":event_data["vote open day"],"time":event_data["vote open time"]}
        vote_close_day:dict = {"day":event_data["vote close day"],"time":event_data["vote close time"]}
        tracking_start_day:dict = {"day":event_data["tracking start day"],"time":event_data["tracking start time"]}
        tracking_stop_day:dict = {"day":event_data["tracking end day"],"time":event_data["tracking end time"]}
        return EventState(
            vote_open = self.datetime_generator(vote_open_day["day"],vote_open_day["time"]),
            vote_close = self.datetime_generator(vote_close_day["day"],vote_close_day["time"]),
            tracking_start = self.datetime_generator(tracking_start_day["day"],tracking_start_day["time"]),
            tracking_stop = self.datetime_generator(tracking_stop_day["day"],tracking_stop_day["time"])
        )
    
    def event_to_json(self,event_state:EventState) -> dict:
        """Convert the EventState object to a dictionary for JSON serialization. Returns an empty dictionary if the EventState is invalid."""
        if not event_state:
            self.warn(self,"No EventState to convert to JSON",self.event_to_json)
            return {}
        vote_open_day:dict = {"day":event_state.vote_open_day.strftime("%A").lower(),"time":event_state.vote_open_day.strftime("%H:%M")}
        vote_close_day:dict = {"day":event_state.vote_close_day.strftime("%A").lower(),"time":event_state.vote_close_day.strftime("%H:%M")}
        tracking_start_day:dict = {"day":event_state.tracking_start_day.strftime("%A").lower(),"time":event_state.tracking_start_day.strftime("%H:%M")}
        tracking_stop_day:dict = {"day":event_state.tracking_stop_day.strftime("%A").lower(),"time":event_state.tracking_stop_day.strftime("%H:%M")}
        event_data:dict = {
            "vote open day":vote_open_day["day"],
            "vote open time":vote_open_day["time"],
            "vote close day":vote_close_day["day"],
            "vote close time":vote_close_day["time"],
            "tracking start day":tracking_start_day["day"],
            "tracking start time":tracking_start_day["time"],
            "tracking stop day":tracking_stop_day["day"],
            "tracking stop time":tracking_stop_day["time"]
        }
        return event_data
    
    def update_config(self,config_json:dict,event_state:EventState) -> dict:
        """Combines the EventState object with the config dictionary. Returns the updated config file (dictionary), or an empty dictionary if the EventState is invalid."""
        if not config_json or not event_state:
            self.warn(self,"No config JSON or EventState to combine",self.update_config)
            return {}
        config_json["event"] = self.event_to_json(event_state)
        return config_json
    
class ApiParser(Logger):
    def __init__(self):
        super().__init__()

    def json_to_api(self,config_json:dict) -> ApiState:
        """Converts the config dictionary to an ApiState object. Returns None if the config_json is invalid."""
        if not config_json:
            self.warn(self,"No config JSON to convert to ApiState",self.json_to_api)
            return None
        api_data:dict = config_json["api"]
        return ApiState(
            url = api_data["url"],
            discord_contact_name = api_data["discord contact name"],
            bulk_update_frequency_minutes = api_data["bulk update frequency minutes"],
            update_ratelimit_seconds = api_data["update ratelimit seconds"]
        )
    
    def api_to_json(self,api_state:ApiState) -> dict:
        """Convert the ApiState object to a dictionary for JSON serialization. Returns an empty dictionary if the ApiState is invalid."""
        if not api_state:
            self.warn(self,"No ApiState to convert to JSON",self.api_to_json)
            return {}
        api_data:dict = {
            "url":api_state.url,
            "discord contact name":api_state.discord_contact_name,
            "bulk update frequency":api_state.update_frequency
        }
        return api_data
    
    def update_config(self,config_json:dict,api_state:ApiState) -> dict:
        """Combines the ApiState object with the config dictionary. Returns the updated config file (dictionary), or an empty dictionary if the ApiState is invalid."""
        if not config_json or not api_state:
            self.warn(self,"No config JSON or ApiState to combine",self.update_config)
            return {}
        config_json["api"] = self.api_to_json(api_state)
        return config_json