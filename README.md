## Geeker — коллектор библиотеки, блога, чатов и сообществ

Этот репозиторий содержит Django‑проект **Geeker** с разделами:
- **Домашняя страница / Библиотека**: коллекции и предметы.
- **Профиль пользователя**: профиль, роли, настройки языка и часового пояса.
- **Блог**: публикации и комментарии (расширяемо).
- **Чат и подписки**: чаты между пользователями и в сообществах.
- **Сообщества**: публичные и приватные комьюнити.

Проект спроектирован с учётом:
- быстрого отклика (коллекции и предметы с индексацией в PostgreSQL),
- безопасности (HTTPS, bcrypt, JWT, CSRF/XSS‑защита, ролевые модели),
- масштабируемости (PostgreSQL + Redis + Celery + Channels, Docker‑оркестрация).

---

## Структура проекта

- **Корень проекта**
  - **`manage.py`** — запуск Django‑команд (`runserver`, `migrate`, `createsuperuser` и т.д.).
  - **`requirements.txt`** — список Python‑зависимостей.
  - **`config/`**
    - **`settings/base.py`** — общие настройки:
      - PostgreSQL, Redis, Celery, Channels;
      - DRF + SimpleJWT (JWT‑аутентификация);
      - локализация (`ru`, `en`);
      - безопасность (CSRF, HTTPS, HSTS, XSS);
      - кэширование через `django-redis`.
    - **`settings/dev.py`** — режим разработки (DEBUG=True, упрощённый HTTPS).
    - **`settings/prod.py`** — продакшен (DEBUG=False, строгие security‑флаги).
    - **`urls.py`** — корневая маршрутизация:
      - `/accounts/`, `/profile/`, `/library/`, `/blog/`, `/communities/`, `/chat/`.
    - **`wsgi.py`** — входная точка для WSGI‑серверов (gunicorn/uWSGI).
    - **`asgi.py`** — входная точка ASGI (HTTP + WebSocket через Django Channels).
    - **`celery.py`** — конфигурация Celery‑воркера (очереди задач на Redis).

- **`apps/` — доменные приложения**
  - **`apps/core`**
    - **`models.py`**
      - `TimeStampedModel` — абстрактная модель с `created_at`/`updated_at`.
      - `Comment` — универсальная модель комментария (generic FK, расширяемая).
  - **`apps/accounts`**
    - **`views.py`**
      - `LoginView`, `LogoutView`, `RegisterView` — HTML‑страницы входа/выхода/регистрации.
    - **`urls.py`**
      - `/accounts/login/`, `/accounts/logout/`, `/accounts/register/`;
      - `/accounts/api/token/`, `/accounts/api/token/refresh/` — JWT‑эндпоинты (SimpleJWT).
  - **`apps/profiles`**
    - **`models.py`**
      - `UserProfile` — профиль пользователя (роль `user/moderator/admin`, язык, часовой пояс, био, аватар).
    - **`views.py`**
      - просмотр и редактирование профиля текущего пользователя.
    - **`urls.py`**
      - `/profile/` — профиль,
      - `/profile/edit/` — редактирование профиля.
  - **`apps/library`**
    - **`models.py`**
      - `Tag`, `Collection`, `Item`, `ItemMedia`:
        - связи «владелец → коллекции → предметы → медиа»;
        - индексы по `owner`, `visibility`, `created_at`, `collection`, `position`;
        - `SearchVectorField` + `GinIndex` для полнотекстового поиска (PostgreSQL).
    - **`views.py`**
      - `HomeView` — домашняя страница (список коллекций текущего пользователя).
      - `CollectionListView`, `CollectionDetailView` — список и детали коллекций.
      - `CollectionCreateView/UpdateView/DeleteView` — CRUD коллекций.
      - `ItemDetailView` — просмотр предмета с медиа.
    - **`urls.py`**
      - `/library/` — домашняя,
      - `/library/collections/…`,
      - `/library/items/<id>/`.
  - **`apps/blog`**
    - **`models.py`**
      - `BlogPost` — автор, заголовок, slug, содержимое, статус `draft/published`, теги, `published_at`.
    - **`views.py`**, **`urls.py`**
      - `/blog/` — список опубликованных постов;
      - `/blog/<slug>/` — просмотр поста.
  - **`apps/communities`**
    - **`models.py`**
      - `Community` — сообщество (публичное/приватное, владелец).
      - `CommunityMembership` — членство (роль `member/moderator`, бан, дата вступления).
    - **`views.py`**, **`urls.py`**
      - `/communities/` — список сообществ;
      - `/communities/<slug>/` — детали сообщества.
  - **`apps/chat`**
    - **`models.py`**
      - `Chat` — чат (`direct/group/community`), участники, при необходимости привязка к сообществу.
      - `Message` — сообщения (автор, текст, вложения, флаги `is_edited/is_deleted`, индексы по чату и времени).
    - **`views.py`**, **`urls.py`**
      - `/chat/` — список чатов;
      - `/chat/<id>/` — страница комнаты.
    - **`consumers.py`**, **`routing.py`**
      - WebSocket‑чат через Django Channels;
      - URL `ws://host/ws/chat/<chat_id>/`.
  - **`apps/integrations`**
    - **`base.py`** — базовые интерфейсы адаптеров (`BaseStorageAdapter`, `BaseEmailAdapter`).
    - **`storage.py`** — пример `S3StorageAdapter` (S3/MinIO‑совместимое хранилище для медиа).

