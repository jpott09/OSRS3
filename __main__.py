from services.config_handler import ConfigHandler
from services.discord_handler import DiscordHandler
from modules.objects.paths import Paths
from services.session_handler import StateHandler
import os
import asyncio

# get current working directory and assign folder paths
cwd:str = os.path.dirname(os.path.abspath(__file__))
folder_path_data:str = os.path.join(cwd,"data")
folder_path_assets:str = os.path.join(cwd,"assets")
# assign filepaths
filepath_config:str = os.path.join(cwd,"config.json")
paths:Paths = Paths(
    filepath_player_data = os.path.join(folder_path_data,"player_data.json"),
    filepath_boss_data = os.path.join(folder_path_data,"local_bosses.json"),
    filepath_session_data = os.path.join(folder_path_data,"session_data.json"),
    filepath_image_folder = os.path.join(folder_path_assets,"images"),
    folder_path_generated_image = folder_path_assets
)
# create config and pass to discord handler
config_handler:ConfigHandler = ConfigHandler(filepath_config,paths)
state_handler:StateHandler = StateHandler(paths.filepath_session_data)
dh:DiscordHandler = DiscordHandler(config_handler,state_handler)
asyncio.run(dh.run())
print("Bot has started.")