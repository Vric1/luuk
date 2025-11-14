@echo off
echo Запуск Telegram РП Бота с ИИ...
echo.

REM Проверка установки Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не установлен или не добавлен в PATH
    echo Скачайте Python с https://python.org/downloads/
    pause
    exit /b 1
)

REM Установка зависимостей если нужно
if not exist "venv\" (
    echo Создание виртуального окружения...
    python -m venv venv
)

REM Активация виртуального окружения
call venv\Scripts\activate.bat

REM Установка зависимостей
echo Проверка зависимостей...
pip install -r requirements.txt

REM Запуск бота
echo.
echo ========================================
echo  Бот запускается...
echo  Для остановки нажмите Ctrl+C
echo ========================================
echo.

python bot.py

echo.
echo Бот остановлен.
pause