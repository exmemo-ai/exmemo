import os
from loguru import logger
import pytz
from django.utils import timezone
from django.utils.translation import gettext as _

from backend.common.files import utils_filemanager, filecache
from backend.common.utils.file_tools import get_ext
from backend.common.parser import converter
from .models import StoreEntry
from .entry import delete_entry, add_data, REL_DIR_FILES, REL_DIR_NOTES
from .zipfile import is_compressed_file, uncompress_file
from .entry_item import EntryItem

def update_file(dic, addr, file_path, md5, vault, is_unzip, is_createSubDir, progress_callback=None, task_id=None):
    if addr.startswith("/"):
        addr = addr[1:]
    dic_item = dic.copy()
    if vault is not None:
        dic_item["addr"] = os.path.join(vault, addr)
    else:
        dic_item["addr"] = addr
    dic_item["md5"] = md5

    if is_unzip and is_compressed_file(file_path):
        return uncompress_file(dic_item, file_path, is_createSubDir, progress_callback, task_id)
    else:
        return add_data(dic_item, {"path":file_path})

        
def update_files(file_paths, filepaths, filemd5s, dic, vault, is_unzip, is_createSubDir, 
                 progress_callback=None, task_id=None):
    debug = False
    success_list = []
    if len(file_paths) > 0 and len(filemd5s) == 0:
        filemd5s = [None] * len(file_paths)

    total = len(file_paths)
    emb_status = "success" 
    for idx, (file_path, addr, md5) in enumerate(zip(file_paths, filepaths, filemd5s)):
        logger.info(f"update_files idx:{idx}, path:{file_path}, addr:{addr}, md5:{md5}")
        if len(file_paths) == 1:
            ret, ret_emb, detail = update_file(dic, addr, file_path, md5, vault, is_unzip, is_createSubDir, 
                                           progress_callback, task_id) # for single file, such as: zip
        else:
            ret, ret_emb, detail = update_file(dic, addr, file_path, md5, vault, is_unzip, is_createSubDir)
        if not ret_emb:
            emb_status = "failed"
        if ret:
            success_list.append(addr)
        if progress_callback:
            progress_callback((idx + 1) * 100 / total, task_id)    
    if debug:
        logger.info(f"upload_files success {str(success_list)[:200]}")

    return success_list, emb_status

