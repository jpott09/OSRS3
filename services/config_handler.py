from modules.repositories.filesystem import ConfigRepository
from modules.logic.parser import ApiParser, EventParser, DiscordParser
from modules.state.api_state import ApiState
from modules.state.discord_state import DiscordState
from modules.state.event_state import EventState
from base.logging import Logger
from modules.objects.paths import Paths
from datetime import datetime

class ConfigHandler(Logger):
    def __init__(self,filepath_config:str,paths:Paths):
        super().__init__()
        self.paths:Paths = paths
        self.__repository:ConfigRepository = ConfigRepository(filepath_config)
        self.__parser_api:ApiParser = ApiParser()
        self.__parser_event:EventParser = EventParser()
        self.__parser_discord:DiscordParser = DiscordParser()
        self.config:dict = self.__repository.load()

        self.api_state:ApiState = None
        self.event_state:EventState = None
        self.discord_state:DiscordState = None

        self.load()

    def load(self) -> bool:
        """Loads the config from the file system.  Returns True if the load was successful."""
        self.api_state:ApiState = self.__parser_api.json_to_api(self.config)
        self.event_state:EventState = self.__parser_event.json_to_event(self.config)
        self.discord_state:DiscordState = self.__parser_discord.json_to_discord(self.config)
        if self.api_state is None or self.event_state is None or self.discord_state is None:
            self.error(self,"Error loading config.",self.load)
            return False
        self.log(self,"api_state, event_state, discord_state objects created successfully",self.load)
        api_valid:bool = self._check_api_state(self.api_state)
        discord_valid:bool = self._check_discord_state(self.discord_state)
        if not api_valid:
            self.error(self,"api_state object is invalid.",self.load)
            return False
        if not discord_valid:
            self.error(self,"discord_state object is invalid.",self.load)
            return False
        self.log(self,"api_state and discord_state objects are valid. Checking event state...",self.load)
        event_valid:bool = self._check_event_state(self.event_state)
        if not event_valid:
            self.error(self,"event_state object is invalid.",self.load)
            return False
        self.log(self,"event_state object is valid.",self.load)
        return True
    
    def save(self) -> bool:
        """Saves the config to the file system.  Returns True if the save was successful."""
        self.api_dict:dict = self.__parser_api.api_to_json(self.api_state)
        self.event_dict:dict = self.__parser_event.event_to_json(self.event_state)
        self.discord_dict:dict = self.__parser_discord.discord_to_json(self.discord_state)
        updated_config:dict = self.__parser_api.update_config(self.config,self.api_dict)
        if not updated_config:
            self.error(self,"Error updating config with API data.",self.save)
        else:
            self.config = updated_config
        updated_config = self.__parser_event.update_config(self.config,self.event_dict)
        if not updated_config:
            self.error(self,"Error updating config with Event data.",self.save)
        else:
            self.config = updated_config
        updated_config = self.__parser_discord.update_config(self.config,self.discord_dict)
        if not updated_config:
            self.error(self,"Error updating config with Discord data.",self.save)
        else:
            self.config = updated_config
        return self.__repository.write(self.config)
    
    def get_discord_state(self) -> DiscordState:
        """Returns the discord state object."""
        return self.discord_state
    
    def get_api_state(self) -> ApiState:
        """Returns the api state object."""
        return self.api_state
    
    def get_event_state(self) -> EventState:
        """Returns the event state object."""
        return self.event_state
    
    # Internal helper functions ----------------------------------------------
    def _check_event_state(self,event_state:EventState) -> bool:
        """Checks the times in the event state.  Adjusts times if not enough time between stages is provided.  Returns True if the event state object is valid."""
        if not event_state: return False
        # check 'days'
        days:list[str] = [event_state.vote_open_day,event_state.vote_close_day,event_state.tracking_start_day,event_state.tracking_stop_day]
        valid_days:list[str] = ["mon","tue","wed","thu","fri","sat","sun"]
        days_valid:bool = True
        for day in days:
            if not day in valid_days:
                days_valid = False
                break
        if not days_valid:
            self.error(self,"Invalid day provided in config file for event_state.",self._check_event_state)
            return False
        # check 'hours'
        hours:list[int] = [event_state.vote_open_hour,event_state.vote_close_hour,event_state.tracking_start_hour,event_state.tracking_stop_hour]
        valid_hours:list[int] = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
        hours_valid:bool = True
        for hour in hours:
            if not hour: 
                hours_valid = False
                break
            if not self._is_int(hour):
                hours_valid = False
                break
            if not hour in valid_hours:
                hours_valid = False
                break
        if not hours_valid:
            self.error(self,"Invalid hour provided in config file for event_state.",self._check_event_state)
            return False
        # check 'minutes'
        minutes:list[int] = [event_state.vote_open_minute,event_state.vote_close_minute,event_state.tracking_start_minute,event_state.tracking_stop_minute]
        minutes_valid:bool = True
        for minute in minutes:
            if not self._is_int(minute):
                minutes_valid = False
                break
            if minute < 0 or minute > 59:
                minutes_valid = False
                break
        if not minutes_valid:
            self.error(self,"Invalid minute provided in config file for event_state.",self._check_event_state)
            return False
        # check 'datetime' objects
        vote_open = event_state.vote_open
        vote_close = event_state.vote_close
        tracking_start = event_state.tracking_start
        tracking_stop = event_state.tracking_stop
        if not vote_open or not vote_close or not tracking_start or not tracking_stop:
            self.error(self,"Invalid datetime object provided in config file for event_state.",self._check_event_state)
            return False
        # TODO : check and adjust times if not enough time between stages
        return True
    
    def _check_api_state(self,api_state:ApiState) -> bool:
        """Returns True if the api state object is valid."""
        if not api_state: return False
        # check url
        url:str = api_state.url
        url_valid:bool = True
        if not url or url == "": url_valid = False
        if not self._is_str(url): url_valid = False
        if not url.__contains__("http"): url_valid = False
        if not url_valid:
            self.error(self,"Invalid provided in config file for api['url'].",self._check_api_state)
            return False
        # check discord_contact_name
        name:str = api_state.discord_contact_name
        name_valid:bool = True
        if not name or name == "": name_valid = False
        if not self._is_str(name): name_valid = False
        if not name_valid:
            self.error(self,"Invalid provided in config file for api['discord_contact_name'].",self._check_api_state)
            return False
        # check bulk update frequency
        bulk_update_frequency:int = api_state.bulk_update_frequency_minutes
        frequency_valid:bool = True
        if not bulk_update_frequency: frequency_valid = False
        if not self._is_int(bulk_update_frequency): frequency_valid = False
        if not frequency_valid:
            self.error(self,"Invalid provided in config file for api['update_frequency'].",self._check_api_state)
            return False
        # check update ratelimit
        update_ratelimit:int = api_state.update_ratelimit_seconds
        ratelimit_valid:bool = True
        if not update_ratelimit: ratelimit_valid = False
        if not self._is_int(update_ratelimit): ratelimit_valid = False
        if not ratelimit_valid:
            self.error(self,"Invalid provided in config file for api['update_ratelimit'].",self._check_api_state)
            return False
        self.log(self,"api_state object is valid.",self._check_api_state)
        return True
    
    def _check_discord_state(self,discord_state:DiscordState) -> bool:
        """Check the discord state object for validity."""
        if not discord_state: return False
        # check voting_channel_id
        voting_channel_id:int = discord_state.voting_channel_id
        voting_channel_id_valid:bool = True
        if not voting_channel_id: voting_channel_id_valid = False
        if not self._is_int(voting_channel_id): voting_channel_id_valid = False
        if not voting_channel_id_valid:
            self.error(self,"Invalid provided in config file for discord['voting_channel_id'].",self._check_discord_state)
            return False
        # check leaderboard_channel_id
        leaderboard_channel_id:int = discord_state.leaderboard_channel_id
        leaderboard_channel_id_valid:bool = True
        if not leaderboard_channel_id: leaderboard_channel_id_valid = False
        if not self._is_int(leaderboard_channel_id): leaderboard_channel_id_valid = False
        if not leaderboard_channel_id_valid:
            self.error(self,"Invalid provided in config file for discord['leaderboard_channel_id'].",self._check_discord_state)
            return False
        # check set_name_channel_id
        set_name_channel_id:int = discord_state.set_name_channel_id
        set_name_channel_id_valid:bool = True
        if not set_name_channel_id: set_name_channel_id_valid = False
        if not self._is_int(set_name_channel_id): set_name_channel_id_valid = False
        if not set_name_channel_id_valid:
            self.error(self,"Invalid provided in config file for discord['set_name_channel_id'].",self._check_discord_state)
            return False
        # check console_channel_id
        console_channel_id:int = discord_state.console_channel_id
        console_channel_id_valid:bool = True
        if not console_channel_id: console_channel_id_valid = False
        if not self._is_int(console_channel_id): console_channel_id_valid = False
        if not console_channel_id_valid:
            self.error(self,"Invalid provided in config file for discord['console_channel_id'].",self._check_discord_state)
            return False
        # check bot_token
        bot_token:str = discord_state.bot_token
        bot_token_valid:bool = True
        if not bot_token or bot_token == "": bot_token_valid = False
        if not self._is_str(bot_token): bot_token_valid = False
        if not bot_token_valid:
            self.error(self,"Invalid provided in config file for discord['bot_token'].",self._check_discord_state)
            return False
        # check discord_admin_list
        admin_list:list[str] = discord_state.discord_admin_list
        admin_list_valid:bool = True
        if not admin_list: admin_list_valid = False
        if not isinstance(admin_list,list): admin_list_valid = False
        for admin in admin_list:
            if not self._is_str(admin):
                admin_list_valid = False
                break
        if not admin_list_valid:
            self.error(self,"Invalid provided in config file for discord['discord_admin_list'].",self._check_discord_state)
            return False
        self.log(self,"discord_state object is valid.",self._check_discord_state)
        return True
    
    def _is_str(self,value:str) -> bool:
        """Returns True if the value is a string."""
        return isinstance(value,str)
    
    def _is_int(self,value:int) -> bool:
        """Returns True if the value is an int."""
        return isinstance(value,int)