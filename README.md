# Igrovorot

Социальная сеть для геймеров. Пользователи читают ленту постов и рецензий, ведут блоги, оценивают игры, подписываются друг на друга и подключают Steam-аккаунт для отображения библиотеки.

## Стек

| Слой | Технология |
|---|---|
| Backend | Python 3.13, Django 6 |
| База данных | PostgreSQL |
| Фронтенд | Vanilla JS, CSS Custom Properties |
| Внешние API | RAWG API (каталог игр), Steam API (библиотека) |
| Email | Gmail SMTP |
| Конфигурация | python-decouple (`.env`) |

## Структура проекта

```
GameStorn/
├── apps/
│   ├── users/        # Авторизация, профили, Steam-интеграция, middleware
│   ├── posts/        # Посты, комментарии, лента, поиск
│   ├── games/        # Каталог игр (RAWG), детальные страницы
│   ├── reviews/      # Рецензии с оценкой, сигналы инвалидации кеша
│   ├── social/       # Лайки, подписки (Follow)
│   └── moderation/   # Панель модератора, жалобы, бан пользователей
├── project/          # settings.py, urls.py, wsgi.py
├── templates/        # HTML-шаблоны (base.html + страницы по приложениям)
├── static/
│   ├── css/style.css
│   └── js/           # csrf.js, validate.js, deferred.js, like.js, follow.js
├── media/            # Загружаемые пользователями файлы
└── .env              # Секреты (не коммитить)
```

## Быстрый старт

### 1. Клонировать и создать окружение

```bash
git clone <repo-url>
cd GameStorn
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### 2. Создать `.env`

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=igrovorot
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

RAWG_API_KEY=your-rawg-key
STEAM_API_KEY=your-steam-key
```

### 3. Применить миграции и запустить

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Сайт доступен по адресу `http://127.0.0.1:8000`

## Приложения и ключевые возможности

### users
- Кастомная модель `User` + модель `Profile` (аватар, bio, Steam ID, статус бана)
- Регистрация с подтверждением по email
- `BanMiddleware` — блокирует доступ забаненных пользователей
- `LastSearchMiddleware` — читает куку `last_search`, добавляет `request.last_search`
- Steam-интеграция: подключение аккаунта, отображение библиотеки с наигранными часами

### posts
- Посты с множественными изображениями (`PostImage`, related_name `images`)
- Теги (текстовое поле, фильтрация по тегу)
- Комментарии
- **Лента** (`/feed/`) — посты и рецензии вперемешку, отсортированные по дате; бесконечный скролл через `IntersectionObserver` + AJAX partial-рендер (`?partial=1`)
- Поиск по заголовкам, тегам, играм, пользователям

### games
- Каталог игр с обложками, жанрами, средним рейтингом
- Данные подтягиваются через RAWG API при добавлении игры
- Фрагментный кеш шаблона (`{% cache 900 ... games_version %}`) с версионной инвалидацией через Django signals
- Фильтрация по жанру, поиск, сортировка по рейтингу
- Галерея скриншотов (главное фото + лента превью)

### reviews
- Рецензии с оценкой 1–10
- `post_save` / `post_delete` сигналы инкрементируют `games_list_version` в кеше
- Лайки на рецензиях через AJAX

### social
- Подписки (`Follow`) — AJAX без перезагрузки страницы (`follow.js`)
- Лайки на постах и рецензиях — AJAX с паттерном Deferred (`like.js`, `deferred.js`)

### moderation
- Группа `Moderator` — доступ к панели `/moderation/`
- Управление постами и рецензиями (редактирование, удаление)
- Бан пользователей (срочный или бессрочный) с указанием причины
- Жалобы (`Report`) на посты, рецензии, пользователей с возможностью закрыть

## JavaScript

| Файл | Назначение |
|---|---|
| `csrf.js` | `getCsrfToken()` — читает CSRF-токен из куки |
| `validate.js` | Клиентская валидация форм (required, minlength, email, number) |
| `deferred.js` | Кастомный класс `Deferred` + `ajaxDeferred()` поверх `fetch` |
| `like.js` | Лайки через `ajaxDeferred` с `.done/.fail/.always` |
| `follow.js` | Подписка/отписка через обычный `fetch` |

Inline-скрипты в шаблонах: сворачивание сайдбара (localStorage), бесконечный скролл ленты, галерея скриншотов, превью загружаемых изображений.

## Роли пользователей

| Роль | Возможности |
|---|---|
| Гость | Просмотр ленты, каталога, постов, профилей |
| Пользователь | + создание постов, рецензий, лайки, подписки, редактирование профиля |
| Модератор (группа `Moderator`) | + панель модерации, бан пользователей, закрытие жалоб |
| Суперпользователь | + Django Admin |

## Переменные окружения

| Переменная | Описание |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Режим отладки (`True`/`False`) |
| `ALLOWED_HOSTS` | Разрешённые хосты через запятую |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Gmail SMTP (App Password) |
| `RAWG_API_KEY` | Ключ RAWG API для каталога игр |
| `STEAM_API_KEY` | Ключ Steam Web API |
