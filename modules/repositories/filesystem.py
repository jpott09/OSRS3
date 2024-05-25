from base.logging import Logger
import json

class Filesystem(Logger):
    def __init__(self):
        super().__init__()
    
    def _load_json_dict(self,filepath:str) -> dict:
        """Loads a JSON file from the specified filepath and returns it as a dictionary.  Returns an empty dictionary if an error occurs."""
        try:
            with open(filepath,"r") as file:
                self.log(self,f"Loaded JSON file: {filepath}",self._load_json_dict)
                return json.load(file)
        except Exception as e:
            self.error(self,f"Error loading JSON file: {e}",self._load_json_dict)
            return {}
        
    def _load_json_list(self,filepath:str) -> list[dict]:
        """Loads a JSON file from the specified filepath and returns it as a list.  Returns an empty list if an error occurs."""
        try:
            with open(filepath,"r") as file:
                self.log(self,f"Loaded JSON file: {filepath}",self._load_json_list)
                return json.load(file)
        except Exception as e:
            self.error(self,f"Error loading JSON file: {e}",self._load_json_list)
            return []

    def _write_json_dict(self,filepath:str,data:dict) -> bool:
        """Writes a dictionary to a JSON file at the specified filepath.  Returns True if the write was successful, False otherwise."""
        try:
            with open(filepath,"w") as file:
                json.dump(data,file,indent=4)
                self.log(self,f"Wrote JSON file: {filepath}",self._write_json_dict)
                return True
        except Exception as e:
            self.error(self,f"Error writing JSON file: {e}",self._write_json_dict)
            return False
        
    def _write_json_list(self,filepath:str,data:list) -> bool:
        """Writes a list to a JSON file at the specified filepath.  Returns True if the write was successful, False otherwise."""
        try:
            with open(filepath,"w") as file:
                json.dump(data,file,indent=4)
                self.log(self,f"Wrote JSON file: {filepath}",self._write_json_list)
                return True
        except Exception as e:
            self.error(self,f"Error writing JSON file: {e}",self._write_json_list)
            return False

class PlayerRepository(Filesystem):
    def __init__(self,filepath_player_data:str):
        super().__init__()
        self.__filepath:str = filepath_player_data

    def write(self,player_data:list[dict]) -> bool:
        """Writes the player data list to the player data file.  Returns True if the write was successful, False otherwise."""
        return self._write_json_list(self.__filepath,player_data)
    
    def load(self) -> list[dict]:
        """Loads the player data from the player data file.  Returns an empty list if an error occurs."""
        return self._load_json_list(self.__filepath)
    
class LocalBossRepository(Filesystem):
    def __init__(self,filepath_boss_data:str):
        super().__init__()
        self.__filepath:str = filepath_boss_data

    def write(self,boss_data:list[dict]) -> bool:
        """Writes the boss data dict to the boss data file.  Returns True if the write was successful, False otherwise."""
        return self._write_json_list(self.__filepath,boss_data)
    
    def load(self) -> list[dict]:
        """Loads the boss data from the boss data file.  Returns an empty dictionary if an error occurs."""
        return self._load_json_list(self.__filepath)
    
class ConfigRepository(Filesystem):
    def __init__(self,filepath_config:str):
        super().__init__()
        self.__filepath:str = filepath_config

    def write(self,config:dict) -> bool:
        """Writes the config dict to the config file.  Returns True if the write was successful, False otherwise."""
        return self._write_json_dict(self.__filepath,config)
    
    def load(self) -> dict:
        """Loads the config from the config file.  Returns an empty dictionary if an error occurs."""
        return self._load_json_dict(self.__filepath)
    
class SessionRepository(Filesystem):
    def __init__(self,filepath_session:str):
        super().__init__()
        self.__filepath:str = filepath_session

    def write(self,session:dict) -> bool:
        """Writes the session dict to the session file.  Returns True if the write was successful, False otherwise."""
        return self._write_json_dict(self.__filepath,session)
    
    def load(self) -> dict:
        """Loads the session from the session file.  Returns an empty dictionary if an error occurs."""
        return self._load_json_dict(self.__filepath)


    