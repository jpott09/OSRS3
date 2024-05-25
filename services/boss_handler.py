from modules.repositories.filesystem import LocalBossRepository
from modules.logic.parser import LocalBossParser
from base.logging import Logger
from modules.objects.boss import LocalBoss

class BossHandler(Logger):
    def __init__(self,filepath_boss_data:str):
        super().__init__()
        self.__repository:LocalBossRepository = LocalBossRepository(filepath_boss_data)
        self.__parser:LocalBossParser = LocalBossParser()
        self.__bosses:list[LocalBoss] = []
        #load the boss data
        success:bool = self.__load()
        #log on init
        if not success: self.warn(self,"No boss data found.",self.__init__)
        else: self.log(self,"Boss data loaded successfully",self.__init__)

    def __load(self) -> bool:
        """Loads the boss data from the file system.  Returns True if the load was successful."""
        self.log(self,"Loading boss data")
        self.__bosses = [self.__parser.local_boss_json_to_object(boss_data) for boss_data in self.__repository.load()]
        if not self.__bosses or len(self.__bosses) == 0:
            self.warn(self,"No boss data found",self.__load)
            return False
        self.log(self,f"Loaded {len(self.__bosses)} bosses",self.__load)
        return True
    
    def get_bosses(self) -> list[LocalBoss]:
        """Returns the list of bosses."""
        return self.__bosses