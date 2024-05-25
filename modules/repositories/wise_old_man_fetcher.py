import requests
from base.logging import Logger

class WiseOldManFetcher(Logger):
    def __init__(self,fetch_player_url:str,api_discord_username:str = "") -> None:
        """Initializes the WiseOldManFetcher with the URL to fetch player data from.  Url should be the full base URL of the WiseOldMan API and should not end with a slash."""
        super().__init__()
        self.fetch_player_url:str = fetch_player_url
        #if last character of url is a slash, remove it
        if self.fetch_player_url[-1] == "/":
            self.fetch_player_url = self.fetch_player_url[:-1]

    def fetch_player(self,username:str) -> dict:
        """Attempt to fetch player data from the WiseOldMan API. Returns an empty dictionary if an error occurs."""
        url:str = f"{self.fetch_player_url}/players/{username}"
        self.log(self,f"Fetching player {username} from {url}",self.fetch_player)
        try:
            response = requests.get(f"{url}")
            if not response:
                self.warn(self,f"No response from {url}",self.fetch_player)
                return {}
            json_data:dict = response.json()
            if not json_data or json_data == {}:
                self.warn(self,f"No data returned from {url}",self.fetch_player)
                return {}
            api_username:str = json_data.get("username","")
            if username.lower() != api_username.lower():
                self.warn(self,f"API returned data for {api_username} instead of {username}",self.fetch_player)
                return {}
            self.log(self,f"Successfully fetched player {username} from {url}",self.fetch_player)
            return response.json()
        except requests.RequestException as e:
            self.error(self,f"Error fetching player {username} from {url}: {e}",self.fetch_player)
            return {}