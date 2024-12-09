import json
import traceback
from loguru import logger

from django.http import HttpResponse
from rest_framework.views import APIView
from knox.auth import TokenAuthentication
from django.utils.translation import gettext as _

import backend.common.files.filecache as filecache
from backend.common.utils.net_tools import do_result
from backend.common.user.views import LoginView
from backend.common.user.user import DEFAULT_USER
from backend.common.utils.file_tools import get_ext
import app_message.user_manager as user_manager
from .message import *
from .session import SessionManager, get_session_by_req
from rest_framework.permissions import IsAuthenticated

class SessionAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sdata = get_session_by_req(request)
        logger.info(
            f'request.data {request.data}, is_group {sdata.is_group}'
        )

        logger.info(f"message recv: args {sdata.args}")        
        rtype = request.POST.get("rtype", "text")
        try:
            if rtype == "get_messages":
                return sdata.get_messages()
            elif rtype == "clear_session":
                return SessionManager.get_instance().clear_session(sdata)
            elif rtype == "get_sessions":
                return SessionManager.get_instance().get_sessions(sdata.user_id)
            elif rtype == "save_session":
                sdata.save_to_db()
                return do_result(True, {"type": "text", "content": "session saved"})
            elif rtype == "get_current_session":
                detail = {"type": "text", "content": sdata.sid}
                return do_result(True, detail)
        except Exception as e:
            logger.warning(f"message failed {e}")
            traceback.print_exc()
        return HttpResponse(
            json.dumps(
                {"status": "failed", "info": _("backend_processing_failed")}
            )
        )


class MessageAPIView(APIView):
    def post(self, request):
        """
        Accept and process text messages, including URLs
        """
        auth = TokenAuthentication()
        user_auth_tuple = auth.authenticate(request)
        has_token = False
        logger.info(f"user_auth_tuple {user_auth_tuple}")
        if user_auth_tuple is not None:
            request.user, request.auth = user_auth_tuple
            has_token = True

        sdata = get_session_by_req(request)
        logger.info(
            f'request.data {request.data}, has_token {has_token}, is_group {sdata.is_group}'
        )

        if has_token or sdata.is_group:
        #if False:
            logger.info(f"message recv: args {sdata.args}")
            if "user_id" not in sdata.args or sdata.args["user_id"] is None:
                sdata.args["user_id"] = DEFAULT_USER
            if sdata.args["user_id"] == DEFAULT_USER:
                LoginView.create_user_default()
            
            rtype = request.POST.get("rtype", "text")
            try:
                if rtype == "text":
                    ret, detail = do_message(sdata)
                    logger.debug(f"{ret}, {detail}")
                    return do_result(ret, detail)
                elif rtype == "file":
                    return self.upload_file(sdata, request)
            except Exception as e:
                logger.warning(f"message failed {e}")
                traceback.print_exc()
            return HttpResponse(
                json.dumps(
                    {"status": "failed", "info": _("backend_processing_failed")}
                )
            )
        else:
            content = request.POST.get("content", None)
            user_name = request.POST.get("user_name", DEFAULT_USER)
            if content is None:
                return HttpResponse(
                    json.dumps(
                        {
                            "status": "failed",
                            "info": _("please_sign_up_or_log_in_first"),
                        }
                    )
                )
            #ret = user_manager.UserTools.get_instance().chat(user_name, content)
            #return HttpResponse(json.dumps({"status": "success", "info": ret}))
            ret = test_chat(sdata, content)
            return HttpResponse(json.dumps({"status": "success", "type":"json", "content":{"info": ret, "sid": sdata.sid}}))

    def upload_file(self, sdata, request):
        ret, path, filename = real_upload_file(request)
        if ret:
            ret, detail = msg_recv_file(
                path, filename, sdata
            )  # May return files or text
            return do_result(True, detail)  # return True to show info
        return HttpResponse(
            json.dumps({"status": "failed", "info": _("backend_processing_failed")})
        )


def real_upload_file(request):
    logger.debug(f"real_upload_file {request.FILES}")
    files = request.FILES
    for file in files.values():  # only one file
        filename = file.name
        tmp_path = filecache.get_tmpfile(get_ext(filename))
        logger.debug(f"file save to {tmp_path}")
        with open(tmp_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
        return True, tmp_path, filename
    return False, None, None

# 241206 test

from swarm import Swarm, Agent
import app_message.my_agent as my_agent

client = Swarm()

def test_chat(sdata, content):
    agent_user = my_agent.UserAgent()
    user_agent = Agent(
        name=agent_user.agent_name,
        instructions=agent_user.instructions,
        functions=agent_user.get_functions()
    )

    agent_others = my_agent.OthersAgent()
    others_agent = Agent(
        name=agent_others.agent_name,
        instructions=agent_others.instructions,
        functions=agent_others.get_functions()
    )

    def transfer_to_user():
        """如果是针对用户登录注册修改的操作，就交给这个agent处理"""
        print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaa1')
        return user_agent

    def transfer_to_others():
        """如果其它agent都不适合，就交给这个agent处理"""
        print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaa2')
        return others_agent

    triage_agent = Agent(
        name="Triage Agent",
        instructions="Determine which agent is best suited to handle the user's request, and transfer the conversation to that agent.",
    )
    triage_agent.functions = [transfer_to_user, transfer_to_others]
    context_variables = {"isLoggedIn": False, "user_id": "", "password": "", "status": "init"}

    messages = []
    for msg in sdata.messages:
        messages.append({"role": msg.sender, "content": msg.content})
    messages.append({"role": "user", "content": content})
    print("@@@@@@@@@@", messages)
    response = client.run(
        agent=triage_agent,
        messages=messages,
        context_variables=context_variables,
        debug=True
    )
    print(response.messages[-1]["content"])
    print(response.context_variables)
    if response.context_variables['status'] == 'wait_login':
        print('返回 json，可以登录')
        ret = {"user_id": response.context_variables['user_id'], "password": response.context_variables['password']}
    elif response.context_variables['status'] == 'need_login':
        print('需要登录，继续沟通')
        ret = user_manager.DEFAULT_TEXT
    else:
        ret = response.messages[-1]["content"]
    sdata.send_message(content, ret)
    return ret
    

