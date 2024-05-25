from modules.repositories.filesystem import ConfigRepository
from modules.logic.parser import ApiParser, EventParser, DiscordParser
from modules.state.api_state import ApiState
from modules.state.discord_state import DiscordState
from modules.state.event_state import EventState
from base.logging import Logger
from modules.objects.paths import Paths

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
        self.log(self,"Config loaded successfully",self.load)
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