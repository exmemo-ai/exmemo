import os
import re
import time
import traceback
from loguru import logger

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from django.utils.translation import gettext as _

from backend.common.llm import llm_tools
from backend.common.user.user import *
from backend.common.user.resource import *
from backend.common.utils import text_tools 

EMBEDDING_CHUNK_SIZE = 512

def llm_query(uid, role, question, app, engine_type=None, debug=False):
    start_time = time.time()
    user = UserManager.get_instance().get_user(uid)

    ret, desc = llm_tools.check_llm_limit(user, debug)
    if not ret:
        return ret, desc, {}
        
    if engine_type is None:
        engine_type = user.get("llm_tool_model", None)
    try:
        llm_info = llm_tools.LLMInfo.get_info(engine_type, 'llm_tool_model')
        if debug:
            logger.debug(f"Role {role}")
            logger.debug(f"Question {question}")
            logger.debug(f"Proxy {os.getenv('HTTPS_PROXY')}")
        if llm_info.api_method == "gemini":
            ret, answer, token_count = llm_tools.query_gemini(
                role, question, api_key=llm_info.api_key, model_name=llm_info.model_name, debug=debug
            )
        else:
            ret, answer, token_count = llm_tools.query_openai(
                role,
                question,
                api_key=llm_info.api_key,
                url=llm_info.url,
                model_name=llm_info.model_name,
                debug=debug,
            )
        if ret:
            duration = round(time.time() - start_time, 3)    
            dic = llm_tools.save_llm_usage(user, app, llm_info.get_desc(), duration, token_count)
            if debug:
                logger.debug("---------------------------")
                logger.debug("Answer: {answer}...".format(answer=answer[:50]))
                logger.debug(f"desc: {dic}")
            return ret, answer, dic
    except Exception as e:
        logger.warning(f"{engine_type} failed {e}")
        traceback.print_exc()
    return False, _("call_failed"), {"token_count": 0}


def find_first_json(s):
    json_pattern = re.compile(r"\{.*?\}", re.DOTALL)
    match = json_pattern.search(s)

    while match:
        json_string = match.group(0)
        try:
            json_object = json.loads(json_string.replace("'", '"'))
            return json_object
        except json.JSONDecodeError:
            s = s[match.end() :]
            match = json_pattern.search(s)
    return None


def llm_query_json(uid, role, question, app, engine_type=None, debug=False):
    ret, answer, dic = llm_query(uid, role, question, app, engine_type, debug)
    if ret:
        json_object = text_tools.parse_json(answer)
        if json_object is not None:
            return ret, json_object, dic
    return ret, {}, dic


class EmbeddingTools:
    @staticmethod
    def get_instance():
        if not hasattr(EmbeddingTools, "_instance"):
            EmbeddingTools._instance = EmbeddingTools()
        return EmbeddingTools._instance

    def __init__(self):
        self.model = None
        self.model_name = None
        self.model_ollama_url = None

    @staticmethod
    def get_model_name(use_embedding=True):
        if not use_embedding:
            return None
        embedding_type, ollama_url, ollama_model = (
            EmbeddingTools.load_embedding_setting()
        )
        if embedding_type == "none":
            return None
        if embedding_type == "openai":
            return embedding_type
        if ollama_model == "none" or ollama_model is None:
            return None
        return ollama_model

    def get_model(self):
        """
        Get model instance
        args:
            model_name: None, openai, ollama
        """
        embedding_type, ollama_url, ollama_model = (
            EmbeddingTools.load_embedding_setting()
        )
        model_name = EmbeddingTools.get_model_name()
        if self.model_name is None and model_name is None:
            return self.model
        if self.model_name == model_name:
            if model_name == "openai":
                return self.model
            if model_name == "ollama" and self.model_ollama_url == ollama_url:
                return self.model

        logger.info(f"now loading model {model_name}")
        if embedding_type == "openai":
            self.model = OpenAIEmbeddings()
        elif embedding_type == "ollama":
            if (
                ollama_url is None
                or ollama_url == "none"
                or ollama_model is None
                or ollama_model == "none"
            ):
                return None
            self.model = OllamaEmbeddings(base_url=ollama_url, model=ollama_model)
        else:  # None
            self.model = None
        self.model_name = model_name
        self.model_ollama_url = ollama_url
        return self.model

    @staticmethod
    def split(raw, chunk_size=EMBEDDING_CHUNK_SIZE, chunk_overlap=50):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        return text_splitter.split_text(raw)

    @staticmethod
    def use_embedding():
        val = os.getenv("USE_EMBEDDING", "False")
        if val.lower() == "true":
            return True
        return False

    @staticmethod
    def load_embedding_setting():
        embedding_type = os.getenv("EMBEDDING_TYPE", "none")
        ollama_url = os.getenv("EMBEDDING_OLLAMA_URL", None)
        ollama_model = os.getenv("EMBEDDING_OLLAMA_MODEL", None)
        return embedding_type, ollama_url, ollama_model

    @staticmethod
    def do_embedding(all_splits, use_embedding, debug=False):
        ret = False
        embeddings = []
        if debug:
            logger.info(f"embedding {use_embedding}")
        try:
            if not use_embedding:
                embeddings = [None for split in all_splits]
            else:
                model = EmbeddingTools.get_instance().get_model()
                if debug:
                    logger.info(f"embedding model {model}")
                if model is not None:
                    embeddings = model.embed_documents(all_splits)
                    ret = True
                else:
                    embeddings = [None for split in all_splits]
        except Exception as e:
            logger.warning(f"failed {e}")
            embeddings = [None for split in all_splits]
        return ret, embeddings
