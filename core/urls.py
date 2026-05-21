from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=False)),
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Компании
    path('company/create/', views.company_create, name='company_create'),
    path('company/join/<int:company_id>/', views.company_join_request, name='company_join'),
    path('company/members/', views.company_members, name='company_members'),
    path('company/edit/', views.company_edit, name='company_edit'),
    path('company/requests/', views.company_requests_manage, name='company_requests_manage'),
    path('company/delete/', views.company_delete, name='company_delete'),
    path('company/leave/', views.company_leave, name='company_leave'),
    path('notifications/', views.notifications_view, name='notifications'),
    
    # Проекты
    path('project/create/', views.project_create, name='project_create'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    
    # Задачи
    path('tasks/', views.tasks_list, name='tasks_list'),
    path('tasks/export/', views.export_tasks_excel, name='tasks_export'),  # ← ДОБАВИТЬ ЭТУ СТРОКУ
    path('task/create/', views.task_create, name='task_create'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/update-status/', views.task_update_status, name='task_update_status'),
    path('task/<int:task_id>/delete/', views.task_delete, name='task_delete'),

    # Профиль
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]