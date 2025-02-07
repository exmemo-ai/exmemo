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
from app_translate import word_processor


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
        elif rtype == "review":
            return self.get_review(args)
        elif rtype == "dictation":
            return self.get_dictation(args)
        elif rtype == "update":
            return self.update(request)
        elif rtype == "get_sentence":
            return self.get_sentence(args, request)
        elif rtype == "summary":
            return self.summary(args, request)
        elif rtype == "insert_wordlist":
            return self.insert_wordlist(args, request)
        elif rtype == "delete_wordlist":
            return self.delete_wordlist(args, request)
        elif rtype == "get_wordsfrom":
            return self.get_wordsfrom(args)
        return do_result(False, f"not support {rtype}")
    
    def get_wordsfrom(self, args):
        if args['user_id'] is None:
            return do_result(False, {"list": []})
        queryset = StoreTranslate.objects.values('wfrom').distinct()
        wordsfrom = [item['wfrom'] for item in queryset]
        wordsfrom = list(set(wordsfrom)) + ['ALL']
        return do_result(True, {"list": wordsfrom})
    
    def insert_wordlist(self, args, request):
        wfrom = request.GET.get("wfrom", request.POST.get("wfrom", None))
        if wfrom is None:
            return do_result(False, "no xfrom")
        if args['user_id'] is None:
            return do_result(False, "no user")
        if wfrom == "JHSW_1600":
            word_processor.insert_words(args['user_id'], wfrom = wfrom)
        elif wfrom == "HSW_3500":
            word_processor.insert_words(args['user_id'], wfrom = wfrom)
        elif wfrom.startswith("BASE_"):
            word_processor.insert_words(args['user_id'], wfrom = 'BASE', limit=int(wfrom[5:]))
        else:
            return do_result(False, f"no support wfrom {wfrom}")
        return do_result(True, "ok")
    
    def delete_wordlist(self, args, request):
        status = request.GET.get("status", request.POST.get("status", None))
        if status is None:
            return do_result(False, "no status")
        if args['user_id'] is None:
            return do_result(False, "no user")
        if status == "not_learned":
            StoreTranslate.objects.filter(user_id=args['user_id'], status='not_learned').delete()
        elif status == "learned":
            StoreTranslate.objects.filter(user_id=args['user_id'], status='learned').delete()
        elif status == "all":
            StoreTranslate.objects.filter(user_id=args['user_id']).delete()
        else:
            return do_result(False, f"no support status {status}")
        return do_result(True, "ok")
    
    def get_words(self, args, request):
        if args['user_id'] is None:
            return do_result(False, {"list": []})
        status = request.GET.get("status", request.POST.get("status", "not_learned"))
        dateStr = request.GET.get("date", request.POST.get("date", None))
        wfrom = request.GET.get("wfrom", request.POST.get("wfrom", None))
        limit = 100
        if dateStr is not None:
            queryset = StoreTranslate.objects.filter(
                user_id=args['user_id'], status=status, 
                updated_time__gte=dateStr)
        else:
            queryset = StoreTranslate.objects.filter(
                user_id=args['user_id'], status=status
                )
        if wfrom is not None and wfrom != "ALL":
            queryset = queryset.filter(wfrom=wfrom)
        queryset = queryset.order_by("freq").all()[:limit]
        serializer = StoreTranslateSerializer(queryset, many=True)
        data = serializer.data
        json_data = json.loads(json.dumps(data))
        return do_result(True, {"list": json_data})

    def get_review(self, args):
        if args['user_id'] is None:
            return do_result(False, {"list": []})
        status = "review"
        limit = 100
        queryset = StoreTranslate.objects.filter(
            user_id=args['user_id'], status=status
            ).order_by("freq").all()[:limit]
        serializer = StoreTranslateSerializer(queryset, many=True)
        data = serializer.data
        date = timezone.now().strftime("%Y-%m-%d")
        ret = []
        for item in data:
            info = item.get("info", None)
            if info is None:
                ret.append(item)
                continue
            learn_date = None
            if 'opt' in info:
                learn_date = info['opt'].get("learn_date", None)
            if learn_date is None:
                learn_date = info.get("learn_date", None)
            if learn_date is None or learn_date != date:
                ret.append(item)
        json_data = json.loads(json.dumps(ret))
        return do_result(True, {"list": json_data})

    def get_dictation(self, args):
        if args['user_id'] is None:
            return do_result(False, {"list": []})
        status = "review"
        limit = 100
        queryset = StoreTranslate.objects.filter(
            user_id=args['user_id'], status=status
            ).order_by("freq").all()[:limit]
        serializer = StoreTranslateSerializer(queryset, many=True)
        data = serializer.data
        date = timezone.now().strftime("%Y-%m-%d")
        ret = []
        for item in data:
            info = item.get("info", None)
            if info is None:
                continue
            learn_date = None
            if 'opt' in info:
                learn_date = info['opt'].get("learn_date", None)
            if learn_date is None:
                learn_date = info.get("learn_date", None)
            if learn_date == date:
                ret.append(item)
        json_data = json.loads(json.dumps(ret))
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
        try: 
            stored_examples = StoreTranslate.objects.filter(word=word, user_id=args['user_id'])
            if stored_examples.exists():
                obj = stored_examples.first()
                examples = None
                if 'base' in obj.info and 'example_list' in obj.info['base']:
                    examples = obj.info['base']['example_list']
                elif 'examples' in obj.info:
                    examples = obj.info['examples']
                if examples is not None:
                    logger.info(f'examples {examples}')
                    if isinstance(examples, list) and len(examples) > 0 and 'sentence' in examples[0]:
                        return do_result(True, {"word": word, "examples": examples})
        except Exception as e:
            logger.warning(f"get_example {e}")
        wm = word_processor.WordManager.get_instance()
        wordItem = wm.get_word(word)
        if wordItem is not None and len(wordItem.example_list) > 0:
            self.update_db(args['user_id'], word, wordItem, None)
            return do_result(True, {"word": word, "examples": wordItem.example_list})
        ret, example = translate.generate_sentence_example(args['user_id'], word)
        if ret:
            self.update_db(args['user_id'], word, None, [example])
            return do_result(True, {"word": word, "examples": [example]})
        return do_result(False, "generate sentence error")
    

    def update_db(self, user_id, word, base, example_list):
        try:
            logger.info(f'add example to db {base}, {example_list}')
            stored_examples = StoreTranslate.objects.filter(word=word, user_id=user_id)
            if stored_examples.exists():
                obj = stored_examples.first()
                if base is not None:
                    obj.info['base'] = base.serialize()
                if example_list is not None:
                    obj.info['base']['example_list'] = example_list
                obj.save()
        except Exception as e:
            logger.warning(f"get_example insert to db failed, {e}")


    def summary(self, args, request):
        dateStr = request.GET.get("date", request.POST.get("date", None))
        if dateStr == None:
            dateStr = timezone.now().strftime("%Y-%m-%d")
        totalWords = StoreTranslate.objects.filter(
            user_id=args['user_id']).count()
        not_learned = StoreTranslate.objects.filter(
            user_id=args['user_id'], status='not_learned').count()
        learned = StoreTranslate.objects.filter(
            user_id=args['user_id'], status='learned').count()
        learning = StoreTranslate.objects.filter(
            user_id=args['user_id'], status='learning').count()
        review = StoreTranslate.objects.filter(
            user_id=args['user_id'], status='review').count()

        #todayReview = StoreTranslate.objects.filter(
        #    user_id=args['user_id'], status='review', updated_time__gte=dateStr).count()        
        queryset = StoreTranslate.objects.filter(
            user_id=args['user_id'], status='review', updated_time__gte=dateStr)
        serializer = StoreTranslateSerializer(queryset, many=True)
        todayReview = 0
        for item in serializer.data:
            info = item.get("info", None)
            if info is not None and 'opt' in info and info['opt'].get("learn_date", None) == dateStr:
                todayReview+=1
        
        return do_result(True, {"total_words": totalWords, "learned": learned, 
                                "not_learned": not_learned, "today_review": todayReview, 
                                "today_learning": learning, "to_review": review})

