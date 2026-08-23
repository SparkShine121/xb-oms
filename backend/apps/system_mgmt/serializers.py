from rest_framework import serializers

from .models import ApprovalRequest, OperationLog, BackupRecord


class ApprovalRequestSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.CharField(source='submitted_by.username', read_only=True, default='')
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True, default='')

    class Meta:
        model = ApprovalRequest
        fields = ['id', 'approval_type', 'target_id', 'target_model', 'status',
                  'submitted_by', 'submitted_by_name', 'reviewed_by', 'reviewed_by_name',
                  'note', 'created_at', 'updated_at']
        read_only_fields = ['status', 'reviewed_by', 'created_at', 'updated_at']


class OperationLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='')

    class Meta:
        model = OperationLog
        fields = ['id', 'user', 'username', 'action', 'model_name', 'object_id',
                  'path', 'detail', 'created_at']


class BackupRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupRecord
        fields = ['id', 'file_path', 'file_size', 'trigger', 'created_at']
