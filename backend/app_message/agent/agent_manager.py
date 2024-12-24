import time
from openai import OpenAI
from swarm import Agent
from loguru import logger
from django.utils.translation import gettext as _

from app_message.agent.other_agent import (
    AudioAgent,
    HelpAgent,
    LLMAgent,
    DietAgent,
    TranslateAgent,
)
from app_message.agent.user_agent import UserAgent, SettingAgent
from app_message.agent.data_agent import DataAgent, WebAgent, FileAgent, RecordAgent
from app_message.session import Session
from app_message.exsmarm import ExSmarm
from backend.common.user.user import UserManager
from backend.common.llm import llm_tools
from backend.common.user.resource import *
from backend.common.utils.sys_tools import is_app_installed

DEFAULT_TEXT = _(
    "please_register_or_log_in_first_comma___enter_formatted_as_colon__register_username_xxx_comma__password_xxx__enter_or_log_in_username_xxx_comma__password_xxx"
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
        logger.info(f"is_logged_in: {is_logged_in}")

        return f"""You are to triage a users request, and call a tool to transfer to the right intent.
        User login status: {is_logged_in}. If not logged in, please transfer to User Agent to handle login,
        or prompt the user to login first, do not answer other questions.
        If logged in, please call the appropriate tool to transfer to the correct intent based on user's question.
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
            engine_type = user.get("llm_tool_model", {})
        llm_info = llm_tools.LLMInfo.get_info(engine_type, 'llm_tool_model')
        logger.info(f'llm_info {llm_info}')
        llm = OpenAI(base_url=llm_info.url, api_key=llm_info.api_key)
        client = ExSmarm(llm)
        transfer_functions = []
        for a in alist:
            agent = Agent(
                    name=a.agent_name,
                    model=llm_info.model_name,
                    instructions=a.get_instructions(),
                    functions=a.get_functions()
                )
            
            cls_name = a.__class__.__name__
            def make_transfer(target_agent):
                func_name = f"transfer_to_{cls_name.lower().replace(' ', '_')}"
                def transfer_func():
                    logger.info(f"transfer to {target_agent.name}")
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

        context_variables = {"sdata": sdata, "from": "agent_manager"}
        if not sdata.is_logged_in():
            sdata.set_cache('user_id', "")
            sdata.set_cache('password', "")

        messages = []
        messages.append({"role": "user", "content": content})

        try:
            response = client.run(
                agent=triage_agent,
                messages=messages,
                context_variables=context_variables,
                max_turns=10,
                debug=True
            )
        except Exception as e:
            logger.warning(f"Error: {e}")
            err_str = str(e)
            if len(err_str) > 100:
                err_str = err_str[:100] + "..."
            return False, _("agent_llm_error") + "\nError:\n" + err_str

        if 'total_count' in response.context_variables:
            total_count = response.context_variables['total_count']
            if total_count > 0:
                duration = round(time.time() - start_time, 3)    
                llm_tools.save_llm_usage(user, "agent", llm_info.get_desc(), duration, total_count)
        sdata.cache = response.context_variables['sdata'].cache
        logger.info(f'response {response.context_variables}')
        return self.post_process(response, sdata)
    
    def post_process(self, response, sdata):
        return True, response.messages[-1]["content"]
 
class AllAgentManager(BaseAgentManager):
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AllAgentManager()
        return cls._instance
    
    def __init__(self):
        super().__init__()

        if is_app_installed("app_record"):
            self.add_agent(RecordAgent())

        self.add_agent(DataAgent())  
        self.add_agent(FileAgent())
        self.add_agent(WebAgent())
        self.add_agent(AudioAgent())
        
        if is_app_installed("app_diet"):
            self.add_agent(DietAgent())
            
        if is_app_installed("app_translate"):
            self.add_agent(TranslateAgent())

        self.add_agent(SettingAgent())
        self.add_agent(UserAgent())
        self.add_agent(HelpAgent())
        #self.add_agent(LLMAgent()) # This agent is not used in the current version

    def post_process(self, response, sdata):
        call_tools = False
        for msg in response.messages:
            if 'tool_name' in msg and msg['tool_name'].startswith("_afunc_"):
                call_tools = True
                break
        if call_tools:
            return True, response.messages[-1]["content"]
        else:
            return True, _('system_tools') + "\n" + HelpAgent._afunc_help({"sdata": sdata})

class UserAgentManager(BaseAgentManager):
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = UserAgentManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.add_agent(UserAgent())

    def post_process(self, response, sdata):
        if not sdata.is_logged_in():
            if response.context_variables['sdata'].get_cache('user_id') != "" and response.context_variables['sdata'].get_cache('password') != "":
                logger.debug('Returning json, can login')
                ret = {"user_id": response.context_variables['sdata'].get_cache('user_id'), 
                    "password": response.context_variables['sdata'].get_cache('password')}
            else:
                logger.debug('Returning prompt')
                ret = response.messages[-1]["content"]
                ret = ret + "\n" + DEFAULT_TEXT
        else:
            ret = response.messages[-1]["content"]
        return True, ret