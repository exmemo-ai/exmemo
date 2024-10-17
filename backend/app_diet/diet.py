import re
import os
import json
import traceback
import pandas as pd
from datetime import timedelta
import datetime

from django.utils.translation import gettext as _
from loguru import logger

from backend.common.user.user import *
from backend.common.llm.llm_hub import llm_query

from .models import StoreDiet, StoreFood

ROLE_DIET = _("you_are_a_clinical_nutritionist")


def get_int(data):
    try:
        return int(float(data))
    except:
        return -1


def del_diet(content, uid):
    """
    Delete Diet Record
    """
    date = get_date(content)
    time_of_day = get_time_of_day(content, default_now=False)
    if time_of_day is None:
        data = StoreDiet.objects.filter(date=date, uid=uid)
    else:
        data = StoreDiet.objects.filter(date=date, time_of_day=time_of_day, uid=uid)

    if time_of_day is None:
        time_of_day = ""

    if len(data) == 0:
        return True, _("no_diet_record_found_for_{time_of_day}_on_{date}").format(
            date=date, time_of_day=time_of_day
        )

    df = pd.DataFrame.from_records(data.values())
    df["time_of_day_idx"] = df["time_of_day"].apply(lambda x: get_time_of_day_idx(x))
    df = df.sort_values("time_of_day_idx")
    keywords = []
    for idx, item in df.iterrows():
        if item["food"] in content:
            StoreDiet.objects.filter(idx=item["idx"]).delete()
            logger.debug(f'delete {item["food"]}')
            keywords.append(item["food"])

    if len(keywords) == 0:
        return True, _(
            "no_dietary_records_found_for_keywords_related_to_{time_of_day}_on_{date}"
        ).format(date=date, time_of_day=time_of_day)
    else:
        return True, _(
            "successfully_deleted_the_diet_record_for_{time_of_day}_on_{date}_with_keywords_{keywords}"
        ).format(date=date, time_of_day=time_of_day, keywords=",".join(keywords))


def edit_diet(content, uid):
    """
    Dietary Record
    """
    df, info = parse_content(content, uid)
    logger.debug("edit_diet")
    logger.debug(df)
    logger.debug(info)
    if df is not None:
        save_diet_to_db(content, df, uid)
        string = calc_diet(content, uid)
        return True, string
    else:
        return True, info


def save_diet_to_db(content, df, uid):
    """
    Save dietary records to the database
    """
    now = datetime.datetime.now()
    timestr = now.strftime("%Y-%m-%d %H:%M:%S")
    date = get_date(content)
    time_of_day = get_time_of_day(content)

    for idx, item in df.iterrows():
        print(
            item["food"],
            get_int(item["weight"]),
            get_int(item["kc"]),
            date,
            time_of_day,
            uid,
            timestr,
        )

        idx = StoreDiet.calc_idx_static(uid, item["food"], date, time_of_day)
        if not StoreDiet.objects.filter(idx=idx).exists():
            logger.debug(f"insert {idx}")
            StoreDiet.objects.create(
                food=item["food"],
                weight=get_int(item["weight"]),
                kc=get_int(item["kc"]),
                date=date,
                time_of_day=time_of_day,
                uid=uid,
                created_time=timestr,
            )
        else:
            logger.debug(f"update {idx}")
            StoreDiet.objects.filter(idx=idx).update(
                weight=get_int(item["weight"]), kc=get_int(item["kc"])
            )


def calc_diet(content, uid):
    """
    Count Dietary Records
    """
    try:
        date = get_date(content)
        string = ""
        data = StoreDiet.objects.filter(date=date, uid=uid)
        df = pd.DataFrame.from_records(data.values())
        if len(df) == 0:
            return _("no_valid_records_founds_dot_")
        df["time_of_day_idx"] = df["time_of_day"].apply(
            lambda x: get_time_of_day_idx(x)
        )
        df = df.sort_values("time_of_day_idx")
        grp = df.groupby("time_of_day", sort=False)
        for desc, items in grp:
            string += f"\n{desc},{items['kc'].sum()}kc"
            for idx, item in items.iterrows():
                string += f"\n  {item['food']},{item['weight']}g,{item['kc']}kc"
        string += "\n" + _("total_calories_colon__{kc}kc").format(kc=df["kc"].sum())
        return string
    except Exception as e:
        logger.warning(f"calc_diet failed {e}")
        traceback.print_exc()
        return _("no_valid_records_founds_dot_")


def parse_content(content, uid):
    """
    Parse the dietary content described in the text
    """
    ret, info = parse_inner(content, use_gpt4=False, uid=uid)
    if ret is not None:
        return ret, info
    ret, info = parse_inner(content, use_gpt4=True, uid=uid)
    return ret, info


