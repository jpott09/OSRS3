from base.logging import Logger
from modules.objects.player import Player
from modules.objects.boss import LocalBoss, Boss
from modules.dtos.wise_old_man_data import WiseOldManPlayerData
from modules.repositories.filesystem import PlayerRepository
from modules.logic.parser import PlayerParser
from services.wise_old_man_service import WiseOldManService
from modules.state.api_state import ApiState    

class PlayerHandler(Logger):
    def __init__(self,filepath_player_data:str,api_state:ApiState):
        """Filepath to the player data file, the WiseOldMan API URL (full url, should not end with a slash '/'), and the query interval in seconds."""
        super().__init__()
        self.__repository:PlayerRepository = PlayerRepository(filepath_player_data)
        self.__parser:PlayerParser = PlayerParser()
        self.__players:list[Player] = []
        self.__wise_old_man_service:WiseOldManService = WiseOldManService(api_state)
        #load the player data
        success:bool = self.__load()
        #log on init
        if not success: self.warn(self,"No player data found.",self.__init__)
        else: self.log(self,"Player data loaded successfully",self.__init__)

    def __save(self) -> bool:
        """Saves the player data to the file system.  Returns True if the save was successful."""
        self.log(self,"Saving player data")
        player_data:list[dict] = [self.__parser.player_to_json(player) for player in self.__players] or [{}]
        return self.__repository.write(player_data)
    
    def __load(self) -> bool:
        """Loads the player data from the file system.  Returns True if the load was successful."""
        self.log(self,"Loading player data")
        self.__players = [self.__parser.json_to_player(player) for player in self.__repository.load()]
        self.log(self,f"Loaded {len(self.__players)} players",self.__load)
        if not self.__players:
            self.warn(self,"No player data found.",self.__load)
            return False
        return True
    
    def __get_player_by_osrs_name(self,osrs_name:str) -> Player:
        """Returns the player object with the specified osrs name.  Returns None if the player does not exist."""
        osrs_name = osrs_name.lower().strip()
        for player in self.__players:
            if player.osrs_name == osrs_name:
                return player
        return None
    
    def osrs_name_exists(self,osrs_name:str) -> bool:
        """Returns True if the osrs name exists in the player list, False otherwise."""
        osrs_name = osrs_name.lower().strip()
        for player in self.__players:
            if player.osrs_name == osrs_name:
                return True
        return False
    
    def discord_name_exists(self,discord_name:str) -> bool:
        """Returns True if the discord name exists in the player list, False otherwise."""
        for player in self.__players:
            if player.discord_name == discord_name:
                return True
        return False
    
    def get_discord_name(self,osrs_name:str) -> str:
        """Returns the discord name linked to the osrs name.  Returns an empty string if the osrs name does not exist."""
        osrs_name = osrs_name.lower().strip()
        for player in self.__players:
            if player.osrs_name == osrs_name:
                return player.discord_name
        return ""
    
    def get_osrs_name(self,discord_name:str) -> str:
        """Returns the osrs name linked to the discord name.  Returns an empty string if the discord name does not exist."""
        for player in self.__players:
            if player.discord_name == discord_name:
                return player.osrs_name
        return ""
    
    async def force_update_bosses(self, osrs_name:str,update_baseline:bool=True) -> int:
        """Force update the bosses from the API for a specific player.  Returns -1 if the player does not exist, 0 if the player data could not be fetched, 1 if the player was updated successfully."""
        player:Player = self.__get_player_by_osrs_name(osrs_name)
        if not player:
            self.warn(self,f"Player {osrs_name} does not exist",self.force_update_bosses)
            return -1
        existing_player_bosses:list[Boss] = player.boss_list
        self.log(self,f"Forcing update of player {osrs_name}",self.force_update_bosses)
        wise_data:WiseOldManPlayerData = await self.__wise_old_man_service.update_player(osrs_name)
        if not wise_data:
            self.warn(self,f"Could not fetch player data for {osrs_name}",self.force_update_bosses)
            return 0
        for wise_boss in wise_data.boss_data:
            for player_boss in existing_player_bosses:
                if player_boss.name == wise_boss.name:
                    continue
            existing_player_bosses.append(Boss(wise_boss.name,wise_boss.kills))
        player = self.__parser.combine_player_data(player,wise_data,update_baseline)
        self.__save()
        self.log(self,f"Updated player {osrs_name}",self.force_update_bosses)
        return 1

    async def add(self,discord_name:str,osrs_name:str,local_boss_list:list[LocalBoss],update_baseline:bool=True) -> int:
        """Add a player to the player list.  Takes discord name, osrs name, and optionally a flag to update the baseline.
        if no baseline flag is set, it defaults to true, and the baseline offset will be set to current reported kills from api.
        -2: save error occurred. -1: no response from API check. 0: player already exists, 1: player added successfully."""
        if not discord_name or not osrs_name:
            self.warn(self,"Discord name or OSRS name is empty",self.add)
            return -1
        osrs_name = osrs_name.lower().strip()
        #check if the player exists
        if self.discord_name_exists(discord_name):
            self.warn(self,f"Discord name '{discord_name}' is linked to {self.get_osrs_name(discord_name)}",self.add)
            return 0
        if self.osrs_name_exists(osrs_name):
            self.warn(self,f"OSRS name '{osrs_name}' is linked to {self.get_discord_name(osrs_name)}",self.add)
            return 0
        # try and get api data for osrs name
        wise_data:WiseOldManPlayerData = await self.__wise_old_man_service.update_player(osrs_name)
        if not wise_data:
            self.warn(self,f"Could not fetch player data for {osrs_name}",self.add)
            return -1
        else:
            self.log(self,f"Fetched player data for {osrs_name}",self.add)
        # create and update a player object and add it to the player list
        # TODO NOTE! This logic was only adding bosses if they were in the local boss list.  This will be replaced, with the old code commented out.
        """
        player_boss_list:list[Boss] = []
        for local_boss in local_boss_list:
            for wise_boss in wise_data.boss_data:
                if local_boss.api_name == wise_boss.name:
                    player_boss_list.append(Boss(wise_boss.name, wise_boss.kills))
                    break
        """
        # TODO NOTE! END OF OLD CODE
        # TODO NOTE! This is the new code that will add all bosses from the API data, regardless of the local boss list.
        player_boss_list:list[Boss] = []
        for wise_boss in wise_data.boss_data:
            player_boss_list.append(Boss(wise_boss.name, wise_boss.kills))
        # TODO NOTE! END OF NEW CODE
        
        player:Player = Player(discord_name,osrs_name,player_boss_list)
        self.__players.append(self.__parser.combine_player_data(player,wise_data,update_baseline))
        saved:bool = self.__save()  # save player data
        # determine final return value
        if not saved:
            self.error(self,"Error saving player data",self.add)
            return -2
        self.log(self,f"Added player {discord_name} linked to {osrs_name}",self.add)
        return 1
    
    def remove(self,osrs_name:str) -> bool:
        """Remove an osrs player from the player list.  Returns True if the player was removed successfully.
        Returns false if the player does not exists, or an error ocurred while saving the player data."""
        osrs_name = osrs_name.lower().strip()
        player:Player = self.__get_player_by_osrs_name(osrs_name)
        if not player:
            self.warn(self,f"Player {osrs_name} does not exist",self.remove)
            return False
        self.__players.remove(player)
        saved:bool = self.__save()
        if not saved:
            self.error(self,"Error saving player data",self.remove)
            return False
        self.log(self,f"Removed player {osrs_name}",self.remove)
        return True
    
    async def update_all_players(self,update_baseline:bool) -> bool:
        """Update all players in the player list.  Returns True if all players were updated successfully."""
        wise_data:list[WiseOldManPlayerData] = await self.__wise_old_man_service.update_players([player.osrs_name for player in self.__players])
        if not wise_data:
            self.warn(self,"Could not fetch player data for all players",self.update_all_players)
            return False
        self.log(self,"Updating all players",self.update_all_players)
        for player in self.__players:
            for data in wise_data:
                if player.osrs_name == data.username:
                    player = self.__parser.combine_player_data(player,data,update_baseline)
                    break
        saved:bool = self.__save()
        if not saved:
            self.error(self,"Error saving player data",self.update_all_players)
            return False
        self.log(self,"Updated all players",self.update_all_players)
        return True
    
    async def update_player(self,osrs_name:str,update_baseline:bool) -> bool:
        """Update a player in the player list.  Returns True if the player was updated successfully."""
        player:Player = self.__get_player_by_osrs_name(osrs_name)
        if not player:
            self.warn(self,f"Player {osrs_name} does not exist",self.update_player)
            return False
        self.log(self,f"Updating player {osrs_name}",self.update_player)
        wise_data:WiseOldManPlayerData = await self.__wise_old_man_service.update_player(osrs_name)
        if not wise_data:
            self.warn(self,f"Could not fetch player data for {osrs_name}",self.update_player)
            return False
        player = self.__parser.combine_player_data(player,wise_data,update_baseline)
        saved:bool = self.__save()
        if not saved:
            self.error(self,"Error saving player data",self.update_player)
            return False
        self.log(self,f"Updated player {osrs_name}",self.update_player)
        return True
    
    def get_players(self) -> list[Player]:
        """Returns the list of players."""
        return self.__players
        
        








    