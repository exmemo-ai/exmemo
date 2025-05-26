from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from celery.result import AsyncResult
from celery.app.control import Control

from backend.common.user.utils import get_user_id
from .models import UserTask
from .serializers import UserTaskSerializer

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserTaskViewSet(viewsets.ModelViewSet):
    serializer_class = UserTaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        return UserTask.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def running_tasks(self, request):
        user_id = get_user_id(request)
        tasks = UserTask.objects.filter(user_id=user_id).order_by('-created_time')
        
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.serializer_class(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def task_status(self, request, pk=None):
        try:
            user_id = get_user_id(request)
            task = UserTask.objects.get(task_id=pk, user_id=user_id)
            celery_result = AsyncResult(task.task_id)
            
            if celery_result.status != task.status:
                task.status = celery_result.status
                if celery_result.ready():
                    task.result = celery_result.result if celery_result.successful() else {'error': str(celery_result.result)}
                task.save()
                
            return Response(self.serializer_class(task).data)
        except UserTask.DoesNotExist:
            return Response(
                {'error': 'Task not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        try:
            user_id = get_user_id(request)
            task = UserTask.objects.get(task_id=pk, user_id=user_id)
            app = AsyncResult(task.task_id).app
            Control(app).revoke(task.task_id, terminate=True)
            task.status = 'REVOKED'
            task.save()
            return Response({'message': 'Task terminated successfully'})
        except UserTask.DoesNotExist:
            return Response(
                {'error': 'Task not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['delete'])
    def delete_task(self, request, pk=None):
        try:
            user_id = get_user_id(request)
            task = UserTask.objects.get(task_id=pk, user_id=user_id)
            task.delete()
            return Response({'message': 'Task deleted successfully'})
        except UserTask.DoesNotExist:
            return Response(
                {'error': 'Task not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['delete'])
    def delete_completed_tasks(self, request):
        try:
            user_id = get_user_id(request)
            completed_tasks = UserTask.objects.filter(
                user_id=user_id, 
                status__in=['SUCCESS', 'FAILURE', 'REVOKED']
            )
            
            deleted_count = completed_tasks.count()
            completed_tasks.delete()
            return Response({
                'message': f'Successfully deleted {deleted_count} completed tasks'
            })
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
