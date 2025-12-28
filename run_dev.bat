@echo off
REM Автоматический запуск проекта Geeker в режиме разработки (SQLite, dev-настройки)

SETLOCAL

REM Переходим в папку скрипта (корень проекта)
cd /d %~dp0

echo [Geeker] Проверка виртуального окружения...
IF NOT EXIST ".venv" (
  echo [Geeker] Виртуальное окружение не найдено, создаю...
  py -3 -m venv .venv
)

echo [Geeker] Активирую виртуальное окружение...
CALL .venv\Scripts\activate.bat

echo [Geeker] Устанавливаю зависимости...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [Geeker] Применяю миграции (создание таблиц SQLite)...
python manage.py makemigrations core profiles library blog communities chat
python manage.py migrate

echo [Geeker] Запускаю сервер разработки на http://127.0.0.1:8000/ ...

REM Запускаем сервер в новом окне, чтобы текущее окно не блокировалось
start "Geeker Django Server" cmd /k "cd /d %~dp0 && CALL .venv\Scripts\activate.bat && python manage.py runserver"

REM Открываем домашнюю страницу в браузере по умолчанию
start "" http://127.0.0.1:8000/library/

echo [Geeker] Готово. Сервер запущен в отдельном окне. Это окно можно закрыть.

ENDLOCAL




