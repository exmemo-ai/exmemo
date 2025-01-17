from .common import (
    make_error_response,
    save_bookmark_changes,
    PathManager
)

class BookmarkUpdateService:
    """Service class for handling bookmark updates"""
    
    def __init__(self, bookmark):
        self.bookmark = bookmark
        self.changed_fields = {}
        
    def update_title(self, new_title):
        """Update bookmark title and related fields"""
        if new_title and new_title != self.bookmark.title:
            self.changed_fields.update(
                PathManager.update_bookmark_on_title_change(self.bookmark, new_title)
            )
        return self
        
    def update_tags(self, new_tags):
        """Update bookmark tags"""
        if new_tags is not None and new_tags != self.bookmark.ctype:
            self.changed_fields['ctype'] = new_tags
        return self
        
    def update_url(self, new_url):
        """Update bookmark URL"""
        if new_url and new_url != self.bookmark.addr:
            self.changed_fields['addr'] = new_url
        return self
        
    def update_folder(self, new_folder, type='None'):
        """Update bookmark folder and optionally status"""
        if new_folder and new_folder != self.bookmark.path:
            if type == 'readlater':
                self.changed_fields['status'] = "collect"
                full_path = PathManager.format_path_readlater(new_folder, self.bookmark.title)
            else:
                full_path = new_folder
            self.changed_fields['path'] = full_path
        return self
        
    def save(self):
        """Save all changes and return response"""
        if not self.changed_fields:
            return make_error_response(400, "No fields to update")
            
        if 'path' in self.changed_fields:
            self.changed_fields = PathManager.update_bookmark_metapath(
                self.bookmark, 
                self.changed_fields
            )            
        return save_bookmark_changes(self.bookmark, self.changed_fields)
