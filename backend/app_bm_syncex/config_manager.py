# ======= 前端llm&截断配置项接收，暂时注释 =======
# import os
# import json
# from pathlib import Path
# from loguru import logger
# from dotenv import load_dotenv

# class BookmarkConfigManager:
#     def __init__(self, data_dir='/data/bookmark_config'):
#         self.data_dir = Path(data_dir)
#         try:
#             self.data_dir.mkdir(parents=True, exist_ok=True)
#             logger.info(f"Config directory initialized: {self.data_dir}")
#         except Exception as e:
#             logger.error(f"Failed to create config directory {self.data_dir}: {e}")
#             self.data_dir = Path("/tmp/bookmark_config")
#             self.data_dir.mkdir(parents=True, exist_ok=True)
#         load_dotenv()
        
#     def _get_config_path(self, username):
#         """获取用户配置文件路径"""
#         config_path = self.data_dir / f"{username}_config.json"
#         logger.debug(f"Config path for {username}: {config_path}")
#         return config_path
        
#     def get_default_config(self):
#         """从环境变量获取默认配置"""
#         default_config = {
#             'extract_content': os.getenv('BOOKMARK_EXTRACT_CONTENT', 'False').lower() == 'true',
#             'llm_api_key': os.getenv('OPENAI_API_KEY', ''),
#             'llm_base_url': os.getenv('OPENAI_API_BASE_URL', 'https://api.openai.com/v1'),
#             'llm_model': os.getenv('DEFAULT_TOOL_LLM', 'gpt-4o-mini'),
#             'truncate_content': True,
#             'max_content_length': int(os.getenv('MAX_CONTENT_LENGTH', '1000')),
#             'truncate_mode': 'start',
#             'auto_tag': True
#         }
#         logger.debug(f"Default config: {default_config}")
#         return default_config
        
#     def load_config(self, username):
#         """加载用户配置,不存在则返回默认配置"""
#         config_path = self._get_config_path(username)
#         try:
#             if config_path.exists():
#                 with open(config_path, 'r', encoding='utf-8') as f:
#                     config = json.load(f)
#                     logger.info(f"Loaded config for {username} from {config_path}")
#                     return config
#         except Exception as e:
#             logger.error(f"Error loading config for {username}: {e}")
            
#         # 如果文件不存在或加载失败,返回默认配置
#         default_config = self.get_default_config()
#         self.save_config(username, default_config)  # 保存默认配置
#         return default_config
        
#     def save_config(self, username, config):
#         """保存用户配置"""
#         config_path = self._get_config_path(username)
#         try:
#             # 打印保存路径和数据
#             logger.info(f"Saving config to: {config_path}")
#             logger.info(f"Config data to save: {config}")
            
#             with open(config_path, 'w', encoding='utf-8') as f:
#                 json.dump(config, f, indent=2, ensure_ascii=False)
            
#             # 立即读取验证
#             with open(config_path, 'r', encoding='utf-8') as f:
#                 saved_config = json.load(f)
#                 logger.info(f"Verified saved config: {saved_config}")
            
#             return True
#         except Exception as e:
#             logger.error(f"Error saving config for {username}: {e}")
#             return False
