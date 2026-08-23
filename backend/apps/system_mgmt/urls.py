from rest_framework.routers import DefaultRouter

from .views import ApprovalRequestViewSet, OperationLogViewSet, BackupViewSet

router = DefaultRouter()
router.register('approvals', ApprovalRequestViewSet, basename='approvals')
router.register('logs', OperationLogViewSet, basename='operation-logs')
router.register('backups', BackupViewSet, basename='backups')
urlpatterns = router.urls
