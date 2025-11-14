@echo off
echo ========================================
echo   Автоматический деплой на Scalingo
echo ========================================
echo.

REM Проверка Git
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git не установлен!
    echo 💡 Установите Git: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Проверка Scalingo CLI
scalingo version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Scalingo CLI не найден
    echo 💡 Установите: 
    echo    iwr -useb https://cli-dl.scalingo.com/install ^| iex
    echo.
    echo 🌐 Или используйте веб-интерфейс: https://dashboard.scalingo.com/
    pause
    exit /b 1
)

echo ✅ Git и Scalingo CLI найдены
echo.

REM Инициализация Git если нужно
if not exist ".git\" (
    echo 📦 Инициализация Git репозитория...
    git init
    echo.
)

REM Добавление файлов
echo 📝 Добавление файлов в Git...
git add .
git status
echo.

REM Коммит
set /p commit_message="💬 Введите сообщение коммита (Enter = 'Deploy to Scalingo'): "
if "%commit_message%"=="" set commit_message=Deploy to Scalingo

git commit -m "%commit_message%"
echo.

REM Создание приложения в Scalingo
echo 🚀 Создание приложения в Scalingo...
set /p app_name="📱 Введите имя приложения (например: telegram-rp-bot-myname): "

if "%app_name%"=="" (
    echo ❌ Имя приложения обязательно!
    pause
    exit /b 1
)

scalingo create %app_name% --region osc-fr1
echo.

REM Настройка переменных окружения
echo ⚙️ Настройка переменных окружения...
echo.

echo 🤖 Настройте переменные в Dashboard:
echo    https://dashboard.scalingo.com/apps/%app_name%/environment
echo.
echo 📋 Необходимые переменные:
echo    TELEGRAM_BOT_TOKEN = ваш_токен_от_botfather
echo    OPENROUTER_API_KEY = ваш_ключ_от_openrouter
echo    MODEL_NAME = tngtech/deepseek-r1t2-chimera:free
echo.

set /p continue="✅ Настроили переменные? (y/N): "
if /i not "%continue%"=="y" (
    echo ⏸️ Настройте переменные и запустите скрипт снова
    pause
    exit /b 0
)

REM Деплой
echo 🚀 Деплой приложения...
git push scalingo main

echo.
echo ========================================
echo ✅ Деплой завершён!
echo ========================================
echo.
echo 🔗 Ваше приложение: https://dashboard.scalingo.com/apps/%app_name%
echo 📊 Логи: scalingo -a %app_name% logs
echo 🔄 Рестарт: scalingo -a %app_name% restart
echo.

pause