# MIT Assistent — Backend

Минимальный Django backend для лендинга МИТ Ассистент.

## Функции

- Сбор заявок с формы сайта (`POST /api/leads/`)
- Управление FAQ через Django Admin и отдача через API (`GET /api/faqs/`)

## Стек

- Python 3.12, Django 5.1, DRF 3.15
- PostgreSQL 16
- Gunicorn + Nginx + systemd
- Let's Encrypt SSL

## Production-деплой на VPS (Ubuntu 24.04)

### Требования к VPS

- Ubuntu 24.04 LTS
- root-доступ
- Минимум 1 vCPU, 2 GB RAM, 20 GB SSD
- Домен `api.titovtech.ru` с A-записью на IP VPS

### Деплой

1. Залей проект на VPS в `/opt/mit-assistent/backend/`
2. Запусти от root:

```bash
chmod +x deploy/install.sh
./deploy/install.sh
```

Скрипт установит всё: PostgreSQL, Python, Nginx, Gunicorn, SSL.

3. Создай суперпользователя:

```bash
cd /opt/mit-assistent/backend
venv/bin/python manage.py createsuperuser
```

### Управление

```bash
# Статус
systemctl status mit-assistent
systemctl status nginx
systemctl status postgresql

# Перезапуск backend
systemctl restart mit-assistent

# Логи
journalctl -u mit-assistent -f
tail -f /var/log/mit-assistent/gunicorn-error.log
tail -f /var/log/mit-assistent/gunicorn-access.log

# Backup PostgreSQL
su - postgres -c 'pg_dump mit_assistent' > backup_$(date +%Y%m%d).sql

# Restore PostgreSQL
su - postgres -c 'psql mit_assistent' < backup_20260706.sql
```

## Быстрый старт (локальная разработка)

Для локальной разработки можно использовать SQLite:

```bash
cp .env.example .env
# В .env замени DATABASES на SQLite или используй локальный PostgreSQL
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## API

### POST /api/leads/

Создать заявку.

```json
{
  "last_name": "Иванов",
  "first_name": "Иван",
  "telegram": "@ivanov",
  "email": "ivan@example.com",
  "task_description": "Хочу автоматизировать отчёты",
  "utm_source": "google",
  "utm_medium": "cpc",
  "utm_campaign": "launch",
  "utm_content": "banner1",
  "utm_term": "1c+assistent",
  "page_url": "https://titovtech.ru/assistent/"
}
```

Ответ: `{"success": true, "message": "Заявка отправлена"}`

Honeypot-защита: добавь скрытое поле `honeypot` в форму. Если оно заполнено — запрос отклонится.

### GET /api/faqs/

Список активных FAQ, отсортированных по `sort_order`.

```json
[
  {"question": "Что такое МИТ Ассистент?", "answer": "Это AI-помощник..."},
  {"question": "Сколько стоит?", "answer": "От 10 000 ₽/мес..."}
]
```

## Переменные окружения

См. `.env.example`. Основные:

| Переменная | Назначение |
|---|---|
| `SECRET_KEY` | Секретный ключ Django |
| `DEBUG` | Режим отладки (True/False) |
| `ALLOWED_HOSTS` | Разрешённые хосты через запятую |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Подключение к PostgreSQL |
| `CORS_ALLOWED_ORIGINS` | Разрешённые CORS-ориджины через запятую |
| `CSRF_TRUSTED_ORIGINS` | Доверенные CSRF-ориджины через запятую |

## Структура проекта

```
backend/
├── config/             # Django settings, urls, wsgi
├── leads/              # Модель Lead + API + Admin
├── faqs/               # Модель FAQItem + API + Admin
├── deploy/             # systemd unit, nginx config, install.sh
├── staticfiles/        # Собранная статика (collectstatic)
├── logs/               # Логи Django
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```
