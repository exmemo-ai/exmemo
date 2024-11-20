import os
import traceback
from loguru import logger
from langchain_community.chat_models import ChatOpenAI

# from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationTokenBufferMemory
from langchain.memory.chat_memory import BaseChatMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import get_buffer_string
from .llm_tools import select_llm_model
from typing import Any, Dict


class MyCoversationMemory(ConversationTokenBufferMemory):
    """
    Solve the issue of unrecognized tokens returned by some LLMs.
    """

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        BaseChatMemory.save_context(self, inputs, outputs)
        buffer = self.chat_memory.messages
        try:
            curr_buffer_length = self.llm.get_num_tokens_from_messages(buffer)
        except Exception as e:  # some LLMs may return unrecognized tokens
            curr_buffer_length = sum(
                [self.llm.get_num_tokens(get_buffer_string([m])) for m in buffer]
            )
        if curr_buffer_length > self.max_token_limit:
            pruned_memory = []
            while curr_buffer_length > self.max_token_limit:
                pruned_memory.append(buffer.pop(0))
                curr_buffer_length = self.llm.get_num_tokens_from_messages(buffer)


class ChatEngine:
    """
    Conversation engine, this is a chat session
    demo:
        chat_engine = ChatEngine(model='gemini')
        chat_engine.predict("Hello")
    """

    def __init__(self, engine_type, debug=False):
        self.engine_type = engine_type
        self.api_method, api_key, url, model_name = select_llm_model(engine_type)
        if debug:
            logger.info(
                f"ChatEngine init: {engine_type} {self.api_method}, {api_key}, {url}, {model_name}"
            )
        else:
            logger.info(f"ChatEngine init: {engine_type}")
        if self.api_method == "gemini":
            self.llm = ChatGoogleGenerativeAI(
                model=model_name, google_api_key=api_key, max_output_tokens=500
            )
        else:
            self.llm = ChatOpenAI(
                model=model_name, openai_api_key=api_key, openai_api_base=url
            )
        self.memory = MyCoversationMemory(llm=self.llm, max_token_limit=1000)
        self.conversation = ConversationChain(
            llm=self.llm, memory=self.memory, verbose=False  # Show more details
        )

    def predict(self, input):
        ret = True
        count = 0
        try:
            if self.api_method == "gemini":
                answer = self.conversation.predict(input=input)
                count = self.llm.get_num_tokens(self.memory.buffer)
            elif self.engine_type.startswith("gpt"):
                with get_openai_callback() as cb:  # to save records
                    answer = self.conversation.predict(input=input)
                    count = cb.total_tokens
            else:
                answer = self.conversation.predict(input=input)
                count = self.llm.get_num_tokens(self.memory.buffer)
        except Exception as e:
            traceback.print_exc()
            logger.error(f"ChatEngine predict error: {e}")
            answer = str(e)
            count = 0
            ret = False
        return ret, answer, count

    def get_memory(self):
        return self.memory.buffer

    def clear_memory(self):
        self.memory.clear()