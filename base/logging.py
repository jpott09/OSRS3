import threading
import colorama

class Logger:
    def __init__(self,thread_lock:threading.Lock=None):
        self.log_color:str = colorama.Fore.WHITE
        self.warn_color:str = colorama.Fore.YELLOW
        self.error_color:str = colorama.Fore.RED
        self.lock = thread_lock or threading.Lock()
        self.__mute_logs:bool = False
        self.__mute_warns:bool = False
        self.__mute_errors:bool = False

    def __print(self, instance, msg, color, func=None):
        with self.lock:
            class_name = instance.__class__.__name__
            if func is not None:
                msg = f"[{class_name}.{func.__name__}] {msg}"
            else:
                msg = f"[{class_name}] {msg}"
            print(f"{color}{msg}{colorama.Style.RESET_ALL}")

    def mute(self) -> None:
        self.__mute_logs = True
        self.__mute_warns = True
        self.__mute_errors = True

    def unmute(self) -> None:
        self.__mute_logs = False
        self.__mute_warns = False
        self.__mute_errors = False

    def mute_logs(self) -> None:
        self.__mute_logs = True

    def unmute_logs(self) -> None:
        self.__mute_logs = False

    def mute_warns(self) -> None:
        self.__mute_warns = True

    def unmute_warns(self) -> None:
        self.__mute_warns = False

    def mute_errors(self) -> None:
        self.__mute_errors = True

    def unmute_errors(self) -> None:
        self.__mute_errors = False

    def log(self, instance, msg,func=None):
        if not self.__mute_logs: self.__print(instance, msg, self.log_color, func)

    def warn(self, instance, msg,func=None):
        if not self.__mute_warns: self.__print(instance, msg, self.warn_color, func)

    def error(self, instance, msg,func=None):
        if not self.__mute_errors: self.__print(instance, msg, self.error_color, func)