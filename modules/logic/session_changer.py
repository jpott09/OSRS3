from base.logging import Logger
from modules.state.session import Session
from modules.objects.boss import LocalBoss
from datetime import datetime
import random

class SessionChanger(Logger):
    def __init__(self):
        super().__init__()
        #session names
        self.__no_session:str = "No Session"
        self.__open_voting_session:str = "Open Voting"
        self.__close_voting_session:str = "Close Voting"
        self.__open_tracking_session:str = "Open Tracking"
        self.__close_tracking_session:str = "Close Tracking"

    def open_voting(self,session:Session,boss_list:list[LocalBoss]) -> bool:
        """Opens voting for the session.  Generates 4 random bosses for the boss pool. Returns True if successful, False otherwise"""
        if not session:
            self.warn(self,"No session to open voting",self.open_voting)
            return False
        session.session_name = self.__open_voting_session
        session.tracking_active = False
        session.voting_active = True
        session.last_boss = session.current_boss
        session.current_boss = None
        #generate 4 random bosses from the boss list
        if len(boss_list) - len(session.used_boss_list) < 4:
            session.used_boss_list.clear()
        valid_bosses:list[LocalBoss] = [boss for boss in boss_list if boss not in session.used_boss_list]
        if len(valid_bosses) < 4:
            self.error(self,"Not enough bosses to generate a pool",self.open_voting)
            return False
        session.boss_pool = random.sample(valid_bosses,4)
        session.start_time = datetime.now()
        return True
    
    def close_voting(self,session:Session,selected_boss:LocalBoss) -> bool:
        """Closes voting for the session.  Returns True if successful, False otherwise"""
        if not session:
            self.warn(self,"No session to close voting",self.close_voting)
            return False
        if session.session_name == self.__close_voting_session:
            self.error(self,"Session is already closed",self.close_voting)
            return False
        session.session_name = self.__close_voting_session
        session.tracking_active = False
        session.voting_active = False
        session.last_boss = session.current_boss or session.last_boss
        session.current_boss = selected_boss
        session.boss_pool.clear()
        session.start_time = datetime.now()
        return True
    
    def open_tracking(self,session:Session,selected_boss:LocalBoss = None) -> bool:
        """Opens tracking for the session.  If no selected_boss is passed, and no session.current_boss is set, will return false.
        Returns True if successful, False otherwise"""
        if not session:
            self.warn(self,"No session to open tracking",self.open_tracking)
            return False
        if not session.current_boss and not selected_boss:
            self.error(self,"No boss to open tracking",self.open_tracking)
            return False
        session.session_name = self.__open_tracking_session
        session.tracking_active = True
        session.voting_active = False
        if selected_boss:
            session.current_boss = selected_boss
        session.used_boss_list.append(session.current_boss)
        session.last_boss = session.current_boss
        session.boss_pool.clear()
        session.start_time = datetime.now()
        return True
    
    def close_tracking(self,session:Session) -> bool:
        """Closes tracking for the session.  Returns True if successful, False otherwise"""
        if not session:
            self.warn(self,"No session to close tracking",self.close_tracking)
            return False
        if not session.tracking_active:
            self.error(self,"Session tracking is not active",self.close_tracking)
            return False
        session.session_name = self.__close_tracking_session
        session.tracking_active = False
        session.voting_active = False
        session.last_boss = session.current_boss
        session.current_boss = None
        session.boss_pool.clear()
        session.start_time = datetime.now()
        return True
    
    def reset_session(self,session:Session) -> bool:
        """Closes the session.  Returns True if successful, False otherwise"""
        if not session:
            self.warn(self,"No session to close",self.no_session)
            return False
        session.session_name = self.__no_session
        session.tracking_active = False
        session.voting_active = False
        session.boss_pool.clear()
        session.start_time = datetime.now()
        return True

