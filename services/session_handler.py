from modules.state.session import Session
from base.logging import Logger
from modules.repositories.filesystem import SessionRepository
from modules.logic.parser import SessionParser
from modules.objects.boss import LocalBoss
from services.boss_handler import BossHandler
from modules.logic.session_changer import SessionChanger

class StateHandler(Logger):
    def __init__(self,session_filepath:str):
        super().__init__()
        self.__repository = SessionRepository(session_filepath)
        self.__parser:SessionParser = SessionParser()
        self.__session_changer:SessionChanger = SessionChanger()
        self.__current_session:Session = self.__parser.json_to_session(self.__repository.load()) or Session()

        
    def get_current_session(self) -> Session:
        """Returns the current session object."""
        return self.__current_session
    
    def __save_current_session(self) -> bool:
        """Saves the current session object to the file system.  Returns True if the save was successful."""
        self.log(self,"Saving current session")
        return self.__repository.write(self.__parser.session_to_json(self.__current_session))
    
    def open_voting(self,local_boss_list:list[LocalBoss]) -> bool:
        """Opens voting for the current session.  Returns True if successful, False otherwise."""
        if not self.__session_changer.open_voting(self.__current_session,local_boss_list):
            return False
        return self.__save_current_session()
    
    def close_voting(self,boss:LocalBoss) -> bool:
        """Closes voting for the current session.  A boss must be set.  Returns True if successful, False otherwise."""
        if not boss:
            self.error(self, "No boss set to close voting with", self.close_voting)
        if not self.__session_changer.close_voting(self.__current_session,boss):
            return False
        return self.__save_current_session()
    
    def open_tracking(self,boss:LocalBoss = None) -> bool:
        """Opens tracking for the current session.  A boss must be set if it was not set previous to tracking.
        (For example, coming from no stage, with no boss, straight to open_tracking() )
        this will only apply in manual session changes.  Returns True if successful, False otherwise."""
        if not self.__session_changer.open_tracking(self.__current_session,self.__current_session.current_boss if not boss else boss):
            return False
        return self.__save_current_session()
        
    def close_tracking(self) -> bool:
        """Closes tracking for the current session.  Returns True if successful, False otherwise."""
        if not self.__session_changer.close_tracking(self.__current_session):
            return False
        return self.__save_current_session()
    
    def reset_session(self) -> bool:
        """Resets the current session.  Returns True if successful, False otherwise."""
        if not self.__session_changer.reset_session(self.__current_session):
            return False
        return self.__save_current_session()
        
    def add_used_boss(self,boss:LocalBoss) -> bool:
        """Adds a boss to the used boss list.  Returns True if successful, False otherwise."""
        self.__current_session.used_boss_list.append(boss)
        return self.__save_current_session()
    
    def clear_used_bosses(self) -> bool:
        """Clears the used boss list.  Returns True if successful, False otherwise."""
        self.__current_session.used_boss_list.clear()
        return self.__save_current_session()