def parse_inner(content, use_gpt4, uid, debug=True):
    """
    Internal implementation for parsing textual descriptions of dietary content
    """
    demo = '[{"food":"Croissant","weight":"200","kc":240}]"'
    question = "User input is as follows: '{content}',\nPlease identify the food based on the user input, calculate the calories, and if the weight is not specified, use the general case.\nReturn the food name, weight, and calories as a JSON array, in the format of: {demo}. Note: return only the JSON string, no other content.".format(
        content=content, demo=demo
    )
    if use_gpt4:
        ret, answer, detail = llm_query(
            uid, ROLE_DIET, question, "diet", engine_type="gpt4", debug=debug
        )
    else:
        ret, answer, detail = llm_query(uid, ROLE_DIET, question, "diet", debug=debug)

    if ret:
        try:
            # Extract JSON string using regex
            # logger.debug('before re, answer: ' + answer)
            pattern = re.compile(r"(\[.*\])")
            match = pattern.search(answer)
            if match is not None:
                answer = match.group(1)
            # logger.debug('after re, answer: ' + answer)
            dic = eval(answer)
            if type(dic) == dict:
                dic = [dic]
            df = pd.DataFrame(dic)
            df = adjust_df(df, uid)
            return df, None
        except Exception as e:
            logger.warning(f"add_diet failed {answer} {e}")
            traceback.print_exc()
    return None, answer


def adjust_df(df, uid):
    """
    Adjust Calories
    """
    for idx, item in df.iterrows():
        llm_kc = int(get_int(item["kc"]) / get_int(get_int(item["weight"])) * 100)
        data_kc = Food().get_calorie(
            item["food"], default_value=llm_kc, uid=uid, debug=False
        )
        # If the difference between llm_kc and data_kc exceeds 10%, then print it out
        if abs(llm_kc - data_kc) > 30:
            print(idx, item["food"], item["weight"], item["kc"], "\t", llm_kc, data_kc)
            print("  ", item["kc"], int(get_int(item["weight"]) * data_kc / 100))
            # Update df
            df.loc[idx, "kc"] = int(get_int(item["weight"]) * data_kc / 100)
    return df


class Food:
    # Write as singleton pattern
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(Food, cls).__new__(cls)
        return cls.__instance

    def __init__(self) -> None:
        self.df = self.load()

    def load(self, inser_if_empty=True):
        objs = StoreFood.objects.all()
        if len(objs) > 0:
            return pd.DataFrame(objs.values())
        elif inser_if_empty:
            # Take the current file path
            current_path = os.path.dirname(os.path.abspath(__file__))
            # Take the parent path
            SRC_DIR = os.path.dirname(current_path)
            # SRC_DIR = os.path.dirname(os.path.dirname(current_path))
            file_path = os.path.join(SRC_DIR, "data/food.csv")
            df = pd.read_csv(file_path)
            # Warehousing
            now = datetime.datetime.now()
            timestr = now.strftime("%Y-%m-%d %H:%M:%S")
            for idx, item in df.iterrows():
                if idx % 100 == 0:
                    logger.debug(f"load {idx}")
                if not StoreFood.objects.filter(food=item["name"]).exists():
                    StoreFood.objects.create(
                        food=item["name"],
                        kc=get_int(item["heat"]),
                        carbs=get_int(item["carbohydrate"]),
                        fat=get_int(item["fat"]),
                        protein=get_int(item["protein"]),
                        created_time=timestr,
                    )
            return self.load(inser_if_empty=False)
        return pd.DataFrame()

    def add_food(self, name, calorie, debug=False):
        """
        Add Food
        """
        # Add a row to the dataframe without using append
        tmp = self.df[self.df["food"] == name]
        if not tmp.empty:
            if debug:
                print(_("already_exists_{name}").format(name=name))
            return
        self.df = pd.concat(
            [self.df, pd.DataFrame([{"food": name, "kc": calorie}])]
        ).reset_index(drop=True)
        # self.df.to_csv(self.file_path, index=False)
        StoreFood.objects.create(
            food=name, kc=calorie, created_time=datetime.datetime.now()
        )
        if debug:
            print(
                _("add_successful_{name}_{calorie}").format(name=name, calorie=calorie)
            )

    def get_calorie_inner(self, name, debug=False):
        """
        Get the calories of the food
        """
        tmp = self.df[self.df["food"] == name]
        if tmp.empty:
            tmp = self.df[self.df["food"].str.contains(name)]
        if tmp.empty:
            return 0
        else:
            if debug:
                print(tmp[["food", "kc"]].reset_index(drop=True))
            return tmp["kc"].median()

    def get_food(self, name, uid, use_llm=True, debug=False):
        tmp = self.df[self.df["food"] == name]
        if not tmp.empty:
            return name
        tmp = self.df[self.df["food"].str.contains(name)]
        if tmp.empty:
            return None
        if use_llm:
            ll = tmp["food"].tolist()
            ll = sorted(ll, key=lambda x: len(x))
            ret = self.query(name, ll[:10], uid, debug=debug)
            if ret is None:
                return None
            else:
                real_name = self.get_food(ret, uid, use_llm=False, debug=debug)
                if real_name is None:
                    return None
                else:
                    self.add_food(
                        real_name,
                        self.get_calorie_inner(real_name, debug=debug),
                        debug=debug,
                    )
                    return real_name

    def query(self, food, ll, uid, debug=False):
        """
        Query the exact name of the food
        """
        try:
            question = 'If I say I ate "{food}", then which of the following foods is the most likely one: {foods}? Only respond with the name of the food, do not provide any other information.'.format(
                food=food, foods=",".join(ll)
            )
            ret, answer, _ = llm_query(uid, ROLE_DIET, question, "diet")
            if ret:
                if debug:
                    print(question)
                    print(answer)
                return answer
        except:
            print(_("fuzzy_query_failed"))
        return None

    def get_calorie(
        self, name, default_value=-1, use_llm=True, uid=DEFAULT_USER, debug=False
    ):
        """
        Get the calories of the food
        """
        real_name = self.get_food(
            name, uid, use_llm=use_llm, debug=debug
        )  # Find the exact name
        if real_name is None:
            if debug:
                print(_("no_food_found_with_the_name_{name}").format(name=name))
            if (
                default_value != -1
            ):  # If there is a default value, use the default value
                self.add_food(name, default_value, debug=debug)
                return default_value
            if use_llm:  # If not found, use llm to query
                self.find_food_calorie(name, uid, debug=debug)
                return self.get_calorie(name, use_llm=False, uid=uid, debug=debug)
            else:
                return 0  # If not found, return 0
        else:
            return self.get_calorie_inner(
                real_name, debug=debug
            )  # Fetching values directly from the library

    def find_food_calorie(self, name, uid, debug=False):
        """
        Get the calories of the food and store it in the database
        """
        try:
            demo = "{'food': 'apple','calorie': 52}"
            question = 'If I say I ate "{name}", what food did I most likely eat? How many kilocalories per 100 grams does it have? Please return in json format, like: {demo}, do not answer any other content.'.format(
                name=name, demo=demo
            )
            ret, answer, _ = llm_query(uid, ROLE_DIET, question, "diet", debug=debug)
            if ret:
                dic = json.loads(answer)
                self.add_food(dic["food"], dic["calorie"], debug=debug)
        except Exception as e:
            print(e, "question", question)


