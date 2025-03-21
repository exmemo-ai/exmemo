from typing import List, Callable
from loguru import logger
from django.utils.translation import gettext as _

from app_message.command import CommandManager, Command, LEVEL_NORMAL, LEVEL_TOP, msg_common_select
from backend.common.user.resource import *
from backend.common.utils.text_tools import get_language_name
from backend.settings import LANGUAGE_CODE

DEFAULT_INSTRUCTIONS = f"Determine the single most suitable tool to call based on the user's input, and respond in {get_language_name(LANGUAGE_CODE.lower())}."

def agent_function(description, is_command=True):
    def decorator(func):
        static_func = staticmethod(func)
        static_func.__func__.description = description
        static_func.__func__.is_command = is_command
        return static_func
    return decorator

class BaseAgent:
    def __init__(self):
        self.agent_name = "BaseAgent"

    def get_instructions(self):
        funcs = self.get_functions()
        if len(funcs) > 0:
            func_list = []
            for func in funcs:
                desc = BaseAgent.get_func_desc(self, func)
                func_list.append(f"'{desc}'")
            return _("provides {func_str} functions_please_select").format(func_str=", ".join(func_list))    
        else:
            return DEFAULT_INSTRUCTIONS

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
            desc = BaseAgent.get_func_desc(self, func)
            real_func = func.__get__(None, type(self))
            if hasattr(real_func, 'is_command') and real_func.is_command:
                logger.debug(f'add_commands {desc}')
                CommandManager.get_instance().register(
                    Command(func, [desc], level=LEVEL_NORMAL)
                )
                cmd_list.append((desc, desc))
            else:
                logger.info(f'not a command {desc}')

        def msg_main(context_variables: dict):
            sdata = context_variables['sdata']
            return msg_common_select(sdata, cmd_list)

        if len(cmd_list) > 0:
            CommandManager.get_instance().register(
                Command(msg_main, [self.agent_name], level=LEVEL_TOP)
            )

    @staticmethod
    def get_func_desc(agent, func):
        real_func = func.__get__(None, type(agent))
        if hasattr(real_func, 'description'):
            desc = real_func.description
        else:
            desc = func.__doc__ or func.__name__
        return desc