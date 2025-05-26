from loguru import logger
import pytz
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from knox.auth import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
import json
import os

from django.utils.translation import gettext as _
from .models import StorePrompt
from .serializer import StorePromptSerializer
from backend.common.user.utils import get_user_id
from backend.common.utils.net_tools import do_result
from backend.common.user.user import UserManager
from backend.settings import BASE_DATA_DIR
from backend.settings import LANGUAGE_CODE
from backend.common.user.utils import parse_common_args
from backend.common.llm.llm_hub import llm_query

AI_ROLE="You are an AI assistant."

class StorePromptViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = StorePromptSerializer
    queryset = StorePrompt.objects.all()

    def list(self, request, *args, **kwargs):
        user_id = get_user_id(request)
        user = UserManager.get_instance().get_user(user_id)
        first_use_prompt = user.get("first_use_prompt")
        if first_use_prompt:
            self._reset_prompt(user_id)
            user.set("first_use_prompt", False)

        qs = StorePrompt.objects.filter(user_id=user_id).order_by("-updated_time")
        logger.info(f"Found {qs.count()} prompts for user {user_id}")        
        serializer = self.get_serializer(qs, many=True)
        return do_result(True, {"results": serializer.data})
    
    def create(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            if not data.get('created_time'):
                data['created_time'] = timezone.now().astimezone(pytz.UTC)
            if not data.get('user_id'):
                data['user_id'] = get_user_id(request)
                
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            logger.warning(f"Validation error: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.warning(f"Error creating prompt: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="get_etype_list")
    def get_etype_list(self, request):
        etype_list = [
            "translate",
            "view", 
            "editor"
        ]
        return do_result(True, {"list": etype_list})

    @action(detail=False, methods=["get"], url_path="reset_prompt")
    def reset_prompt(self, request):
        user_id = get_user_id(request)
        self._reset_prompt(user_id)
        return do_result(True, "Prompt reset successfully.")

    def _reset_prompt(self, user_id):
        StorePrompt.objects.filter(user_id=user_id).delete()
        created_time = timezone.now().astimezone(pytz.UTC)

        if LANGUAGE_CODE.lower().find("zh") >= 0:
            json_path = os.path.join(BASE_DATA_DIR, "default_prompts_zh.json")
        else:
            json_path = os.path.join(BASE_DATA_DIR, "default_prompts.json")
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                default_prompts_data = json.load(f)
        except Exception as e:
            logger.warning(f"Error reading default prompts file: {str(e)}")
            default_prompts_data = []

        default_prompts = []
        for prompt in default_prompts_data:
            default_prompts.append({
                "user_id": user_id,
                "title": prompt["title"],
                "prompt": prompt["prompt"],
                "etype": prompt["etype"],
                "created_time": created_time,
            })

        for prompt in default_prompts:
            try:
                StorePrompt.objects.create(**prompt)
            except Exception as e:
                logger.warning(f"Error creating prompt {prompt['title']}: {str(e)}")


class QAAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Provide interfaces to support the paper analysis page
        """
        args = parse_common_args(request)
        rtype = request.GET.get("rtype", request.POST.get("rtype", None))
        content = request.GET.get("content", request.POST.get("content", None))
        logger.debug(f"rtype *{rtype}*")

        if rtype == "gpt":
            return self.handle_gpt_request(content, request, args)
        return do_result(False, _("method_not_supported_colon_") + rtype)


    def handle_gpt_request(self, content, reqeust, args):
        if content is not None:
            logger.debug(f"content {content[:20]}")
        debug = True
        if content is None or len(content.strip()) == 0:
            return False, _("empty_contents")
        try:
            if debug:
                print("req", content)
            llm_type = reqeust.GET.get("llm_type", reqeust.POST.get("llm_type", "llm_chat_model")) 
            ret, answer, detail = llm_query(
                args["user_id"], AI_ROLE, content[:4096], "ai", llm_type=llm_type, debug=debug
            )
            return do_result(True, answer)
        except Exception as e:
            logger.warning(e)
            return do_result(False, str(e))
        