from openai import OpenAI
from typing import List, Callable
from swarm import Agent
from loguru import logger

from app_message.session import Session
from app_message.exsmarm import ExSmarm
from app_message.command import CommandManager, Command, LEVEL_NORMAL, LEVEL_TOP, msg_common_select
import app_message.user_manager as user_manager
from backend.common.user.user import UserManager
from backend.common.llm import llm_tools

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

        def msg_main(sdata):
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

    def do_command(self, sdata: Session, engine_type: str = None):
        content = sdata.current_content
        if content.startswith('/'):
            content = content[1:]
        alist = self.agents

        user = UserManager.get_instance().get_user(sdata.user_id)
        if engine_type is None:
            engine_type = user.get("llm_chat_model", llm_tools.DEFAULT_CHAT_LLM)
        api_method, api_key, url, model_name = llm_tools.select_llm_model(engine_type)
        # later check api_method is openai/gemini
        logger.warning(f'api_method {api_method} {url}, {model_name}')
        llm = OpenAI(base_url=url, api_key=api_key)
        client = ExSmarm(llm)
        transfer_functions = []
        for a in alist:
            agent = Agent(
                    name=a.agent_name,
                    model=model_name,
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
            model=model_name,
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
                ret = ret + "\n" + user_manager.DEFAULT_TEXT
        else:
            ret = response.messages[-1]["content"]
        sdata.cache = response.context_variables['sdata'].cache # tmp，由于 deep_copy，sdata未被修改，需要手动更新
        return True, ret
