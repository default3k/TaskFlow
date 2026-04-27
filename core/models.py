from django.db import models
from django.contrib.auth.models import AbstractUser

class Company(models.Model):
    """Модель компании"""
    name = models.CharField('Название компании', max_length=200)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    owner = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_companies', verbose_name='Владелец')
    
    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = 'Компании'
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    """Расширенная модель пользователя"""
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
    company = models.ForeignKey(
        Company, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Компания',
        related_name='employees'
    )
    phone = models.CharField('Телефон', max_length=20, blank=True)
    position = models.CharField('Должность', max_length=100, blank=True)
    is_active_member = models.BooleanField('Активный сотрудник', default=False)
    joined_at = models.DateTimeField('Дата вступления', auto_now_add=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='core_user_set',
        related_query_name='core_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='core_user_set',
        related_query_name='core_user',
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    # Базовые проверки ролей
    def is_company_owner(self):
        return self.role == 'owner' and self.company is not None
    
    def is_company_admin(self):
        return self.role in ['owner', 'admin'] and self.company is not None
    
    def is_company_manager(self):
        return self.role in ['owner', 'admin', 'manager'] and self.company is not None
    
    # Новая система прав
    def can_manage_company(self):
        """Управление компанией (роли, заявки, удаление сотрудников)"""
        return self.role in ['owner', 'admin'] and self.company is not None
    
    def can_manage_tasks(self):
        """Создание задач"""
        return self.role in ['owner', 'admin', 'manager'] and self.company is not None
    
    def can_delete_tasks(self):
        """Удаление задач"""
        return self.role in ['owner', 'admin', 'manager'] and self.company is not None
    
    def can_change_any_status(self):
        """Менять статус любой задачи"""
        return self.role in ['owner', 'admin', 'manager'] and self.company is not None
    
    def can_change_own_status(self):
        """Менять статус только своей задачи"""
        return self.role in ['developer', 'designer', 'tester'] and self.company is not None
    
    def can_manage_roles(self):
        """Управление ролями сотрудников"""
        return self.role in ['owner', 'admin'] and self.company is not None
    
    # Старые методы для совместимости (помечены как deprecated)
    def can_approve_tasks(self):
        """Устаревший метод, используйте can_change_any_status"""
        return self.can_change_any_status()
    
    def get_role_display_ru(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

class CompanyJoinRequest(models.Model):
    """Заявка на вступление в компанию"""
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='join_requests')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Компания', related_name='join_requests')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField('Сопроводительное сообщение', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Заявка на вступление'
        verbose_name_plural = 'Заявки на вступление'
        unique_together = ['user', 'company']
    
    def __str__(self):
        return f"{self.user.username} -> {self.company.name} ({self.status})"

class Project(models.Model):
    """Проект"""
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Компания', related_name='projects')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Создал', related_name='created_projects')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    deadline = models.DateTimeField('Срок выполнения', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
    
    def __str__(self):
        return self.name
    
    def get_progress(self):
        tasks = self.tasks.all()
        if not tasks:
            return 0
        completed = tasks.filter(status='done').count()
        return int((completed / tasks.count()) * 100)

class Task(models.Model):
    """Задача"""
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
    
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='waiting')
    priority = models.CharField('Приоритет', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='Проект', related_name='tasks', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Компания', related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Создал', related_name='created_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='Исполнитель', related_name='assigned_tasks', null=True, blank=True)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    deadline = models.DateTimeField('Срок выполнения', null=True, blank=True)
    completed_at = models.DateTimeField('Дата выполнения', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
    
    def __str__(self):
        return self.title