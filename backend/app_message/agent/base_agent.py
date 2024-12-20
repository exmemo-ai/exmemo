from typing import List, Callable
from loguru import logger
from django.utils.translation import gettext as _

from app_message.command import CommandManager, Command, LEVEL_NORMAL, LEVEL_TOP, msg_common_select
from backend.common.user.resource import *
from backend.common.utils.text_tools import get_language_name
from backend.settings import LANGUAGE_CODE

DEFAULT_INSTRUCTIONS = f"Determine the single most suitable tool to call based on the user's input, and respond in {get_language_name(LANGUAGE_CODE.lower())}."

def agent_function(description):
    def decorator(func):
        static_func = staticmethod(func)
        static_func.__func__.description = description
        return static_func
    return decorator

class BaseAgent:
    def __init__(self):
        self.agent_name = "BaseAgent"
        self.instructions = DEFAULT_INSTRUCTIONS

    def get_functions(self) -> List[Callable]:
        ret = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and attr_name.startswith('_afunc_'):
                ret.append(attr)
        return ret
    
    def add_commands(self):
        funcs = self.get_functions()
        cmd_list = []
        for func in funcs:
            real_func = func.__get__(None, type(self))
            if hasattr(real_func, 'description'):
                desc = real_func.description
            else:
                desc = func.__doc__ or func.__name__
            logger.debug(f'add_commands {desc}')
            CommandManager.get_instance().register(
                Command(func, [desc], level=LEVEL_NORMAL)
            )
            cmd_list.append((desc, desc))

        def msg_main(context_variables: dict):
            sdata = context_variables['sdata']
            return msg_common_select(sdata, cmd_list)

        CommandManager.get_instance().register(
            Command(msg_main, [self.agent_name], level=LEVEL_TOP)
        )

