from modules.repositories.wise_old_man_fetcher import WiseOldManFetcher
from modules.logic.parser import WiseOldManParser
from base.logging import Logger
from modules.dtos.wise_old_man_data import WiseOldManPlayerData
from datetime import datetime
from modules.state.api_state import ApiState
import asyncio

class WiseOldManService(Logger):
    def __init__(self,api_state:ApiState) -> None:
        """Initializes the WiseOldManService with the URL to fetch player data from.  Url should be the full base URL of the WiseOldMan API and should not end with a slash."""
        super().__init__()
        self.api_state:ApiState = api_state
        self.repository = WiseOldManFetcher(api_state.url,api_state.discord_contact_name)
        #parsing
        self.parser = WiseOldManParser()
        #rate limiting
        self.last_query:datetime = None
        #asyncio lock
        self.query_lock = asyncio.Lock()

    def __can_query(self) -> bool:
        """Checks if the service can query the WiseOldMan API.  The API has a rate limit of 1 query per 5 seconds. Returns True or False"""
        if self.last_query is None: return True
        return (datetime.now() - self.last_query).seconds >= self.api_state.update_frequency
    
    async def update_player(self,username:str) -> WiseOldManPlayerData:
        """This method is used to update the player data for the specified username.  This function is rate limited. Returns None if the player data could not be fetched."""
        #add the player to the update queue
        async with self.query_lock:
            while not self.__can_query():
                await asyncio.sleep(.5)
            self.last_query = datetime.now()
            player_data:WiseOldManPlayerData = self.parser.json_to_object(self.repository.fetch_player(username))
            if player_data is None:
                self.warn(self,f"Could not fetch player data for {username}",self.update_player)
                return None
            return player_data
        
    async def update_players(self,usernames:list[str]) -> list[WiseOldManPlayerData]:
        """This method is used to update the player data for the specified usernames.  This function is rate limited. Returns an empty list if an error or no data occurs"""
        tasks:list[asyncio.Task] = [self.update_player(username) for username in usernames]
        try:
            player_data:list[WiseOldManPlayerData] = await asyncio.gather(*tasks)
            for data in player_data:
                if data is None:
                    self.warn(self,"Could not fetch all player data",self.update_players)
                    player_data.remove(data)
            if not player_data:
                self.warn(self,"No player data fetched",self.update_players)
                return []
            return player_data
        except Exception as e:
            self.error(self,f"Error updating players: {e}",self.update_players)
            return []