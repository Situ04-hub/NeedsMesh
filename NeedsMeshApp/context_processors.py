from .models import Notification


def notifications_processor(request):
    """Inject unread notification count into every template context."""
    if request.user.is_authenticated:
        unread = Notification.objects.filter(
            recipient=request.user, is_read=False
        )
        return {
            'unread_notifications': unread,
            'unread_count': unread.count(),
        }
    return {'unread_notifications': [], 'unread_count': 0}
