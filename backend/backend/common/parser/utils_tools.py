import datetime
import traceback
from collections import Counter


def most_common(ll):
    """
    Get the most frequent value in the array
    """
    try:
        return Counter(ll).most_common(1)[0][0]
    except Exception as e:
        print(e)
        traceback.print_exc()
    return None


def unique_list(l):
    """
    Used for array deduplication while maintaining the original order
    """
    ret = []
    for x in l:
        if x not in ret:
            ret.append(x)
    return ret


def parse_date(ndate):
    """
    Convert various date formats into datetime.datetime
    """
    if ndate is None:
        return None
    elif isinstance(ndate, datetime.datetime):
        pass
    elif isinstance(ndate, datetime.date):
        ndate = datetime.datetime(ndate.year, ndate.month, ndate.day)
    elif isinstance(ndate, str):
        ndate = datetime.datetime.strptime(ndate, "%Y-%m-%d")
    return ndate


def get_int(data):
    try:
        return int(float(data))
    except:
        return -1
