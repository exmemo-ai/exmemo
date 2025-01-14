from loguru import logger
import json
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
from django.utils import timezone
from . import translate
from .models import StoreEnglishArticle, StoreTranslate
from .serializer import StoreEnglishArticleSerializer, StoreTranslateSerializer
from backend.common.llm.llm_hub import llm_query_json

MSG_ROLE = _("you_are_a_middle_school_english_teacher")


class StoreWordViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = StoreTranslate.objects.filter().all().order_by("-times", "freq")
    serializer_class = StoreTranslateSerializer
    pagination_class = PageNumberPagination


    def list(self, request, *args, **kwargs):
        user_id = get_user_id(request)
        
        if user_id is None:
            return Response([])

        query_args = {"user_id": user_id}
        keywords = request.GET.get("keyword", "")
        keyword_arr = keywords.split(" ")

        q_obj = Q()
        for keyword in keyword_arr:
            if keyword:
                q_obj &= Q(word__icontains=keyword)

        queryset = StoreTranslate.objects.filter(q_obj, **query_args).order_by("-times", "freq")
        serializer = StoreTranslateSerializer(queryset, many=True)
        data = serializer.data

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(data, request)

        if page is not None:
            return paginator.get_paginated_response(page)
        return Response(data)
    
    
class StoreArticleViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = StoreEnglishArticle.objects.filter().all()
    serializer_class = StoreEnglishArticleSerializer
    pagination_class = PageNumberPagination

    def list(self, request, *args, **kwargs):
        user_id = get_user_id(request)
        logger.debug(f"get list by {user_id}")
        
        if user_id is None:
            return Response([])

        query_args = {"user_id": user_id}
        keywords = request.GET.get("keyword", "")
        keyword_arr = keywords.split(" ")

        q_obj = Q()
        for keyword in keyword_arr:
            if keyword:
                q_obj &= Q(title__icontains=keyword)

        queryset = StoreEnglishArticle.objects.filter(q_obj, **query_args)
        serializer = StoreEnglishArticleSerializer(queryset, many=True)
        data = serializer.data
        
        logger.debug(f'total {len(data)}')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(data, request)

        if page is not None:
            return paginator.get_paginated_response(page)
        return Response(data)

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
            logger.warning(f"translate_sentence {e}")
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
        logger.debug(f"translate rtype:{rtype} word:{word} sentence:{sentence}")
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
            logger.warning(f"translate_sentence {e}")
            ret = False
            answer = str(e)
        return do_result(ret, answer)

    def translate_word_role(self, args, word, sentence):
        try:
            ret, answer = translate.translate_word_role(args["user_id"], word, sentence)
        except Exception as e:
            logger.warning(f"translate_sentence {e}")
            ret = False
            answer = str(e)
        return do_result(ret, answer)

class TranslateLearnView(APIView):
    def post(self, request):
        return self.do_learn(request)

    def get(self, request):
        return self.do_learn(request)

    def do_learn(self, request):
        args = parse_common_args(request)
        logger.info(f"translate learn {args}")
        rtype = request.GET.get("rtype", request.POST.get("rtype", "get_unknown"))
        if rtype == "get_words":
            return self.get_words(args, request)
        elif rtype == "get_review":
            return self.get_review(args)
        elif rtype == "update":
            return self.update(request)
        elif rtype == "get_sentence":
            return self.get_sentence(args, request)
        return do_result(False, f"not support {rtype}")
    
    def get_words(self, args, request):
        if args['user_id'] is None:
            return do_result(False, {"list": []})
        status = request.GET.get("status", request.POST.get("status", "not_learned"))
        dateStr = request.GET.get("date", request.POST.get("date", None))
        limit = 100
        if dateStr is not None:
            queryset = StoreTranslate.objects.filter(
                user_id=args['user_id'], status=status, 
                updated_time__gte=dateStr).order_by("freq").all()[:limit]
        else:
            queryset = StoreTranslate.objects.filter(
                user_id=args['user_id'], status=status
                ).order_by("freq").all()[:limit]
        serializer = StoreTranslateSerializer(queryset, many=True)
        data = serializer.data
        json_data = json.loads(json.dumps(data))
        return do_result(True, {"list": json_data})

    def update(self, request):
        listData = request.GET.get("list", request.POST.get("list", None))
        if listData is None:
            return do_result(False, "no list")
        listData = json.loads(listData)
        if len(listData) == 0:
            return do_result(False, "empty list")
        logger.warning(f"update {listData}")
        for item in listData:
            word = item.get("word", None)
            status = item.get("status", None)
            info = item.get("info", None)
            if word is None or status is None:
                continue
            try:
                StoreTranslate.objects.filter(idx=item.get("idx")).update(status=status, info=info, updated_time=timezone.now());
            except Exception as e:
                logger.warning(f"update {e}")
                return do_result(False, str(e))
        return do_result(True, f"update items")
    
    def get_sentence(self, args, request):
        word = request.GET.get("word", request.POST.get("word", None))
        if word is None:
            return do_result(False, "no word")
        if args['user_id'] is None:
            return do_result(False, "no user")

        demo = '{"sentence": "This is a book.", "sentence_meaning": "这是一本书。", "word_meaning": "书"}'
        query = "Please give me a simple sentence with the word '{word}' in it, and translate the sentence to Chinese. result like {demo}".format(
            word=word, demo=demo
        )
        ret, dic, detail = llm_query_json(
            args['user_id'], MSG_ROLE, query, "translate", debug=True
        )
        sentence = dic['sentence']
        sentence_trans = dic['sentence_meaning']
        word_trans = dic['word_meaning']
        return do_result(True, {
            "sentence": sentence, 
            "sentence_meaning": sentence_trans,
            "word_meaning": word_trans
        })
