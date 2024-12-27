
from django.core.cache import cache
from django.conf import settings

class BookmarkCacheManager:
    CACHE_TTL = 3600  # 缓存1小时
    
    @staticmethod
    def get_cache_key(bookmark_id, suffix=''):
        return f'bookmark:{bookmark_id}:{suffix}'
    
    @classmethod
    def get_weight(cls, bookmark_id):
        """获取缓存的权重"""
        return cache.get(cls.get_cache_key(bookmark_id, 'weight'))
        
    @classmethod
    def set_weight(cls, bookmark_id, weight):
        """设置权重缓存"""
        cache.set(cls.get_cache_key(bookmark_id, 'weight'), weight, cls.CACHE_TTL)
        
    @classmethod
    def get_click_stats(cls, bookmark_id):
        """获取缓存的点击统计"""
        return cache.get(cls.get_cache_key(bookmark_id, 'clicks'))
    
    @classmethod
    def set_click_stats(cls, bookmark_id, stats):
        """设置点击统计缓存"""
        cache.set(cls.get_cache_key(bookmark_id, 'clicks'), stats, cls.CACHE_TTL)
        
    @classmethod
    def invalidate_cache(cls, bookmark_id):
        """清除指定书签的所有缓存"""
        cache.delete_many([
            cls.get_cache_key(bookmark_id, 'weight'),
            cls.get_cache_key(bookmark_id, 'clicks')
        ])