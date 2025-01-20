
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
import math

class BookmarkWeightCalculator:
    def __init__(self, bookmark, current_time=None):
        self.bookmark = bookmark
        self.current_time = current_time or timezone.now()
        
    def calculate_total_weight(self):
        """计算书签的综合权重"""
        weights = {
            'freshness': self._calculate_freshness_weight(),
            'clicks': self._calculate_clicks_weight(),
            'recent_activity': self._calculate_recent_activity_weight(),
            'continuous': self._calculate_continuous_clicks_weight()
        }
        
        coefficients = {
            'freshness': 0.3,       
            'clicks': 0.3,           
            'recent_activity': 0.2,  
            'continuous': 0.2       
        }

        total_weight = sum(
            weight * coefficients[factor] 
            for factor, weight in weights.items()
        )
        
        return round(total_weight, 3)
    
    def _calculate_freshness_weight(self):
        """计算新鲜度权重，考虑创建时间和最后点击时间"""
        days_since_creation = (self.current_time - self.bookmark.created_time).days
        
        last_click = (BookmarkClick.objects.filter(bookmark=self.bookmark)
                     .order_by('-meta__clicked_at')
                     .first())
        
        if last_click:
            last_click_time = timezone.datetime.fromisoformat(
                last_click.meta['clicked_at']
            )
            days_since_last_click = (self.current_time - last_click_time).days
        else:
            days_since_last_click = days_since_creation
            
        creation_weight = 1.0 / (1 + math.log1p(days_since_creation/30))
        last_click_weight = 1.0 / (1 + math.log1p(days_since_last_click/7))
        
        return (creation_weight * 0.4 + last_click_weight * 0.6)
    
    def _calculate_clicks_weight(self):
        """计算点击总量权重"""
        total_clicks = BookmarkClick.objects.filter(
            bookmark=self.bookmark
        ).count()
        

        return math.log1p(total_clicks)
    
    def _calculate_recent_activity_weight(self):
        """计算近期活跃度权重"""
        time_windows = {
            'day': self.current_time - timedelta(days=1),
            'week': self.current_time - timedelta(days=7),
            'month': self.current_time - timedelta(days=30)
        }
        
        click_counts = {}
        for period, start_time in time_windows.items():
            click_counts[period] = BookmarkClick.objects.filter(
                bookmark=self.bookmark,
                meta__clicked_at__gte=start_time.isoformat()
            ).count()
        
        window_weights = {
            'day': 0.5,
            'week': 0.3,
            'month': 0.2
        }
        
        activity_score = sum(
            count * window_weights[period] 
            for period, count in click_counts.items()
        )
        
        return math.log1p(activity_score)
    
    def _calculate_continuous_clicks_weight(self):
        """计算连续点击权重"""
        recent_clicks = BookmarkClick.objects.filter(
            bookmark=self.bookmark,
            meta__clicked_at__gte=(self.current_time - timedelta(hours=24)).isoformat()
        ).order_by('meta__clicked_at')
        
        if not recent_clicks:
            return 0
            
        click_times = [
            timezone.datetime.fromisoformat(click.meta['clicked_at']) 
            for click in recent_clicks
        ]
        
        continuous_score = 0
        for i in range(1, len(click_times)):
            time_diff = (click_times[i] - click_times[i-1]).total_seconds() / 3600  # 转换为小时
            if time_diff <= 1:  
                continuous_score += 1.0
            elif time_diff <= 4:  
                continuous_score += 0.5
                
        return math.log1p(continuous_score)