- **Шаблоны и статика**
  - **`templates/base/`**
    - `base.html` — общий HTML‑каркас (подключение `static/css/main.css` и `static/js/main.js`).
    - `base_app.html` — layout с левой боковой панелью и основной областью контента.
    - `_navbar.html` — верхняя панель (логотип, имя пользователя, logout).
    - `_sidebar.html` — боковое меню: Дом, Профиль, Библиотека, Блог, Чат, Сообщества.
    - `_messages.html` — вывод флэш‑сообщений.
    - `_pagination.html` — пагинация.
  - **`templates/accounts/`** — страницы логина/регистрации.
  - **`templates/profiles/`** — просмотр/редактирование профиля.
  - **`templates/library/`** — домашняя, список и детали коллекций, детали предметов.
  - **`templates/blog/`**, **`templates/communities/`**, **`templates/chat/`** — соответствующие разделы.
  - **`static/css/main.css`** — адаптивный современный интерфейс с тёмной темой.
  - **`static/js/main.js`** — глобальный JS (можно добавить переключатель темы и др.).

- **Docker / Nginx / оркестрация**
  - **`docker/web.Dockerfile`** — образ Python + Django + gunicorn.
  - **`docker/nginx.Dockerfile`**, **`docker/nginx.conf`** — конфигурация Nginx:
    - редирект HTTP → HTTPS;
    - TLS (сертификаты `fullchain.pem` и `privkey.pem`);
    - проксирование `/`, `/static/`, `/media/`, `/ws/` на приложение.
  - **`compose/docker-compose.dev.yml`** — стек разработки:
    - `web` (Django `runserver`),
    - `db` (PostgreSQL),
    - `redis` (Redis‑сервер).
  - **`compose/docker-compose.prod.yml`** — продакшен‑стек:
    - `web` (gunicorn + Django),
    - `db` (PostgreSQL),
    - `redis`,
    - `nginx` (HTTPS reverse proxy).

---

## Зависимости и необходимые программы

- **Обязательные компоненты (для локального запуска без Docker):**
  - Python 3.12+;
  - PostgreSQL 14+ (сервер БД или внешний инстанс);
  - Redis 6/7 (для кэша, Celery и Channels);
  - Git (по желанию, для версионирования).

- **Для запуска через контейнеры:**
  - Docker Desktop (Windows);
  - Docker Compose (входит в Docker Desktop).

---

## Настройка подключения к базам данных

Все параметры окружения читаются через `django-environ` в `config/settings/base.py`.

Создайте в корне проекта файл `.env` (рядом с `manage.py`), например:

```env
DJANGO_SECRET_KEY=some-very-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=geeker
POSTGRES_USER=geeker
POSTGRES_PASSWORD=geeker_pass
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
REDIS_CHANNEL_URL=redis://127.0.0.1:6379/3

SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
```

- Для локальной PostgreSQL:
  - создайте БД `geeker` и пользователя `geeker` с паролем `geeker_pass` (или измените значения в `.env`).
- Для PostgreSQL в Docker:
  - используйте `POSTGRES_HOST=db` и те же значения, что заданы в `compose/docker-compose.dev.yml`.

---

## Запуск проекта локально (без Docker)

1. **Создать и активировать виртуальное окружение (Windows PowerShell):**