def real_import(user_id, process_list, progress_callback=None, task_id=None, debug=False):
    success_list = []
    try:
        total = len(process_list)
        for idx, (base_src_path, dst_path, need_delete) in enumerate(process_list):
            if need_delete:
                delete_entry(user_id, [{"addr": dst_path, "etype": "note"}])
            
            src_ext = get_ext(base_src_path) 
            src_path = filecache.get_tmpfile(src_ext)
            ret = utils_filemanager.get_file_manager().get_file(
                user_id, base_src_path, src_path
            )
            if not ret:
                logger.warning(f"Failed to get source file: {base_src_path}")
                continue
            
            filecache.TmpFileManager.get_instance().add_file(src_path)
            
            md_path = filecache.get_tmpfile('.md')
            ret = converter.convert(src_path, md_path)
            if not ret:
                logger.warning(f"Failed to convert file: {base_src_path}")
                continue

            if debug: logger.info(f"## convert file {src_path} to {md_path}")

            dic = {
                "user_id": user_id,
                "etype": "note", 
                "addr": dst_path,
                "title": os.path.basename(dst_path),
            }
            ret, ret_emb, info = add_data(dic, {"path":md_path})
            if ret:
                success_list.append(dst_path)
            if progress_callback:
                progress_callback((idx + 1) * 100 / total, task_id)
        return success_list
    except Exception as e:
        logger.error(f"Error during import: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
def real_refresh(user_id, addr, etype, is_folder, progress_callback=None, task_id=None, debug=False):
    if not is_folder:
        entries = StoreEntry.objects.filter(user_id=user_id, idx=addr, etype=etype, block_id=0, is_deleted=False)
    else:
        if not addr.endswith("/"):
            addr = addr + "/"
        if etype == 'web':
            entries = StoreEntry.objects.filter(user_id=user_id, path__startswith=addr,
                          etype=etype, block_id=0, is_deleted=False)
        else:
            entries = StoreEntry.objects.filter(user_id=user_id, addr__startswith=addr,
                          etype=etype, block_id=0, is_deleted=False)
    success_list = []
    if entries.count() == 0:
        logger.warning(f"real_refresh {user_id} {addr} etype:{etype}, is_folder:{is_folder}, entries {len(entries)}")
        return success_list
    for i, entry in enumerate(entries):
        entry = EntryItem.from_model(entry)
        if etype == "file" or etype == "note":
            ext = get_ext(entry.path)
            file_path = filecache.get_tmpfile(ext)
            ret = utils_filemanager.get_file_manager().get_file(
                user_id, entry.path, file_path
            )
            if not ret:
                logger.warning(f"Failed to get file: {entry.path}")
                continue
            filecache.TmpFileManager.get_instance().add_file(file_path)
            ret, ret_emb, detail = add_data(entry, {"path":file_path if (etype == "file" or etype == "note") else None})
        else:
            ret, ret_emb, detail = add_data(entry)
        if ret:
            success_list.append(entry.addr)
        if progress_callback:
            progress_callback((i + 1) * 100 / len(entries), task_id)

    return success_list

def rename_file(uid, oldaddr, newaddr, dic, debug=False):
    if debug:
        logger.debug(f'rename_file {uid} {oldaddr} to {newaddr}')
    if dic['etype'] == 'file':
        oldpath = os.path.join(REL_DIR_FILES, oldaddr)
        newpath = os.path.join(REL_DIR_FILES, newaddr)
    elif dic['etype'] == 'note':
        oldpath = os.path.join(REL_DIR_NOTES, oldaddr)
        newpath = os.path.join(REL_DIR_NOTES, newaddr)
    else:
        return False
    ret = utils_filemanager.get_file_manager().rename_file(uid, oldpath, newpath)
    if ret:
        StoreEntry.objects.filter(user_id=uid, addr=oldaddr, etype=dic['etype']).update(addr=newaddr, path=newpath, 
                                  updated_time = timezone.now().astimezone(pytz.UTC))
        return True
    return False

def real_delete(user_id, path, etype, is_folder, progress_callback=None, task_id=None):
    success_list = []
    try:
        if not is_folder:
            entries = StoreEntry.objects.filter(user_id=user_id, addr=path, etype=etype, block_id=0)
            if not entries:
                normalized_path = path.replace('\\', '/').replace('//', '/')
                entries = StoreEntry.objects.filter(user_id=user_id, addr=normalized_path, etype=etype, block_id=0)
        else:
            dirname = path if path.endswith('/') else path + '/'
            entries = StoreEntry.objects.filter(user_id=user_id, etype=etype, addr__startswith=dirname, block_id=0)
            
        if entries.count() == 0:
            logger.warning(f"real_delete {user_id} {path} etype:{etype}, is_folder:{is_folder}")
            return success_list

        for i, entry in enumerate(entries):
            delete_entry(user_id, [{"addr": entry.addr, "etype": etype}])
            success_list.append(entry.addr)
            if progress_callback:
                progress_callback((i + 1) * 100 / len(entries), task_id)
                
        return success_list
    except Exception as e:
        logger.error(f"Error during delete: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def real_move(user_id, source, target, etype, is_folder, progress_callback=None, task_id=None):
    success_list = []
    try:
        if not is_folder:
            entry = StoreEntry.objects.filter(user_id=user_id, addr=source, etype=etype, block_id=0).first()
            if not entry:
                normalized_source = source.replace('\\', '/').replace('//', '/')
                entry = StoreEntry.objects.filter(user_id=user_id, addr=normalized_source, etype=etype, block_id=0).first()
            if entry:
                dic = entry.__dict__.copy()
                ret = rename_file(user_id, entry.addr, target, dic)
                if ret:
                    success_list.append(target)
        else:
            dirname = source if source.endswith('/') else source + '/'
            entries = StoreEntry.objects.filter(user_id=user_id, etype=etype, addr__startswith=dirname, block_id=0)
            
            total = len(entries)
            for i, entry in enumerate(entries):
                rel_path = entry.addr[len(dirname):]
                new_dst = os.path.join(target, rel_path)
                dic = entry.__dict__.copy()
                ret = rename_file(user_id, entry.addr, new_dst, dic)
                if ret:
                    success_list.append(new_dst)
                if progress_callback:
                    progress_callback((i + 1) * 100 / total, task_id)

        return success_list
    except Exception as e:
        logger.error(f"Error during move: {str(e)}")
        import traceback
        traceback.print_exc()
        return None