# ======= 前端llm&截断配置项接收，暂时注释 =======

# from django.core.cache import cache
# from functools import lru_cache
# from .config_manager import BookmarkConfigManager

# class SimpleConfigService:
#     def __init__(self):
#         self.config_manager = BookmarkConfigManager()
    
#     @lru_cache(maxsize=100)  # 使用Python内置的LRU缓存，最多缓存100个用户的配置
#     def get_config(self, username):
#         """获取用户配置，使用装饰器自动缓存"""
#         return self.config_manager.load_config(username)
    
#     def update_config(self, username, config):
#         """更新配置并清除缓存"""
#         result = self.config_manager.save_config(username, config)
#         if result:
#             self.get_config.cache_clear()
#         return result

# # 全局单例
# config_service = SimpleConfigService()
