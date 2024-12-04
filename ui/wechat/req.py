import re
import json
import threading
import traceback
import requests
from email.header import decode_header

import os
if 'TEST' not in os.environ:
    from common.log import logger
    from plugins import *
    from bridge.reply import Reply, ReplyType
else:
    from loguru import logger

URL_ADDR = os.getenv('K_BACKEND_ADDR', 'http://192.168.10.166:8005')
TMP_AUDIO = '/tmp/tmp.mp3'
logger.info(f'backend addr {URL_ADDR}')

class User:
    def __init__(self, token, user_id, password):
        self.token = token
        self.user_id = user_id
        self.password = password
        self.session_dict = {}

    def set_sid(self, local_sid, remote_sid):
        self.session_dict[local_sid] = remote_sid

    def get_sid(self, local_sid):
        if local_sid in self.session_dict:
            return self.session_dict[local_sid]
        return ""

class UserManager:
    _instance = None
    
    @staticmethod
    def get_instance():
        if UserManager._instance is None:
            UserManager._instance = UserManager()
        return UserManager._instance

    def __init__(self) -> None:
        self.user_dict = {}

    def set(self, uid, user_id, password, token):
        self.user_dict[uid] = User(token, user_id, password)

    def get_token(self, uid):
        if uid in self.user_dict:
            return self.user_dict[uid].token
        return None
    
    def get_sid(self, uid, local_id):
        if uid in self.user_dict:
            return self.user_dict[uid].get_sid(local_id)
        return ""

    def get_user(self, uid):
        if uid in self.user_dict:
            return self.user_dict[uid]
        return None
    
    def remove_token(self, uid):
        if uid in self.user_dict:
            self.user_dict[uid].token = None

    def remove_user(self, uid):
        if uid in self.user_dict:
            del self.user_dict[uid]

def real_login(user_name, user_id, password):
    url = URL_ADDR + '/api/auth/login/'
    data = {'username':user_id, 'password':password}
    r = requests.post(url, data=data)
    if r.status_code == 200:
        UserManager.get_instance().set(user_name, user_id, password, r.json()['token'])
        logger.info(f'login success')
        return True, '登录成功'
    else:
        logger.warning(f'login failed, status code {r.status_code}')
        if r.status_code == 401 or r.status_code == 400:
            return True, '用户名或密码错误，请重新登录'
        return True, f'登录失败, status code {r.status_code}'
   
def real_logout(user_name):
    url = URL_ADDR + '/api/auth/logout/'
    token = UserManager.get_instance().get_token(user_name)
    try:        
        if token is not None:
            headers = {'Authorization': f'Token {token}'}
        else:
            headers = None
        UserManager.get_instance().remove_user(user_name)        
        r = requests.post(url, headers=headers)
        if r.status_code == 200 or r.status_code == 204:
            return True, '登出成功'
        else:
            return True, f'登出失败, status code {r.status_code}'
    except Exception as e:
        logger.warning(f'logout {e}')
        return True, f'登出失败, {e}'            
    
def add_args(data, **kwargs):
    for k,v in kwargs.items():
        data[k] = v
        
    data['is_group'] = False
    if 'group_id' in kwargs and kwargs['group_id'] is not None:
        data['local_sid'] = kwargs['group_id']
        data['is_group'] = True
    elif 'wechat_user_id' in kwargs and kwargs['wechat_user_id'] is not None:
        data['local_sid'] = '_' + kwargs['wechat_user_id']
    else:
        data['local_sid'] = '_unknown'
    data['sid'] = UserManager.get_instance().get_sid(kwargs['wechat_user_id'], data['local_sid'])
    return data

def decode_content_disposition(header_value):
    '''
    Decode Content-Disposition header，get filename
    '''
    decoded_header = decode_header(header_value)
    if decoded_header[0][1] is not None:  #  Check MIME encode
        decoded_string = decoded_header[0][0].decode(decoded_header[0][1])
    else:
        decoded_string = decoded_header[0][0]
    logger.debug(f'decoded_string {decoded_string}')
    entries = decoded_string.split(';')
    for entry in entries:
        if 'filename' in entry:
            filename = entry.split('=')[1].strip().strip('"')
            return filename
    return None

g_timer = None

def rm_timer():
    global g_timer
    if g_timer is not None:
        try:
            g_timer.cancel()
        except Exception as e:
            logger.warning(f'rm_timer {e}')
        g_timer = None

def parse_log_info(user_name, info):
    try:
        if isinstance(info, str):
            match = re.search(r'{.*}', info)
            if match is not None:
                info = match.group()
            dic = json.loads(info)
        elif isinstance(info, dict):
            dic = info
        else:
            return False, f'not support info type {type(info)}'
        if 'user_id' in dic and 'password' in dic:
            return real_login(user_name, dic['user_id'], dic['password'])
        if 'logout' in dic:
            return real_logout(user_name)
    except Exception as e:
        logger.error(f'login {e}')
        return False, str(e)
    return False, None

