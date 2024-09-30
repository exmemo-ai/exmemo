import re
import pandas as pd
from django.utils.translation import gettext as _


def regular_keyword(keyword):
    """
    Standardize keywords, remove punctuation marks from the beginning and end
    """
    if keyword is None:
        return ""
    keyword = keyword.strip()
    # Remove punctuation marks at the end of the opening
    keyword = re.sub(r"^[,，.。!！?？]+", "", keyword)
    keyword = re.sub(r"[,，.。!！?？]+$", "", keyword)
    # Multiple spaces merged into one
    keyword = re.sub(r"\s+", " ", keyword)
    return keyword


def regular_str(text, del_enter=False, max_length=-1):
    """
    Normalize text by trimming leading and trailing spaces, and replacing multiple spaces with a single one
    """
    if pd.isna(text):
        return _("content_not_found")
    text = text.strip()
    # Replace multiple entries with one
    text = re.sub(r"\r\n", "\n", text)
    if del_enter:
        text = re.sub(r"\n", " ", text)
    if max_length != -1 and len(text) > max_length:
        text = text[:max_length] + "..."
    return text
