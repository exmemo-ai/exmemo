import copy
import json
from typing import List
from loguru import logger
import threading
from swarm.util import debug_print
from swarm import Swarm
from swarm.types import (
    Agent,
    Response,
)

class ExSmarm(Swarm):
    def _check_locks(self, d: dict, path: str = '') -> None:
        for k, v in d.items():
            current_path = f"{path}.{k}" if path else k
            if isinstance(v, threading._RLock):
                print(f"Found lock at {current_path}: {v}")
            elif isinstance(v, dict):
                self._check_locks(v, current_path)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        self._check_locks(item, f"{current_path}[{i}]")
    
    def run(
        self,
        agent: Agent,
        messages: List,
        context_variables: dict = {},
        model_override: str = None,
        stream: bool = False,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ) -> Response:
        if stream:
            return self.run_and_stream(
                agent=agent,
                messages=messages,
                context_variables=context_variables,
                model_override=model_override,
                debug=debug,
                max_turns=max_turns,
                execute_tools=execute_tools,
            )
        active_agent = agent
        
        print("Checking for locks in context_variables:") # debug
        self._check_locks(context_variables)

        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)
        total_count = 0

        while len(history) - init_len < max_turns and active_agent:
            # get completion with current history, agent
            completion = self.get_chat_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=stream,
                debug=debug,
            )
            message = completion.choices[0].message
            total_count += completion.usage.total_tokens
            debug_print(debug, '@@@ response', completion.usage.total_tokens)
            debug_print(debug, "Received completion:", message)
            message.sender = active_agent.name
            history.append(
                json.loads(message.model_dump_json())
            )  # to avoid OpenAI types (?)

            if not message.tool_calls or not execute_tools:
                debug_print(debug, "Ending turn.")
                break

            # handle function calls, updating context_variables, and switching agents
            logger.debug(f"message.tool_calls: {message.tool_calls}")
            if len(message.tool_calls) == 1:
                tool_calls = message.tool_calls
            else:
                tool_calls = message.tool_calls[:1]
                logger.debug('only call the first tool')
            partial_response = self.handle_tool_calls(
                tool_calls, 
                active_agent.functions, 
                context_variables, debug
            )
            logger.debug(f'message.tool_calls finished {partial_response}, check {len(history) - init_len} < {max_turns}')
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            if partial_response.agent:
                active_agent = partial_response.agent
 
        context_variables['total_count'] = total_count
        return Response(
            messages=history[init_len:],
            agent=active_agent,
            context_variables=context_variables,
        )