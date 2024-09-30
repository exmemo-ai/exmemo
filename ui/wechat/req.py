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

class TokenManager:
    _instance = None
    
    @staticmethod
    def get_instance():
        if TokenManager._instance is None:
            TokenManager._instance = TokenManager()
        return TokenManager._instance
            
    def __init__(self) -> None:
        self.token_dict = {}
        
    def set(self, uid, user_id, password, token):
        self.token_dict[uid] = (token, user_id, password)
        
    def get_token(self, uid):
        if uid in self.token_dict:
            return self.token_dict[uid][0]
        return None
    
    def get_user_info(self, uid):
        if uid in self.token_dict:
            return self.token_dict[uid][1], self.token_dict[uid][2]
        return None, None
    
    def remove_token(self, uid):
        if uid in self.token_dict:
            info = self.token_dict[uid]
            self.token_dict[uid] = (None, info[1], info[2])
            
    def remove_user(self, uid):
        if uid in self.token_dict:
            del self.token_dict[uid]

def real_login(user_name, user_id, password):
    url = URL_ADDR + '/api/auth/login/'
    data = {'username':user_id, 'password':password}
    r = requests.post(url, data=data)
    if r.status_code == 200:
        TokenManager.get_instance().set(user_name, user_id, password, r.json()['token'])
        logger.info(f'login success')
        return True, '登录成功'
    else:
        logger.warning(f'login failed, status code {r.status_code}')
        if r.status_code == 401 or r.status_code == 400:
            return True, '用户名或密码错误，请重新登录'
        return True, f'登录失败, status code {r.status_code}'
   
def real_logout(user_name):
    url = URL_ADDR + '/api/auth/logout/'
    token = TokenManager.get_instance().get_token(user_name)
    try:        
        if token is not None:
            headers = {'Authorization': f'Token {token}'}
        else:
            headers = None
        TokenManager.get_instance().remove_user(user_name)        
        r = requests.post(url, headers=headers)
        if r.status_code == 200 or r.status_code == 204:
            return True, '登出成功'
        else:
            return True, f'登出失败, status code {r.status_code}'
    except Exception as e:
        logger.warning(f'logout {e}')
        return True, f'登出失败, {e}'            
    
def add_args(data, **kwargs):
    '''
    添加参数
    '''
    for k,v in kwargs.items():
        data[k] = v
        
    data['is_group'] = False
    if 'group_id' in kwargs and kwargs['group_id'] is not None:
        data['session_id'] = kwargs['group_id']
        data['is_group'] = True
    elif 'wechat_user_id' in kwargs and kwargs['wechat_user_id'] is not None:
        data['session_id'] = '_' + kwargs['wechat_user_id']
    else:
        data['session_id'] = '_unknown'
    
    return data

def decode_content_disposition(header_value):
    '''
    解码 Content-Disposition 头部，获取文件名
    '''
    decoded_header = decode_header(header_value)
    if decoded_header[0][1] is not None:  # 如果头部是 MIME 编码的
        decoded_string = decoded_header[0][0].decode(decoded_header[0][1])
    else:  # 如果头部不是 MIME 编码的
        decoded_string = decoded_header[0][0]
    logger.debug(f'decoded_string {decoded_string}')
    # 从解码后的头部获取文件名
    entries = decoded_string.split(';')
    for entry in entries:
        if 'filename' in entry:
            filename = entry.split('=')[1].strip().strip('"')  # 删除两边的空格和引号
            return filename
    return None

g_timer = None

def rm_timer():
    '''
    删除定时器
    '''
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

def parse_result(response, **kwargs):
    if response.status_code == 200:
        # 解析返回的内容
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
                    if 'info' in ret_info:
                        ret, info = parse_log_info(kwargs['wechat_user_id'], ret_info['info'])
                        if ret:
                            return True, False, {'type':'text', 'content':info}
                        if 'request_delay' in ret_info: # 长时操作，需要定时处理
                            delay = ret_info['request_delay']
                            logger.info(f'1. delay {delay} handle message')
                            rm_timer()
                            if delay != -1: # 设置 request_delay 为 -1 时删除定时器
                                g_timer = threading.Timer(delay, handle_message, kwargs=kwargs)
                                g_timer.start()
                        return True, False, {'type':'text', 'content':ret_info['info']}
                    return True, False, {'type':'text', 'content':'操作成功'}
                else:
                    return True, False, {'type':'text', 'content':ret_info['info']}
        else:
            logger.info(f'unsupport content type: {content_type}')
    elif response.status_code == 401:
        TokenManager.get_instance().remove_token(kwargs['wechat_user_id'])
        user_id, password = TokenManager.get_instance().get_user_info(kwargs['wechat_user_id'])
        if user_id is not None and password is not None:
            ret, info = real_login(kwargs['wechat_user_id'], user_id, password)
            if ret:
                return True, True, {'type':'text', 'content':'登录过期，正在重新登录...'}
            else:
                return True, False, {'type':'text', 'content':info}            
    else:
        logger.info(f'Failed to request, status code: {response.status_code}')
    return True, False, {'type':'text', 'content':'后端失败处理'}

def parse_data(string, rtype='text', **kwargs):
    '''
    解析数据
    '''
    ret = True
    retry = False
    token = TokenManager.get_instance().get_token(kwargs['wechat_user_id'])
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
            ret, retry, info = parse_result(r, **kwargs)
        else:
            text = string.strip()
            if len(text) > 0:
                data['content'] = text
                data = add_args(data, **kwargs)
                r = requests.post(url, data=data, headers=headers)
                ret, retry, info = parse_result(r, **kwargs)
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
    处理定时
    '''
    logger.debug('handle time message')
    rm_timer()
    ret, dic = parse_data('获取音频', **kwargs) # 此处暂时只支持获取音频
    if 'TEST' not in os.environ:
        if 'e_context' in kwargs and dic['type'] == 'file': # 只在取到文件后才反馈用户
            _send_info(kwargs['e_context'], dic)

# 判断是否设置了测试标记 TEST
if 'TEST' not in os.environ:
    def _send_info(e_context: EventContext, detail: dict):
        '''
        发送消息，不在主循环中处理
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

