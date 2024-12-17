import time
from openai import OpenAI
from typing import List, Callable
from swarm import Agent
from loguru import logger
from django.utils.translation import gettext as _

from app_message.session import Session
from app_message.exsmarm import ExSmarm
from app_message.command import CommandManager, Command, LEVEL_NORMAL, LEVEL_TOP, msg_common_select
from backend.common.user.user import UserManager
from backend.common.llm import llm_tools
from backend.common.user.resource import *

DEFAULT_TEXT = _(
    "please_register_or_log_in_first_comma___enter_formatted_as_colon__register_username_xxx_comma__password_xxx__enter_or_log_in_username_xxx_comma__password_xxx"
)

class BaseAgent:
    def __init__(self):
        self.agent_name = "BaseAgent"
        self.instructions = "Determine which function to call based on the user's input."

    def get_functions(self) -> List[Callable]:
        ret = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and attr_name.startswith('_afunc_'):
                ret.append(attr)
        return ret
    
    def add_commands(self): # later remove
        funcs = self.get_functions()
        cmd_list = []
        for func in funcs:
            logger.debug(f'add_commands {func.__doc__}')
            CommandManager.get_instance().register(
                Command(func, [func.__doc__], level=LEVEL_NORMAL)
            )
            cmd_list.append((func.__doc__, func.__doc__))

        def msg_main(context_variables: dict):
            sdata = context_variables['sdata']
            return msg_common_select(sdata, cmd_list)

        CommandManager.get_instance().register(
            Command(msg_main, [self.agent_name], level=LEVEL_TOP)
        )

class BaseAgentManager:    
    def __init__(self):
        self.agents = []
        self.agent_names = set()
        
    def add_agent(self, agent):
        if agent.agent_name not in self.agent_names:
            agent.add_commands()
            self.agents.append(agent)
            self.agent_names.add(agent.agent_name)

    def triage_instructions(self, context_variables):
        is_logged_in = context_variables['sdata'].is_logged_in()    
        logger.error(f"is_logged_in: {is_logged_in}")

        return f"""You are to triage a users request, and call a tool to transfer to the right intent.
        用户是否登录: {is_logged_in}，如果没有登录，请 transfer to User Agent 处理登录，或者提示用户登录，不回答其它问题。
        如果已经登录，请根据用户的问题，调用相应的工具转接到正确的意图。
        """

    def do_command(self, sdata: Session, engine_type: str = None, debug = False):
        start_time = time.time()
        content = sdata.current_content
        if content.startswith('/'):
            content = content[1:]
        alist = self.agents

        user = UserManager.get_instance().get_user(sdata.user_id)

        check_ret, desc = llm_tools.check_llm_limit(user, debug)
        if not check_ret:
            return check_ret, desc

        if engine_type is None:
            engine_type = user.get("llm_tool_model", llm_tools.DEFAULT_TOOL_LLM)
        llm_info = llm_tools.LLMInfo.get_info(engine_type)
        # later check api_method is openai/gemini
        logger.warning(f'llm_info {llm_info}')
        llm = OpenAI(base_url=llm_info.url, api_key=llm_info.api_key)
        client = ExSmarm(llm)
        transfer_functions = []
        for a in alist:
            agent = Agent(
                    name=a.agent_name,
                    model=llm_info.model_name,
                    instructions=a.instructions,
                    functions=a.get_functions()
                )
            
            cls_name = a.__class__.__name__
            def make_transfer(target_agent):
                func_name = f"transfer_to_{cls_name.lower().replace(' ', '_')}"
                def transfer_func():
                    from loguru import logger
                    logger.error(f"transfer to {target_agent.name}")
                    return target_agent
                
                transfer_func.__name__ = func_name
                transfer_func.__doc__ = target_agent.instructions
                return transfer_func
            
            transfer_functions.append(make_transfer(agent))

        triage_agent = Agent(
            name="Triage Agent", 
            model=llm_info.model_name,
            instructions=self.triage_instructions,
            functions=transfer_functions
        )

        context_variables = {"sdata": sdata}
        if not sdata.is_logged_in():
            sdata.set_cache('user_id', "")
            sdata.set_cache('password', "")

        messages = []
        messages.append({"role": "user", "content": content})

        response = client.run(
            agent=triage_agent,
            messages=messages,
            context_variables=context_variables,
            max_turns=10,
            debug=True
        )

        if not sdata.is_logged_in():
            if response.context_variables['sdata'].get_cache('user_id') != "" and response.context_variables['sdata'].get_cache('password') != "":
                logger.debug('返回 json，可以登录')
                ret = {"user_id": response.context_variables['sdata'].get_cache('user_id'), 
                    "password": response.context_variables['sdata'].get_cache('password')}
            else:
                logger.debug('返回提示')
                ret = response.messages[-1]["content"]
                ret = ret + "\n" + DEFAULT_TEXT
        else:
            ret = response.messages[-1]["content"]
        logger.error(f'response {response.context_variables}')

        if 'total_count' in response.context_variables:
            total_count = response.context_variables['total_count']
            if total_count > 0:
                duration = round(time.time() - start_time, 3)    
                llm_tools.save_llm_usage(user, "agent", engine_type, duration, total_count)
        sdata.cache = response.context_variables['sdata'].cache # tmp，由于 deep_copy，sdata未被修改，需要手动更新
        return True, ret
