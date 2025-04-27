import os
import zipfile
import tempfile
import py7zr
import patoolib
from loguru import logger
from backend.common.utils.file_tools import get_ext
from .feature import EntryFeatureTool
from .entry import add_data

def is_compressed_file(path):
    """
    Check if the file is a compressed file
    """
    ext = get_ext(path).lower()
    return ext in ['.zip', '.rar']

def uncompress_file(dic_item, tmp_path, is_createSubDir, progress_callback=None, task_id=None, debug=False):
    try:
        base_dir = os.path.dirname(dic_item["addr"])
        filename = os.path.splitext(os.path.basename(dic_item["addr"]))[0]
        ext = get_ext(tmp_path).lower()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            if debug: logger.debug(f'tmp dir {temp_dir}')
            
            if ext == '.zip':
                with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            elif ext == '.7z':
                with py7zr.SevenZipFile(tmp_path, 'r') as sz_ref:
                    sz_ref.extractall(temp_dir)
            elif ext == '.rar':
                patoolib.extract_archive(tmp_path, outdir=temp_dir)
            
            ret_list = []
            if is_createSubDir:
                target_dir = os.path.join(base_dir, filename)
            else:
                target_dir = base_dir

            filename = os.path.basename(dic_item["addr"])
            total_files = sum([len(files) for _, _, files in os.walk(temp_dir)])
            processed_files = 0

            for root, _, files in os.walk(temp_dir):
                if debug: logger.debug(f"root {root} {files}")
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    new_addr = os.path.join(target_dir, rel_path)
                    if debug: logger.debug(f"file {new_addr}")
                    
                    new_dic = dic_item.copy()
                    new_dic["addr"] = new_addr
                    new_dic["title"] = file
                    if debug: logger.debug(f'dic {new_dic}')
                    ret, ret_emb, info = add_data(new_dic, {"path":file_path}, use_llm=False)
                    if ret:
                        ret_list.append({"addr": new_addr})
                    
                    processed_files += 1
                    if progress_callback:
                        progress = (processed_files * 100) // total_files
                        progress_callback(progress, task_id)
            
            if debug: logger.info(f'unzip list {ret_list}')
            return True, True, ret_list
    except Exception as e:
        logger.error(f"Error extracting compressed file: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, False, str(e)
