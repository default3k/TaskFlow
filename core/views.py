from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
from .models import User, Company, CompanyJoinRequest, Project, Task
from .forms import (
    RegistrationForm, CompanyCreateForm, CompanyJoinRequestForm,
    ProjectForm, TaskForm, TaskStatusForm
)

def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = RegistrationForm()
    
    return render(request, 'core/register.html', {'form': form})

def user_login(request):
    """Вход в систему"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    return render(request, 'core/login.html')

def user_logout(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('login')

@login_required
def dashboard(request):
    """Главная страница (дашборд)"""
    user = request.user
    context = {}
    
    if user.company:
        tasks = Task.objects.filter(company=user.company)
        context['tasks_total'] = tasks.count()
        context['tasks_done'] = tasks.filter(status='done').count()
        context['tasks_in_progress'] = tasks.filter(status='in_progress').count()
        context['tasks_review'] = tasks.filter(status='review').count()
        context['my_tasks'] = tasks.filter(assigned_to=user).order_by('-created_at')[:10]
        context['projects'] = Project.objects.filter(company=user.company).order_by('-created_at')[:5]
        
        if user.can_manage_company():
            context['pending_requests'] = CompanyJoinRequest.objects.filter(
                company=user.company, status='pending'
            )
    else:
        context['my_requests'] = CompanyJoinRequest.objects.filter(user=user)
        context['available_companies'] = Company.objects.exclude(
            id__in=user.join_requests.filter(status__in=['pending', 'approved']).values('company_id')
        )
    
    return render(request, 'core/dashboard.html', context)

@login_required
def company_create(request):
    """Создание компании"""
    if request.method == 'POST':
        form = CompanyCreateForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.owner = request.user
            company.save()
            user = request.user
            user.company = company
            user.role = 'owner'
            user.is_active_member = True
            user.save()
            messages.success(request, f'Компания "{company.name}" создана!')
            return redirect('dashboard')
    else:
        form = CompanyCreateForm()
    return render(request, 'core/company_create.html', {'form': form})

@login_required
def company_join_request(request, company_id):
    """Подача заявки на вступление в компанию"""
    company = get_object_or_404(Company, id=company_id)
    
    # Проверяем, нет ли уже заявки
    existing_request = CompanyJoinRequest.objects.filter(user=request.user, company=company).first()
    if existing_request:
        messages.warning(request, 'Вы уже подали заявку в эту компанию')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CompanyJoinRequestForm(request.POST)
        if form.is_valid():
            join_request = form.save(commit=False)
            join_request.user = request.user
            join_request.company = company
            join_request.save()
            messages.success(request, f'Заявка в компанию "{company.name}" отправлена')
            return redirect('dashboard')
    else:
        form = CompanyJoinRequestForm()
    
    return render(request, 'core/company_join_request.html', {'form': form, 'company': company})

@login_required
def company_requests_manage(request):
    """Управление заявками в компанию"""
    if not request.user.can_manage_company():
        messages.error(request, 'Нет прав')
        return redirect('dashboard')
    
    requests_list = CompanyJoinRequest.objects.filter(
        company=request.user.company, 
        status='pending'
    )
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        join_request = get_object_or_404(CompanyJoinRequest, id=request_id, company=request.user.company)
        
        if action == 'approve':
            join_request.status = 'approved'
            join_request.save()
            user = join_request.user
            user.company = request.user.company
            user.role = 'developer'
            user.is_active_member = True
            user.save()
            messages.success(request, f'{user.username} принят в компанию как разработчик')
        elif action == 'reject':
            join_request.status = 'rejected'
            join_request.save()
            messages.info(request, f'Заявка {join_request.user.username} отклонена')
        
        return redirect('company_requests_manage')
    
    return render(request, 'core/company_requests_manage.html', {'requests': requests_list})

@login_required
def project_create(request):
    """Создание проекта"""
    if not request.user.company:
        messages.error(request, 'Вы не состоите в компании')
        return redirect('dashboard')
    
    if not request.user.can_manage_tasks():
        messages.error(request, 'У вас нет прав на создание проектов')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.company = request.user.company
            project.created_by = request.user
            project.save()
            messages.success(request, f'Проект "{project.name}" создан')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    
    return render(request, 'core/project_form.html', {'form': form, 'title': 'Создание проекта'})

@login_required
def project_detail(request, project_id):
    """Детальная страница проекта"""
    project = get_object_or_404(Project, id=project_id, company=request.user.company)
    return render(request, 'core/project_detail.html', {'project': project})

@login_required
def task_create(request):
    """Создание задачи (владелец, админ, менеджер)"""
    if not request.user.company:
        messages.error(request, 'Вы не состоите в компании')
        return redirect('dashboard')
    
    if not request.user.can_manage_tasks():
        messages.error(request, 'У вас нет прав на создание задач')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = TaskForm(request.POST, company=request.user.company)
        if form.is_valid():
            task = form.save(commit=False)
            task.company = request.user.company
            task.created_by = request.user
            task.save()
            messages.success(request, f'Задача "{task.title}" создана')
            if task.project:
                return redirect('project_detail', project_id=task.project.id)
            return redirect('tasks_list')
    else:
        form = TaskForm(company=request.user.company)
    
    return render(request, 'core/task_form.html', {'form': form, 'title': 'Создание задачи'})

@login_required
def tasks_list(request):
    """Список задач"""
    if not request.user.company:
        messages.error(request, 'Вы не состоите в компании')
        return redirect('dashboard')
    
    tasks = Task.objects.filter(company=request.user.company)
    
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    assigned_filter = request.GET.get('assigned')
    if assigned_filter == 'me':
        tasks = tasks.filter(assigned_to=request.user)
    
    return render(request, 'core/tasks_list.html', {'tasks': tasks})

@login_required
def task_detail(request, task_id):
    """Детальная страница задачи"""
    task = get_object_or_404(Task, id=task_id, company=request.user.company)
    return render(request, 'core/task_detail.html', {'task': task})

@login_required
def task_update_status(request, task_id):
    """Обновление статуса задачи"""
    task = get_object_or_404(Task, id=task_id)
    user = request.user
    
    # Проверка прав на изменение статуса
    can_change = False
    
    # 1. Владелец/админ/менеджер могут менять любой статус
    if user.can_change_any_status():
        can_change = True
    
    # 2. Разработчик/дизайнер/тестировщик могут менять только свои задачи
    elif user.can_change_own_status() and task.assigned_to == user:
        can_change = True
    
    if not can_change:
        messages.error(request, 'Нет прав для изменения статуса')
        return redirect('task_detail', task_id=task.id)
    
    new_status = request.POST.get('status')
    if new_status in dict(Task.STATUS_CHOICES):
        task.status = new_status
        if new_status == 'done':
            task.completed_at = timezone.now()
        task.save()
        messages.success(request, 'Статус обновлен')
    
    return redirect('task_detail', task_id=task.id)

@login_required
def task_delete(request, task_id):
    """Удаление задачи (владелец, админ, менеджер)"""
    task = get_object_or_404(Task, id=task_id)
    user = request.user
    
    if task.company != user.company:
        messages.error(request, 'Нет доступа к этой задаче')
        return redirect('dashboard')
    
    if not user.can_delete_tasks():
        messages.error(request, 'У вас нет прав на удаление задач')
        return redirect('task_detail', task_id=task.id)
    
    # Запоминаем куда редиректить ДО удаления
    if task.project:
        project_id = task.project.id
        task_title = task.title
        task.delete()
        messages.success(request, f'Задача "{task_title}" удалена')
        return redirect('project_detail', project_id=project_id)
    
    # Иначе в общий список задач
    task_title = task.title
    task.delete()
    messages.success(request, f'Задача "{task_title}" удалена')
    return redirect('tasks_list')

@login_required
def company_members(request):
    """Управление сотрудниками компании"""
    if not request.user.can_manage_roles():
        messages.error(request, 'У вас нет прав для управления ролями сотрудников')
        return redirect('dashboard')
    
    members = User.objects.filter(company=request.user.company, is_active_member=True)
    pending_requests = CompanyJoinRequest.objects.filter(company=request.user.company, status='pending')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        member_id = request.POST.get('member_id')
        
        if action == 'change_role':
            new_role = request.POST.get('new_role')
            member = get_object_or_404(User, id=member_id, company=request.user.company)
            
            # Владелец может менять любые роли
            # Админ может менять любые роли, кроме владельца
            if request.user.role == 'owner':
                member.role = new_role
                member.save()
                messages.success(request, f'Роль {member.username} изменена на {member.get_role_display()}')
            elif request.user.role == 'admin' and member.role != 'owner':
                member.role = new_role
                member.save()
                messages.success(request, f'Роль {member.username} изменена на {member.get_role_display()}')
            else:
                messages.error(request, f'Нельзя изменить роль пользователя {member.username}')
        
        elif action == 'remove_member':
            member = get_object_or_404(User, id=member_id, company=request.user.company)
            
            # Нельзя удалить владельца
            if member.role == 'owner':
                messages.error(request, 'Нельзя удалить владельца компании')
            else:
                member.company = None
                member.role = 'applicant'
                member.is_active_member = False
                member.save()
                messages.success(request, f'{member.username} удален из компании')
        
        return redirect('company_members')
    
    return render(request, 'core/company_members.html', {
        'members': members,
        'pending_requests': pending_requests,
    })

@login_required
def company_edit(request):
    """Редактирование компании"""
    if not request.user.can_manage_company():
        messages.error(request, 'У вас нет прав')
        return redirect('dashboard')
    
    if request.method == 'POST':
        company = request.user.company
        company.name = request.POST.get('name')
        company.description = request.POST.get('description')
        company.save()
        messages.success(request, 'Информация о компании обновлена')
        return redirect('company_members')
    
    return render(request, 'core/company_edit.html', {'company': request.user.company})

@login_required
def company_leave(request):
    """Выход из компании (любой сотрудник, кроме владельца)"""
    user = request.user
    
    if not user.company:
        messages.error(request, 'Вы не состоите в компании')
        return redirect('dashboard')
    
    # Владелец не может выйти, только удалить компанию
    if user.role == 'owner':
        messages.error(request, 'Владелец не может выйти из компании. Используйте "Удалить компанию"')
        return redirect('company_members')
    
    if request.method == 'POST':
        company_name = user.company.name
        user.company = None
        user.role = 'applicant'
        user.is_active_member = False
        user.save()
        
        messages.success(request, f'Вы вышли из компании "{company_name}"')
        return redirect('dashboard')
    
    return render(request, 'core/company_confirm_leave.html', {'company': user.company})


@login_required
def company_delete(request):
    """Удаление компании (только владелец или админ)"""
    user = request.user
    
    if not user.company:
        messages.error(request, 'Вы не состоите в компании')
        return redirect('dashboard')
    
    # Проверка прав: только владелец или админ могут удалить компанию
    if not user.can_manage_company():
        messages.error(request, 'У вас нет прав на удаление компании')
        return redirect('dashboard')
    
    company = user.company
    
    if request.method == 'POST':
        company_name = company.name
        
        # Удаляем компанию (каскадно удалятся все проекты, задачи, сотрудники)
        company.delete()
        
        # Обновляем пользователя (он больше не в компании)
        user.company = None
        user.role = 'applicant'
        user.is_active_member = False
        user.save()
        
        messages.success(request, f'Компания "{company_name}" полностью удалена')
        return redirect('dashboard')
    
    return render(request, 'core/company_confirm_delete.html', {'company': company})