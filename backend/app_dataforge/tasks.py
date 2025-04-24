from celery import shared_task
from loguru import logger
from user_tasks.models import UserTask
from .file_tools import real_import, update_files, real_refresh

def update_progress(progress, task_id):
    task = UserTask.objects.get(task_id=task_id)
    task.progress = progress
    #logger.info(f"Task {task_id} progress: {progress}")
    task.save()

@shared_task(bind=True)
def update_files_task(self, user_id, tmp_file_paths, filepaths, filemd5s, dic, vault, is_unzip, is_createSubDir):
    logger.info(f"Task {self.request.id} started with args: {user_id}, {tmp_file_paths}, {filepaths}, {filemd5s}, {dic}, {vault}, {is_unzip}, {is_createSubDir}")
    if user_id:
        UserTask.objects.create(
            user_id=user_id,
            task_id=self.request.id,
            status='PENDING',
            task_name='update_files_task',
        )
    try:
        success_list, emb_status = update_files(
            tmp_file_paths, filepaths, filemd5s, dic, vault, 
            is_unzip, is_createSubDir, 
            progress_callback=update_progress,
            task_id =self.request.id
        )
        if len(success_list) > 0:
            task = UserTask.objects.get(task_id=self.request.id)
            task.status = 'SUCCESS'
            task.result = {'success_list': success_list, 'emb_status': emb_status}
            task.save()
        else:
            task = UserTask.objects.get(task_id=self.request.id)
            task.status = 'FAILURE'
            task.result = {'error': 'No files updated'}
            task.save()
        return success_list
    except Exception as e:
        if user_id:
            task = UserTask.objects.get(task_id=self.request.id)
            task.status = 'FAILURE'
            task.result = {'error': str(e)}
            task.save()
        raise

@shared_task(bind=True)
def import_task(self, user_id, process_list, debug=False):
    logger.info(f"Task {self.request.id} started with args: {user_id}, {str(process_list)[:200]}")
    if user_id:
        UserTask.objects.create(
            user_id=user_id,
            task_id=self.request.id,
            status='PENDING',
            task_name='import_task',
        )
    try:
        success_list = real_import(
            user_id, process_list,
            progress_callback=update_progress,
            task_id = self.request.id,
        )
        if success_list is not None:
            task = UserTask.objects.get(task_id=self.request.id)
            task.status = 'SUCCESS' 
            task.result = {'success_list': success_list}
            task.save()
        else:
            task = UserTask.objects.get(task_id=self.request.id)
            task.status = 'FAILURE'
            task.result = {'error': 'Import failed'}
            task.save()            
        return success_list
    except Exception as e:
        if user_id:
            task = UserTask.objects.get(task_id=self.request.id)
            task.status = 'FAILURE'
            task.result = {'error': str(e)}
            task.save()
        raise

@shared_task(bind=True)
def refresh_task(self, user_id, addr, etype, is_folder):
    logger.info(f"Task {self.request.id} started with args: {user_id}, {addr}, {etype}, {is_folder}")
    if user_id:
        UserTask.objects.create(
            user_id=user_id,
            task_id=self.request.id,
            status='PENDING',
            task_name='refresh_task',
        )
    try:
        success_list = real_refresh(
            user_id, addr, etype, is_folder,
            progress_callback=update_progress,
            task_id = self.request.id,
        )
        if success_list is not None:
            task = UserTask.objects.get(task_id=self.request.id)
            task.status = 'SUCCESS' 
            task.result = {'success_list': success_list}
            task.save()
        else:
            task = UserTask.objects.get(task_id=self.request.id)
            task.status = 'FAILURE'
            task.result = {'error': 'Refresh failed'}
            task.save()            
        return success_list
    except Exception as e:
        if user_id:
            task = UserTask.objects.get(task_id=self.request.id)
            task.status = 'FAILURE'
            task.result = {'error': str(e)}
            task.save()
        raise