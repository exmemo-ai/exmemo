
from celery import shared_task
from django.utils import timezone
from .weight_utils import BookmarkWeightCalculator
from app_dataforge.models import StoreEntry, BookmarkClick
from ..app_bm_keeper.cache_manager import BookmarkCacheManager

@shared_task
def update_all_bookmark_weights():
    """定期更新所有书签权重的Celery任务"""
    current_time = timezone.now()
    bookmarks = StoreEntry.objects.filter(
        source='web_chrome_bm',
        is_deleted=False
    )
    
    results = {
        'total': bookmarks.count(),
        'updated': 0,
        'errors': 0
    }
    
    for bookmark in bookmarks:
        try:
            # 计算新权重
            calculator = BookmarkWeightCalculator(bookmark, current_time)
            new_weight = calculator.calculate_total_weight()
            
            # 更新数据库
            bookmark.weight = new_weight
            bookmark.save(update_fields=['weight'])
            
            # 更新缓存
            BookmarkCacheManager.set_weight(bookmark.id, new_weight)
            
            results['updated'] += 1
            
        except Exception as e:
            results['errors'] += 1
            
    return results

# 批量更新函数，可用于手动触发
def batch_update_weights(batch_size=100):
    """批量更新书签权重"""
    bookmarks = StoreEntry.objects.filter(
        source='web_chrome_bm',
        is_deleted=False
    )
    
    for i in range(0, bookmarks.count(), batch_size):
        batch = bookmarks[i:i+batch_size]
        update_bookmark_weights.delay([b.id for b in batch])

@shared_task
def update_bookmark_weights(bookmark_ids):
    """处理单个批次的更新"""
    current_time = timezone.now()
    for bookmark_id in bookmark_ids:
        try:
            bookmark = StoreEntry.objects.get(id=bookmark_id)
            calculator = BookmarkWeightCalculator(bookmark, current_time)
            bookmark.weight = calculator.calculate_total_weight()
            bookmark.save(update_fields=['weight'])
        except Exception as e:
            continue