```powershell
cd C:\Users\Lit\Desktop\Geeker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. **Установить зависимости:**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. **Настроить `.env`** (см. пример выше) и убедиться, что PostgreSQL и Redis запущены.

4. **Применить миграции и создать суперпользователя:**

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. **Запустить сервер разработки:**

```bash
python manage.py runserver
```

6. **Открыть в браузере:**
   - `http://127.0.0.1:8000/library/` — домашняя/библиотека;
   - `http://127.0.0.1:8000/accounts/register/` — регистрация;
   - `http://127.0.0.1:8000/accounts/login/` — вход;
   - `http://127.0.0.1:8000/profile/` — профиль;
   - `http://127.0.0.1:8000/admin/` — админка.

---

## Запуск через Docker (рекомендуется для единообразия)

### Режим разработки

1. Перейти в каталог `compose/`:

```bash
cd compose
docker compose -f docker-compose.dev.yml up --build
```

2. При первом запуске выполнить миграции и создать суперпользователя:

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

3. Открыть в браузере:
   - `http://localhost:8000/library/`, `http://localhost:8000/accounts/login/`, `http://localhost:8000/admin/`.

### Продакшен‑режим (упрощённый)

1. Подготовить TLS‑сертификаты:
   - `certs/fullchain.pem`,
   - `certs/privkey.pem`.

2. Запустить:

```bash
cd compose
docker compose -f docker-compose.prod.yml up --build -d
```

3. Приложение будет доступно по HTTPS на `https://<ваш_хост>/`.

---

## Безопасность

- **HTTPS**:
  - В prod‑настройках включён `SECURE_SSL_REDIRECT`, HSTS, secure‑cookies.
  - Nginx перенаправляет HTTP → HTTPS.
- **Хэширование паролей**:
  - В `PASSWORD_HASHERS` первым стоит `BCryptSHA256PasswordHasher`.
- **JWT с ограниченным сроком действия**:
  - `ACCESS_TOKEN_LIFETIME=15 минут`, `REFRESH_TOKEN_LIFETIME=7 дней` (см. `SIMPLE_JWT`).
  - Эндпоинты: `/accounts/api/token/` и `/accounts/api/token/refresh/`.
- **Защита от SQL‑инъекций**:
  - Используется Django ORM, без сырых SQL.
- **CSRF/XSS**:
  - `CsrfViewMiddleware` включён, во всех формах применяется `{% csrf_token %}`.
  - Шаблоны используют автоэкранирование; `|safe` не применяется к пользовательскому вводу.
- **Роли и доступ**:
  - Ролевая модель в `UserProfile.role` (`user`, `moderator`, `admin`);
  - можно расширять через стандартные `Group`/`Permission`.

---

## Проверка работоспособности

- **База данных и миграции**
  - Успешный запуск `python manage.py migrate` (или `docker compose exec web python manage.py migrate`) подтверждает корректное подключение к PostgreSQL.
  - В админке `/admin/` должны быть доступны модели пользователей, профилей, коллекций, сообществ, чатов и т.д.

- **Основные пользовательские сценарии**
  - Регистрация на `/accounts/register/`, вход на `/accounts/login/`.
  - Просмотр и редактирование профиля на `/profile/`.
  - Создание коллекции на `/library/collections/create/` и просмотр списка/деталей.
  - Просмотр списка блог‑постов `/blog/` (наполнение через админку).
  - Работа с сообществами `/communities/`.

- **Чат и WebSocket**
  - Зайти в `/chat/`, выбрать комнату `/chat/<id>/`.
  - Открыть одну и ту же комнату в двух вкладках, отправлять сообщения и убедиться, что они появляются в обеих вкладках (Channels + Redis работают).

- **JWT и API**
  - Через Postman или curl:
    - `POST /accounts/api/token/` с корректным `username`/`password` → получить `access`/`refresh`.
    - `POST /accounts/api/token/refresh/` с `refresh` → новый `access`.

---

## Рекомендации по дальнейшей разработке

- Хранить бизнес‑логику в `services.py` внутри каждого приложения, чтобы `views.py` оставались максимально тонкими.
- Добавить DRF‑сериализаторы и API‑viewset’ы (`serializers.py`, `api_views.py`) для всех ключевых сущностей, если планируется SPA или мобильный клиент.
- Для соответствия 152‑ФЗ добавить:
  - эндпоинты/страницы для выгрузки и удаления персональных данных;
  - аудит‑лог действий администраторов (отдельная модель + сигналы).
