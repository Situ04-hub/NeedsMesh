from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home_view, name='home'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Password Reset (OTP)
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('reset-password/', views.reset_password_view, name='reset_password'),

    # Profile
    path('profile/', views.profile_view, name='profile'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Notifications
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_read, name='mark_all_read'),

    # Survey submission (field worker)
    path('submit/', views.submit_survey, name='submit_survey'),

    # Community Needs Board
    path('needs-board/', views.needs_board, name='needs_board'),
    path('needs-board/<int:pk>/help/', views.offer_help, name='offer_help'),

    # Problem detail
    path('problems/<int:pk>/', views.problem_detail, name='problem_detail'),

    # Admin actions
    path('problems/<int:pk>/set-volunteers/', views.set_volunteers_required, name='set_volunteers_required'),
    path('problems/<int:pk>/finalise/', views.finalise_event, name='finalise_event'),
    path('problems/<int:pk>/resolve/', views.resolve_problem, name='resolve_problem'),
    path('problems/<int:pk>/kill/', views.kill_problem, name='kill_problem'),
    path('problems/<int:pk>/message/', views.post_problem_message, name='post_problem_message'),
    path('problems/<int:pk>/accept-volunteer/<int:vol_id>/', views.accept_volunteer, name='accept_volunteer'),
    path('problems/<int:pk>/reject-volunteer/<int:vol_id>/', views.reject_volunteer, name='reject_volunteer'),

    # Heatmap
    path('heatmap/', views.urgency_heatmap, name='urgency_heatmap'),

    # Excel export
    path('export/', views.export_excel, name='export_excel'),

    # Locality management
    path('localities/', views.manage_localities, name='manage_localities'),
    path('localities/<int:pk>/delete/', views.delete_locality, name='delete_locality'),

    # User / role management
    path('users/', views.manage_users, name='manage_users'),

    # Field Worker Applications
    path('manage-applications/', views.manage_applications, name='manage_applications'),
    path('manage-applications/<int:pk>/approve/', views.approve_worker, name='approve_worker'),
    path('manage-applications/<int:pk>/reject/', views.reject_worker, name='reject_worker'),
]
