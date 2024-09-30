"""
Remove stems and affixes
"""

import os
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from . import freq_en

os.environ["NLTK_DATA"] = "/exports/data/nltk_data/"  # later move to other dir

# Instantiate Root Reducer
lemmatizer = WordNetLemmatizer()


# Used to convert individual words
def regular_lemma(base_x):
    """
    Find the base form of the word according to the rules for nouns/verbs/adjectives respectively
    """
    x = base_x
    y = lemmatizer.lemmatize(x, pos="v")
    if y != x:
        return y
    y = lemmatizer.lemmatize(x, pos="n")
    if y != x:
        return y
    y = lemmatizer.lemmatize(x, pos="a")
    if y != x:
        return y
    y = lemmatizer.lemmatize(x, pos="r")
    if y != x:
        return y
    y = lemmatizer.lemmatize(x, pos="s")
    if y != x:
        return y
    x = x.lower()
    y = lemmatizer.lemmatize(x, pos="v")
    if y != x:
        return y
    y = lemmatizer.lemmatize(x, pos="n")
    if y != x:
        return y
    y = lemmatizer.lemmatize(x, pos="a")
    if y != x:
        return y
    y = lemmatizer.lemmatize(x, pos="r")
    if y != x:
        return y
    y = lemmatizer.lemmatize(x, pos="s")
    if y != x:
        return y
    return x


def regular(word):
    word = word.replace("(", "")
    word = word.replace(")", "")
    word = word.replace(",", "")
    return regular_lemma(word.lower())


def extract_first_en_seq(word):
    while len(word) > 0 and (not word[0].isalpha()):
        word = word[1:]
    for i in range(len(word)):
        if not word[i].isalpha():
            word = word[:i]
            break
    return word


# Used to convert verbs in sentences
# Used to convert part-of-speech tagging results into WordNet tagging format
def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith("J"):
        return wordnet.ADJ
    elif treebank_tag.startswith("V"):
        return wordnet.VERB
    elif treebank_tag.startswith("N"):
        return wordnet.NOUN
    elif treebank_tag.startswith("R"):
        return wordnet.ADV
    else:
        return ""


# Custom function to implement tense normalization for verbs
def lemmatize_verbs(text):
    # Begin with a part-of-speech annotation
    pos_tags = nltk.pos_tag(nltk.word_tokenize(text))
    # Rooting Verbs
    result = []
    for word, pos in pos_tags:
        if pos.startswith("V"):
            # Convert part-of-speech tagging to WordNet's tag format
            wordnet_pos = get_wordnet_pos(pos)
            if wordnet_pos != "":
                # If the part of speech is a verb, perform stemming first.
                base_word = lemmatizer.lemmatize(word, wordnet_pos)
                # and then tense reduction in base form
                if base_word == word:
                    # If it is already in its base form, there is no need to restore the tense.
                    result.append(word)
                else:
                    # If it is not in the basic form, try tense restoration
                    lemma_word = lemmatizer.lemmatize(base_word, wordnet.VERB)
                    # If unable to restore, return the base form
                    if lemma_word == base_word:
                        result.append(base_word)
                    else:
                        result.append(lemma_word)
            else:
                result.append(word)
        else:
            result.append(word)
    return " ".join(result)


class RootFinder:
    @staticmethod
    def get_root_manual(word):
        """
        Manually remove the suffix
        """
        arr = {
            "ible": "y",
            "iness": "y",
            "ness": "",
            "ing": "",
            "ly": "",
            "ed": "",
            "en": "",
            "s": "",
        }
        edit = True
        while edit:
            edit = False
            for key, value in arr.items():
                if word.endswith(key):
                    word = word.replace(key, value)
                    edit = True
                    freq = freq_en.FreqTools.get_instance().get_freq(word)
                    if freq != -1:
                        print("@@@@@@@ word", word, freq)
                        return word
                    break
        # word = porter_stemmer.stem(word)
        return word


if __name__ == "__main__":
    # Enter Pending Text
    data = """
    Data science is an interdisciplinary field that uses scientific methods, processes, algorithms, and systems to extract knowledge and insights from many structured and unstructured data.
    Artificial intelligence (AI) is the simulation of human intelligence processes by computer systems. These processes include learning (the acquisition of information and rules for using the information), reasoning (using rules to reach approximate or definite conclusions), and self-correction.
    Python programming language is a high-level programming language that is widely used in data science, statistics, and machine learning. 
    She finished her work and then meandered through the park for an hour.
    """

    # Calling a Custom Rooting Function for Root Restoration
    roots = lemmatize_verbs(data)

    # Output the rooted result of the word
    print(roots)