def parse_result(response, data, **kwargs):
    if response.status_code == 200:
        user_id = kwargs['wechat_user_id']
        content_type = response.headers['Content-Type']
        logger.info(f'content_type {content_type}')
        if 'audio' in content_type or 'octet-stream' in content_type:
            content_disposition = response.headers.get('Content-Disposition')
            logger.info(f'content_disposition {content_disposition}')
            filename = decode_content_disposition(content_disposition)
            logger.info(f'recv file {filename}')
            if filename is None:
                filename = TMP_AUDIO
            else:
                filename = '/tmp/' + filename
            with open(filename, 'wb') as f:
                f.write(response.content)
            return True, False, {'type':'file', 'content':filename}
        elif 'text' in content_type:
            ret_info = json.loads(response.text)
            logger.info(f'backend, ret {ret_info}')
            if 'status' in ret_info:
                if ret_info['status'] == 'success':
                    if 'type' in ret_info and ret_info['type'] == 'json' and 'content' in ret_info:
                        if 'sid' in ret_info['content']:
                            user = UserManager.get_instance().get_user(user_id)
                            if user is not None:
                                user.set_sid(data['local_sid'], ret_info['content']['sid'])
                        return True, False, {'type':'text', 'content':ret_info['content']['info']}
                    elif 'info' in ret_info:
                        ret, info = parse_log_info(user_id, ret_info['info'])
                        if ret:
                            return True, False, {'type':'text', 'content':info}
                        if 'request_delay' in ret_info:
                            delay = ret_info['request_delay']
                            logger.info(f'1. delay {delay} handle message')
                            rm_timer()
                            if delay != -1:
                                g_timer = threading.Timer(delay, handle_message, kwargs=kwargs)
                                g_timer.start()
                        return True, False, {'type':'text', 'content':ret_info['info']}
                    return True, False, {'type':'text', 'content':'操作成功'}
                else:
                    return True, False, {'type':'text', 'content':ret_info['info']}
        else:
            logger.info(f'unsupport content type: {content_type}')
    elif response.status_code == 401:
        UserManager.get_instance().remove_token(user_id)
        user:User = UserManager.get_instance().get_user(user_id)
        if user is not None:
            ret, info = real_login(user_id, user.user_id, user.password)
            if ret:
                return True, True, {'type':'text', 'content':'登录过期，正在重新登录...'}
            else:
                return True, False, {'type':'text', 'content':info}            
    else:
        logger.info(f'Failed to request, status code: {response.status_code}')
    return True, False, {'type':'text', 'content':'后端失败处理'}

def parse_data(string, rtype='text', **kwargs):
    ret = True
    retry = False
    token = UserManager.get_instance().get_token(kwargs['wechat_user_id'])
    logger.info(f'parse DATA {string}, rtype {rtype}, has token {token is not None}')
    try:        
        if token is not None:
            headers = {'Authorization': f'Token {token}'}
        else:
            headers = None
        url = URL_ADDR + '/api/message/'
        data = {'rtype':rtype}            
        if rtype == 'file':
            filename = os.path.basename(string)
            files = {filename: open(string, 'rb')}            
            data = add_args(data, **kwargs)
            r = requests.post(url, files=files, data=data, headers=headers)
            logger.info(f'upload file {data} ret {r.text}')
            ret, retry, info = parse_result(r, data, **kwargs)
        else:
            text = string.strip()
            if len(text) > 0:
                data['content'] = text
                data = add_args(data, **kwargs)
                r = requests.post(url, data=data, headers=headers)
                ret, retry, info = parse_result(r, data, **kwargs)
            else:
                info = {'type':'text', 'content':'内容不能为空'}
    except Exception as e:
        logger.warning(f'error {e}')
        traceback.print_exc()
        info = {'type':'text', 'content':'后端操作失败'}
    if retry:
        return parse_data(string, rtype, **kwargs)
    return ret, info       

def handle_message(**kwargs):
    '''
    Receive audio
    '''
    logger.debug('handle time message')
    rm_timer()
    ret, dic = parse_data('获取音频', **kwargs)
    if 'TEST' not in os.environ:
        if 'e_context' in kwargs and dic['type'] == 'file':
            _send_info(kwargs['e_context'], dic)

if 'TEST' not in os.environ:
    def _send_info(e_context: EventContext, detail: dict):
        '''
        Send_info, not in main loop
        '''
        logger.debug(f'_send_info {detail}')
        reply = Reply()
        if detail['type'] == 'file':
            reply.type = ReplyType.FILE
        elif detail['type'] == 'text':
            reply.type = ReplyType.TEXT
        reply.content = detail['content']
        channel = e_context["channel"]
        channel.send(reply, e_context["context"])

