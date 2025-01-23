from django.utils.translation import gettext as _
from .user import *
from .models import StoreResourceUsage


class ResourceManager:
    __instance = None

    @staticmethod
    def get_instance():
        if not ResourceManager.__instance:
            ResourceManager.__instance = ResourceManager()
        return ResourceManager.__instance

    def add(self, uid, app, rtype, method, amount, during, status, info):
        if info is not None:
            info = json.dumps(info)
        data = StoreResourceUsage.objects.create(
            user_id=uid,
            app=app,
            rtype=rtype,
            method=method,
            amount=amount,
            during=during,
            status=status,
            info=info,
        )
        return data

    def summarize(self, uid):
        data = StoreResourceUsage.objects.filter(user_id=uid).all()
        dic = {}
        for d in data:
            if d.method not in dic:
                dic[d.method] = 0
            dic[d.method] += d.amount
        return dic

    def get_usage(self, uid, method=None, dtype="day", rtype=None, debug=False):
        today = datetime.date.today()
        if dtype == "day":
            day = today
        elif dtype == "week":
            day = today - datetime.timedelta(days=today.weekday())
        elif dtype == "month":
            day = datetime.date(today.year, today.month, 1)
        else:
            day = -1
        if debug:
            logger.debug(
                f"get_usage: method {method}, dtype {dtype}, rtype {rtype}, {day} {uid}"
            )
        
        if day == -1:
            data = StoreResourceUsage.objects.filter(user_id=uid)
        else:
            data = StoreResourceUsage.objects.filter(
                user_id=uid, updated_time__gte=day
            )
            
        if rtype == "default_llm":
            data = data.filter(rtype='llm', method__startswith='default')
        elif rtype == "other_llm":
            data = data.filter(rtype='llm').exclude(method__startswith='default')
        elif rtype is not None:
            data = data.filter(rtype=rtype)
            
        if method is not None:
            data = data.filter(method=method)
            
        data = data.all()
        count = 0
        for d in data:
            count += d.amount
        return count

    def get_usage_summary(self, uid):
        MODEL_MAP = {
            "tts": _("speech_synthesis"), 
            "default_llm": _("default_language_model"),
            "other_llm": _("custom_language_model")
        }
        TYPE_MAP = {
            "day": _("current_day"),
            "week": _("current_week"),
            "month": _("this_month"),
            "all": _("total"),
        }
        ret = []
        for dtype in ["day", "week", "month"]:
            arr = [_("{}_usage").format(TYPE_MAP[dtype])]
            for key, value in MODEL_MAP.items():
                count = self.get_usage(uid, rtype=key, dtype=dtype)
                arr.append(f" * {value}: {count}")
            ret.append("\n".join(arr))
        return "\n".join(ret)
