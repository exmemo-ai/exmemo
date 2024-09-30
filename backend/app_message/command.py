import re
import json
from loguru import logger
from django.utils.translation import gettext as _
from backend.common.llm.llm_hub import llm_query
from backend.common.user.user import *

LEVEL_TOP = 1
LEVEL_NORMAL = 2
MSG_ROLE = "You're a smart assistant"


class Command:
    def __init__(self, function, cmd_list=[], level=LEVEL_NORMAL):
        self.function = function
        self.cmd_list = cmd_list
        self.level = level

    def __repr__(self) -> str:
        print("Command:", self.cmd_list[0], "Level", self.level)


class CommandManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.commands = []

    def register(self, command):
        self.commands.append(command)

    def remove_cmd(self, content, cmd):
        """
        Remove command prefix
        """
        content = re.sub(r"^" + cmd + r"[:：\s]*", "", content, flags=re.IGNORECASE)
        content = content.strip()
        if re.match(r"^[,，。]", content):
            content = re.sub(r"^[,，。]", "", content)
        return content.strip()

    def find_cmd(self, uid, content):
        for command in self.commands:  # Exact match
            for keyword in command.cmd_list:
                if content.lower() == keyword.lower():  # Exact match
                    return [keyword]
        ret = []
        for command in self.commands:
            for keyword in command.cmd_list:
                if keyword.lower().find(content.lower()) >= 0:
                    ret.append(keyword)
                    break
        if len(ret) > 0:
            return ret
        cmd, content_adj = self.match_command(uid, content)
        if cmd is not None:
            return [cmd]
        return ret

    def match_command(self, uid, text):
        keys = [cmd.cmd_list[0] for cmd in self.commands]
        # text Take the first 20 characters
        if len(text) > 20:
            text = text[:20] + "..."
        cmd_list = ",".join(keys)
        demo = '{"cmd":"find record", "keyword":"keyword"}'
        question = f"""If the user enters '{text}',
he might be trying to input which command, choose from: '{cmd_list}';
when a command is confirmed, reply with the JSON string format 'command' and 'keyword': '{demo}'
otherwise reply 'not a command', do not reply with other content."""
        ret, answer, detail = llm_query(uid, MSG_ROLE, question, "cmd", debug=True)
        if ret:
            try:
                dic = json.loads(answer)
                if "cmd" in dic and "keyword" in dic:
                    cmd = dic["cmd"]
                    if cmd in keys:
                        return cmd, dic["keyword"]
            except Exception as e:
                logger.warning(f"match_command failed {e}")
        return None, None

    def msg_do_command(self, args, match_cmd=False, debug=True):
        """
        Handle command execution
        """
        content = args["content"]
        content = re.sub(r"^\d+[\.\s]*", "", content)  # Strike out the first digit
        cmd = None
        content_adj = None
        # Split x by punctuation, spaces, etc.
        arr = re.split(r"[,，。!！?？\s]+", content)
        if len(arr) == 0:
            return False, {"type": "text", "content": _("command_not_found")}
        x = arr[0]
        method = None
        for command in self.commands:  # Exact match
            for keyword in command.cmd_list:
                if x.lower() == keyword.lower():  # Exact match
                    cmd = command.cmd_list[0]  # Back to the first command
                    content_adj = self.remove_cmd(content, keyword)
                    method = "full match"
                    break
            if cmd is not None:
                break
        if cmd is None:  # starts with a match
            for command in self.commands:
                for keyword in command.cmd_list:
                    if x.lower().startswith(keyword.lower()):
                        cmd = command.cmd_list[0]
                        content_adj = self.remove_cmd(content, keyword)
                        method = "start match"
                        break
                if cmd is not None:
                    break
        if cmd is None and match_cmd:
            cmd, content_adj = self.match_command(args["user_id"], content)
            if cmd is not None:
                method = "llm match"
        logger.debug(
            f"msg_do_command: {content} -> {cmd} {content_adj}, method: {method}"
        )
        if cmd is not None:
            args["content"] = content_adj
            for command in self.commands:
                if cmd in command.cmd_list:
                    return command.function(args)
        return False, {"type": "text", "content": _("command_not_found")}

    def check_conflict(self):
        """
        Check if there are command conflicts
        """
        keys = []
        for command in self.commands:
            for keyword in command.cmd_list:
                keyword = keyword.lower()
                for key in keys:
                    if key.startswith(keyword) or keyword.startswith(key):
                        logger.warning(
                            "Command conflict: {key} {keyword}".format(
                                key=key, keyword=keyword
                            )
                        )
                keys.append(keyword)
