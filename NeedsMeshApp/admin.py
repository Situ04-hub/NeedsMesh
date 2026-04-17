from django.contrib import admin
from .models import UserProfile, Locality, CommunityProblem, ProofImage, SurveySubmission, Notification


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'role', 'completed_tasks', 'has_badge']
    list_editable = ['role']
    list_filter = ['role', 'has_badge']
    search_fields = ['full_name', 'user__email']


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ['name', 'latitude', 'longitude', 'average_urgency']
    search_fields = ['name']


@admin.register(CommunityProblem)
class CommunityProblemAdmin(admin.ModelAdmin):
    list_display = ['locality', 'category', 'urgency', 'status', 'submitted_by', 'created_at']
    list_filter = ['status', 'urgency', 'locality']
    search_fields = ['problem_statement', 'category']
    filter_horizontal = ['interested_volunteers', 'selected_volunteers', 'proof_images']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProofImage)
class ProofImageAdmin(admin.ModelAdmin):
    list_display = ['pk', 'image', 'uploaded_at']


@admin.register(SurveySubmission)
class SurveySubmissionAdmin(admin.ModelAdmin):
    list_display = ['field_worker', 'problem', 'submission_date']
    list_filter = ['submission_date']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'message', 'is_read', 'created_at']
    list_filter = ['is_read']