def get_date(content):
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    dic = {
        _("today"): 0,
        _("yesterday"): -1,
        _("the_day_before_yesterday"): -2,
        _("big_day_before_yesterday"): -3,
    }
    for key in dic:
        if key in content:
            date = (now + timedelta(days=dic[key])).strftime("%Y-%m-%d")
            return date
    year = now.year
    month = now.month
    day = now.day
    # later parse date by llm
    pattern = re.compile(
        _("{month}_month_{day}_day").format(month=r"(\d{1,2})", day=r"(\d{1,2})")
    )
    match = pattern.search(content)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        date = f"{year}-{month}-{day}"
    return date


def get_time_of_day(base_content, default_now=True):
    SPECIAL_LIST = [_("spam")]
    content = base_content
    if content is not None:
        for item in SPECIAL_LIST:
            content = content.replace(item, "")
    dic = {
        _("extra_meal_in_the_morning"): [_("early_morning")],
        _("breakfast"): [_("breakfast"), _("breakfast"), _("morning")],
        _("morning_extra_meal"): [_("am")],
        _("lunch"): [_("lunch"), _("lunch"), _("noon")],
        _("extra_meal_in_the_afternoon"): [_("pm")],
        _("dinner"): [_("dinner2"), _("dinner"), _("night")],
        _("evening_extra_meals"): [_("night"), _("midnight"), _("midnight_snack")],
    }
    for key in dic:
        for item in dic[key]:
            if item in content:
                return key
    if not default_now:
        return None
    now = datetime.datetime.now()
    hour = now.hour
    if hour >= 0 and hour < 6:
        time_of_day = _("extra_meal_in_the_morning")
    elif hour >= 6 and hour < 9:
        time_of_day = _("breakfast")
    elif hour >= 9 and hour < 11:
        time_of_day = _("morning_extra_meal")
    elif hour >= 11 and hour < 13:
        time_of_day = _("lunch")
    elif hour >= 13 and hour < 17:
        time_of_day = _("extra_meal_in_the_afternoon")
    elif hour >= 17 and hour < 20:
        time_of_day = _("dinner")
    elif hour >= 20 and hour < 24:
        time_of_day = _("evening_extra_meals")
    return time_of_day


def get_time_of_day_idx(time_of_day):
    dic = {
        _("extra_meal_in_the_morning"): 0,
        _("breakfast"): 1,
        _("morning_extra_meal"): 2,
        _("lunch"): 3,
        _("extra_meal_in_the_afternoon"): 4,
        _("dinner"): 5,
        _("evening_extra_meals"): 6,
    }
    return dic[time_of_day]
