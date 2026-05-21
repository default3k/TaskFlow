# TaskFlow - Управление задачами для компаний

## 📌 О проекте

TaskFlow - это веб-приложение для управления задачами внутри компаний. Позволяет создавать компании, приглашать сотрудников, назначать задачи и отслеживать их выполнение.

### Основные возможности:
- ✅ Регистрация и аутентификация пользователей
- ✅ Создание компаний и управление сотрудниками
- ✅ Ролевая модель доступа (владелец, админ, менеджер, разработчик, дизайнер, тестировщик)
- ✅ Создание проектов и задач
- ✅ Назначение исполнителей
- ✅ Изменение статусов задач (Ожидает → В работе → На проверке → Выполнено)
- ✅ Отслеживание времени выполнения задач
- ✅ Экспорт задач в Excel
- ✅ Дашборд со статистикой

## 🏗 Технологии

| Технология | Версия | Назначение |
|------------|--------|------------|
| Python | 3.14+ | Язык программирования |
| Django | 6.0.3 | Веб-фреймворк |
| SQLite | - | База данных (локально) |
| openpyxl | 3.1.5 | Экспорт в Excel |
| HTML/CSS | - | Интерфейс |

## 📂 Структура проекта
TaskFlow/
├── core/ # Главное приложение
│ ├── migrations/ # Миграции БД
│ │ └── init.py
│ ├── templates/ # HTML шаблоны
│ │ └── core/
│ │ ├── base.html # Базовый шаблон (навигация, стили)
│ │ ├── dashboard.html # Главная страница
│ │ ├── login.html # Страница входа
│ │ ├── register.html # Страница регистрации
│ │ ├── company_create.html # Создание компании
│ │ ├── company_edit.html # Редактирование компании
│ │ ├── company_members.html # Управление сотрудниками
│ │ ├── company_requests_manage.html # Заявки в компанию
│ │ ├── company_join_request.html # Подача заявки
│ │ ├── company_confirm_delete.html # Подтверждение удаления
│ │ ├── company_confirm_leave.html # Подтверждение выхода
│ │ ├── project_create.html # Создание проекта
│ │ ├── project_detail.html # Детали проекта
│ │ ├── project_form.html # Форма проекта
│ │ ├── task_create.html # Создание задачи
│ │ ├── task_detail.html # Детали задачи
│ │ ├── task_form.html # Форма задачи
│ │ └── tasks_list.html # Список задач
│ ├── init.py
│ ├── admin.py # Настройка админ-панели
│ ├── apps.py # Конфигурация приложения
│ ├── models.py # Модели БД (главное)
│ ├── views.py # Контроллеры (логика)
│ ├── forms.py # Формы для валидации
│ └── urls.py # Маршруты приложения
│
├── taskflow_project/ # Настройки проекта
│ ├── init.py
│ ├── settings.py # Настройки Django
│ ├── urls.py # Главные маршруты
│ ├── wsgi.py # Для деплоя
│ └── asgi.py # Для деплоя
│
├── project_versions/ # Архив версий
│ ├── CHANGELOG.md # История изменений
│ ├── README.md # Описание версий
│ └── v1.3_dashboard_stats/ # Версия 1.3
│
├── db.sqlite3 # База данных (не в git)
├── manage.py # Управление Django
├── requirements.txt # Зависимости Python
└── PROJECT_DOCS.md # Этот файл

text

## 🗄 Модели данных

### Company (Компания)
| Поле | Тип | Описание |
|------|-----|----------|
| name | CharField | Название компании |
| description | TextField | Описание |
| created_at | DateTimeField | Дата создания |

### User (Пользователь) - расширенный AbstractUser
| Поле | Тип | Описание |
|------|-----|----------|
| role | CharField | Роль (owner/admin/manager/developer/designer/tester/applicant) |
| company | ForeignKey | Компания, где работает |
| phone | CharField | Телефон |
| position | CharField | Должность |
| joined_at | DateTimeField | Дата вступления |

### CompanyJoinRequest (Заявка)
| Поле | Тип | Описание |
|------|-----|----------|
| user | ForeignKey | Пользователь |
| company | ForeignKey | Компания |
| status | CharField | pending/approved/rejected |
| message | TextField | Сообщение |
| created_at | DateTimeField | Дата создания |

### Project (Проект)
| Поле | Тип | Описание |
|------|-----|----------|
| name | CharField | Название |
| description | TextField | Описание |
| company | ForeignKey | Компания |
| created_by | ForeignKey | Создатель |
| created_at | DateTimeField | Дата создания |
| deadline | DateTimeField | Срок выполнения |

