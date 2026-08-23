from pathlib import Path

from django.apps import apps as django_apps
from django.http import FileResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from common.views import BaseModelViewSet
from common.response import success_response, error_response

from .models import ApprovalRequest, OperationLog, BackupRecord
from .serializers import (
    ApprovalRequestSerializer, OperationLogSerializer, BackupRecordSerializer,
)
from .permissions import AdminOnlyPermission
from .services import perform_backup

# 审批目标模型 → (app_label, ModelName)，get_model 避免跨 app 循环导入
TARGET_APP_MODEL = {
    'FactoryPayment': ('factory_payment', 'FactoryPayment'),
    'FactoryPaymentRecord': ('factory_payment', 'FactoryPaymentRecord'),
    'Order': ('orders', 'Order'),
    'Logistics': ('logistics', 'Logistics'),
}


class ApprovalRequestViewSet(BaseModelViewSet):
    """审批申请：列表/审批处理仅 admin（AdminOnlyPermission）。"""

    serializer_class = ApprovalRequestSerializer
    permission_classes = [IsAuthenticated, AdminOnlyPermission]
    filterset_fields = ['approval_type', 'status']
    ordering = ['-created_at']
    http_method_names = ['get', 'post']

    def get_queryset(self):
        return ApprovalRequest.objects.select_related('submitted_by', 'reviewed_by')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        ar = self.get_object()
        if ar.status != 'pending':
            return error_response(1009, '该申请已处理，不可重复操作', status=400)
        app_model = TARGET_APP_MODEL.get(ar.target_model)
        if app_model:
            model_cls = django_apps.get_model(*app_model)
            try:
                target = model_cls.objects.get(pk=ar.target_id)
            except model_cls.DoesNotExist:
                return error_response(1004, f'目标对象已不存在（{ar.target_model}#{ar.target_id}）', status=404)
            target.is_approved = True
            target.save(update_fields=['is_approved'])
        ar.status = 'approved'
        ar.reviewed_by = request.user
        ar.save(update_fields=['status', 'reviewed_by', 'updated_at'])
        # 审批通过自动备份（失败不影响审批结果）
        try:
            perform_backup('approval')
        except Exception:
            pass
        return success_response(self.get_serializer(ar).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        ar = self.get_object()
        if ar.status != 'pending':
            return error_response(1009, '该申请已处理，不可重复操作', status=400)
        ar.status = 'rejected'
        ar.reviewed_by = request.user
        note = request.data.get('note')
        if note:
            ar.note = note
        ar.save(update_fields=['status', 'reviewed_by', 'note', 'updated_at'])
        return success_response(self.get_serializer(ar).data)


class OperationLogViewSet(BaseModelViewSet):
    """操作日志查询：仅 admin 只读。"""

    serializer_class = OperationLogSerializer
    permission_classes = [IsAuthenticated, AdminOnlyPermission]
    filterset_fields = ['action', 'user']
    search_fields = ['path', 'user__username']
    ordering = ['-created_at']
    http_method_names = ['get']

    def get_queryset(self):
        qs = OperationLog.objects.select_related('user')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)
        return qs


class BackupViewSet(BaseModelViewSet):
    """备份管理：列表 / 手动备份 / 下载，均仅 admin。"""

    serializer_class = BackupRecordSerializer
    permission_classes = [IsAuthenticated, AdminOnlyPermission]
    ordering = ['-created_at']
    http_method_names = ['get', 'post']

    def get_queryset(self):
        return BackupRecord.objects.all()

    @action(detail=False, methods=['post'], url_path='manual-backup')
    def manual_backup(self, request):
        br = perform_backup('manual')
        if br is None:
            return error_response(1010, '当前数据库不支持自动备份（仅 SQLite）', status=400)
        return success_response(self.get_serializer(br).data, status=201)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        br = self.get_object()
        p = Path(br.file_path)
        if not p.exists():
            return error_response(1004, '备份文件不存在或已被清理', status=404)
        return FileResponse(open(p, 'rb'), as_attachment=True, filename=p.name)
