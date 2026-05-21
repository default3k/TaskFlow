from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone

class Company(models.Model):
    name = models.CharField('Название компании', max_length=200)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = 'Компании'
    
    def __str__(self):
        return self.name
    
    def get_owner(self):
        return self.employees.filter(role='owner').first()


class User(AbstractUser):
    ROLE_CHOICES = [
        ('owner', 'Владелец компании'),
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('developer', 'Разработчик'),
        ('designer', 'Дизайнер'),
        ('tester', 'Тестировщик'),
        ('applicant', 'Соискатель'),
    ]
    
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='applicant')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Компания', related_name='employees')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    position = models.CharField('Должность', max_length=100, blank=True)
    joined_at = models.DateTimeField('Дата вступления', auto_now_add=True)
    
    groups = models.ManyToManyField('auth.Group', verbose_name='groups', blank=True, related_name='core_user_set', related_query_name='core_user')
    user_permissions = models.ManyToManyField('auth.Permission', verbose_name='user permissions', blank=True, related_name='core_user_set', related_query_name='core_user')
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(fields=['company'], condition=models.Q(role='owner'), name='unique_owner_per_company')
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_active_member(self):
        return self.company is not None and self.role != 'applicant'
    
    def can_manage_company(self):
        return self.role in ['owner', 'admin'] and self.company is not None
    
    def can_manage_tasks(self):
        return self.role in ['owner', 'admin', 'manager'] and self.company is not None
    
    def can_delete_tasks(self):
        return self.role in ['owner', 'admin', 'manager'] and self.company is not None
    
    def can_change_any_status(self):
        return self.role in ['owner', 'admin', 'manager'] and self.company is not None
    
    def can_change_own_status(self):
        return self.role in ['developer', 'designer', 'tester'] and self.company is not None
    
    def can_manage_roles(self):
        return self.role in ['owner', 'admin'] and self.company is not None


class CompanyJoinRequest(models.Model):
    STATUS_CHOICES = [('pending', 'На рассмотрении'), ('approved', 'Одобрена'), ('rejected', 'Отклонена')]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='join_requests')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='join_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'company']
    
    def __str__(self):
        return f"{self.user.username} -> {self.company.name}"


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_progress(self):
        tasks = self.tasks.all()
        if not tasks:
            return 0
        completed = tasks.filter(status='done').count()
        return int((completed / tasks.count()) * 100)


class Task(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('review', 'На проверке'),
        ('done', 'Выполнено'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочный'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='assigned_tasks', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    last_status_change = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at', '-priority']
    
    def __str__(self):
        return self.title
    
    def clean(self):
        if self.company_id:
            if self.assigned_to and self.assigned_to.company_id != self.company_id:
                raise ValidationError({'assigned_to': f'Исполнитель не состоит в вашей компании'})
            if self.project and self.project.company_id != self.company_id:
                raise ValidationError({'project': f'Проект принадлежит другой компании'})
    
    def save(self, *args, **kwargs):
        if self.status == 'in_progress' and not self.started_at:
            self.started_at = timezone.now()
        if self.status == 'done' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)
    
    def get_time_spent(self):
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return round(delta.total_seconds() / 3600, 1)
        elif self.started_at:
            delta = timezone.now() - self.started_at
            return round(delta.total_seconds() / 3600, 1)
        return None

class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']

class Notification(models.Model):
    """Уведомление для пользователя"""
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Назначена задача'),
        ('task_status_changed', 'Изменен статус задачи'),
        ('task_comment', 'Новый комментарий'),
        ('request_approved', 'Заявка одобрена'),
        ('request_rejected', 'Заявка отклонена'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='Пользователь')
    type = models.CharField('Тип', max_length=30, choices=NOTIFICATION_TYPES)
    message = models.CharField('Сообщение', max_length=255)
    link = models.CharField('Ссылка', max_length=200, blank=True)
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"