### Task (Задача)
| Поле | Тип | Описание |
|------|-----|----------|
| title | CharField | Название |
| description | TextField | Описание |
| status | CharField | waiting/in_progress/review/done |
| priority | CharField | low/medium/high/urgent |
| project | ForeignKey | Проект |
| company | ForeignKey | Компания |
| created_by | ForeignKey | Создатель |
| assigned_to | ForeignKey | Исполнитель |
| created_at | DateTimeField | Дата создания |
| deadline | DateTimeField | Срок выполнения |
| completed_at | DateTimeField | Дата завершения |
| started_at | DateTimeField | Дата начала работы |
| last_status_change | DateTimeField | Последнее изменение |

## 🔐 Система ролей и прав

| Метод | Кто может | Что делает |
|-------|-----------|------------|
| can_manage_company() | owner, admin | Управление компанией |
| can_manage_tasks() | owner, admin, manager | Создание задач |
| can_delete_tasks() | owner, admin, manager | Удаление задач |
| can_change_any_status() | owner, admin, manager | Менять статус любой задачи |
| can_change_own_status() | developer, designer, tester | Менять статус своей задачи |
| can_manage_roles() | owner, admin | Управление ролями |

## 🌐 Маршруты (URLs)

### Основные
| URL | Имя | Описание |
|-----|-----|----------|
| / | dashboard | Главная страница |
| /register/ | register | Регистрация |
| /login/ | login | Вход |
| /logout/ | logout | Выход |

### Компании
| URL | Имя | Описание |
|-----|-----|----------|
| /company/create/ | company_create | Создание компании |
| /company/join/<id>/ | company_join | Подача заявки |
| /company/members/ | company_members | Управление сотрудниками |
| /company/edit/ | company_edit | Редактирование |
| /company/requests/ | company_requests_manage | Заявки |
| /company/delete/ | company_delete | Удаление компании |
| /company/leave/ | company_leave | Выход из компании |

### Проекты
| URL | Имя | Описание |
|-----|-----|----------|
| /project/create/ | project_create | Создание проекта |
| /project/<id>/ | project_detail | Детали проекта |

### Задачи
| URL | Имя | Описание |
|-----|-----|----------|
| /tasks/ | tasks_list | Список задач |
| /tasks/export/ | tasks_export | Экспорт в Excel |
| /task/create/ | task_create | Создание задачи |
| /task/<id>/ | task_detail | Детали задачи |
| /task/<id>/update-status/ | task_update_status | Обновление статуса |
| /task/<id>/delete/ | task_delete | Удаление задачи |

## 🚀 Как запустить проект

### 1. Клонировать репозиторий
```bash
git clone <url>
cd TaskFlow
2. Создать виртуальное окружение
bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
3. Установить зависимости
bash
pip install -r requirements.txt
4. Применить миграции
bash
python manage.py makemigrations
python manage.py migrate
5. Создать суперпользователя
bash
python manage.py createsuperuser
6. Запустить сервер
bash
python manage.py runserver
7. Открыть в браузере
text
http://localhost:8000
📊 Бизнес-логика
Создание компании
Пользователь регистрируется (роль = applicant)

Создает компанию → становится owner

Может принимать заявки от других пользователей

Вступление в компанию
Пользователь подает заявку

Владелец/админ одобряет → пользователь получает роль developer

Пользователь может менять статус своих задач

Управление задачами
Владелец/админ/менеджер создает задачу

Назначает исполнителя (developer/designer/tester)

Исполнитель меняет статус: waiting → in_progress → review → done

При переходе в in_progress фиксируется started_at

При переходе в done фиксируется completed_at

Владелец/админ/менеджер могут менять любой статус

🛠 Важные файлы для разработки
Файл	Что содержит	Когда менять
core/models.py	Структура БД	При добавлении новых сущностей
core/views.py	Логика приложения	При добавлении функционала
core/forms.py	Валидация форм	При изменении форм
core/urls.py	Маршруты	При добавлении страниц
core/templates/	HTML интерфейс	При изменении внешнего вида
taskflow_project/settings.py	Настройки	При деплое
🔧 Частые задачи
Добавить новое поле в модель
Изменить models.py

python manage.py makemigrations

python manage.py migrate

Добавить новую страницу
Создать функцию в views.py

Добавить маршрут в urls.py

Создать HTML шаблон

Экспорт данных
Задачи экспортируются в Excel с сохранением фильтров

Кнопка экспорта на странице /tasks/

📝 История версий
Версия	Дата	Изменения
v1.0	2026-03-30	Базовая функциональность
v1.1	2026-05-21	Исправление моделей
v1.2	2026-05-21	Экспорт в Excel
v1.3	2026-05-21	Улучшенный дашборд
📞 Контакты
Проект выполнен в рамках дипломной работы.

text

## 📁 Теперь создай файл `.gitignore` (чтобы не пушить лишнее):

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Django
db.sqlite3
*.log
*.pot
*.pyc
local_settings.py
.DS_Store

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
project_versions/current/
*.excel
*.xlsx

