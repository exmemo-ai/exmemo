from loguru import logger

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from knox.auth import TokenAuthentication
from django.db.models import Q

from backend.common.user.utils import parse_common_args, get_user_id
from backend.common.utils.net_tools import do_result
from django.utils.translation import gettext as _
from . import translate
from .models import StoreEnglishArticle, StoreTranslate
from .serializer import StoreEnglishArticleSerializer, StoreTranslateSerializer


class StoreWordViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = StoreTranslate.objects.filter().all().order_by("-times", "freq")
    serializer_class = StoreTranslateSerializer

    def list(self, request, *args, **kwargs):
        user_id = get_user_id(request)
        query_args = {}
        if user_id == None:
            return Response([])
        else:
            query_args["user_id"] = user_id
        keywords = request.GET.get("keyword", None)
        q_obj = Q()
        keyword_arr = keywords.split(" ")
        for keyword in keyword_arr:
            q_obj &= Q(word__icontains=keyword)
        queryset = StoreTranslate.objects.filter(q_obj, **query_args)
        serializer = StoreTranslateSerializer(queryset, many=True)
        data = sorted(serializer.data, key=lambda x: x["freq"])
        paginator = PageNumberPagination()
        if queryset.count() > 0:
            paginator.page_size = queryset.count()
        else:
            paginator.page_size = 10
        page = paginator.paginate_queryset(queryset, self.request)
        return paginator.get_paginated_response(data)


class StoreArticleViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = StoreEnglishArticle.objects.filter().all()
    serializer_class = StoreEnglishArticleSerializer


class TranslateAssistantView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self.do_chat(request)

    def get(self, request):
        return self.do_chat(request)

    def do_chat(self, request):
        args = parse_common_args(request)
        logger.info(f"translate chat {args}")
        prompt = request.GET.get("prompt", request.POST.get("prompt", None))
        content = request.GET.get("content", request.POST.get("content", None))
        if prompt is None and content is None:
            info = _("please_enter_questions_or_content_to_be_translated")
            return do_result(False, info)
        ret = False
        answer = _("internal_processing_error")
        try:
            if prompt is not None and content is not None:
                string = "The original text is: {content}\n\nPlease answer the question based on the original text: {prompt}".format(
                    content=content, prompt=prompt
                )
                ret, answer = translate.translate_common(args["user_id"], string)
            elif prompt is not None:
                ret, answer = translate.translate_common(args["user_id"], prompt)
            elif content is not None:
                ret, answer = translate.translate_sentence(args["user_id"], content)
        except Exception as e:
            logger.error(f"translate_sentence {e}")
            ret = False
            answer = str(e)
        return do_result(ret, answer)


class TranslateAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self.do_translate(request)

    def get(self, request):
        return self.do_translate(request)

    def do_translate(self, request):
        args = parse_common_args(request)
        logger.info(f"translate {args}")
        rtype = request.GET.get("rtype", request.POST.get("rtype", "word"))
        word = request.GET.get("word", request.POST.get("word", None))
        sentence = request.GET.get("sentence", request.POST.get("sentence", None))
        logger.debug(f"translate rtype:{rtype} wprd:{word} sentence:{sentence}")
        if rtype == "word":
            return self.translate_word(args, word, sentence)
        elif rtype == "sentence":
            return self.translate_sentence(args, sentence)
        elif rtype == "word_role":
            return self.translate_word_role(args, word, sentence)
        info = "not support"
        return do_result(False, info)

    def translate_word(self, args, word, sentence):
        ret, regular_word, detail = translate.translate_word(
            word, args["user_id"], with_gpt=True, sentence=sentence
        )
        return do_result(True, detail)

    def translate_sentence(self, args, sentence):
        try:
            ret, answer = translate.translate_sentence(args["user_id"], sentence)
        except Exception as e:
            logger.error(f"translate_sentence {e}")
            ret = False
            answer = str(e)
        return do_result(ret, answer)

    def translate_word_role(self, args, word, sentence):
        try:
            ret, answer = translate.translate_word_role(args["user_id"], word, sentence)
        except Exception as e:
            logger.error(f"translate_sentence {e}")
            ret = False
            answer = str(e)
        return do_result(ret, answer)
