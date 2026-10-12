@echo off
setlocal enabledelayedexpansion
title Delux Tour and Travel - Web Server
cd /d "%~dp0"

cls
echo ========================================================================
echo               * DELUX TOUR & TRAVEL - DJANGO WEB SERVER *
echo ========================================================================
echo.

:: 1. Check Python
echo [1/5] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not added to your system PATH!
    echo Please install Python 3.10+ from python.org and check "Add to PATH".
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i detected.

:: 2. Check dependencies
echo.
echo [2/5] Checking required Python packages...
python -c "import django, pymysql, cryptography, razorpay" >nul 2>&1
if errorlevel 1 (
    echo [NOTICE] Installing missing dependencies from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements!
        pause
        exit /b 1
    )
)
echo [OK] All required Python packages are installed.

:: 3. Check WAMP MySQL connection
echo.
echo [3/5] Checking MySQL (WAMP) connection on port 3306...
python -c "import socket; s=socket.socket(); s.settimeout(1.5); s.connect(('127.0.0.1', 3306)); s.close()" >nul 2>&1
if errorlevel 1 (
    echo ========================================================================
    echo [NOTICE] WAMP Server / MySQL is not running on port 3306!
    echo ========================================================================
    echo Gujarati: WAMP Server bandh che, pan server auto-fallback SQLite sathe
    echo           chalu thashe, etle website tarat open thai jashe!
    echo.
    echo Jo tame WAMP MySQL vaparva mangta hov:
    echo 1. Start Menu mathi "WampServer" chalu karo.
    echo 2. WAMP icon Green thay tya sudhi wait karo.
    echo ========================================================================
) else (
    echo [OK] WAMP MySQL Server is active on port 3306.
)

:: 4. Run database migrations & seed initial data
echo.
echo [4/5] Synchronizing database tables and default data...
python manage.py migrate --noinput >nul 2>&1
python manage.py seed_data >nul 2>&1
echo [OK] Database schema & default packages ready!

:: 5. Launch Server & Display All Project URLs
echo.
echo ========================================================================
echo                     * ALL PROJECT URLS / બધી જ લિંક *
echo ========================================================================
echo.
echo  [ CUSTOMER WEBSITE PAGES / મુલાકાતીઓ માટે પેજીસ ]
echo    - Home Page:           http://localhost:5000/
echo    - Tour Packages:       http://localhost:5000/packages.html  (or /packages)
echo    - Book a Package:      http://localhost:5000/book.html      (or /book)
echo    - Plan Custom Trip:    http://localhost:5000/plan.html      (or /plan)
echo    - Photo Gallery:       http://localhost:5000/gallery.html   (or /gallery)
echo    - About Us:            http://localhost:5000/about.html     (or /about)
echo    - Contact Us:          http://localhost:5000/contact.html   (or /contact)
echo.
echo  [ CUSTOMER ACCOUNT & PROFILE / કસ્ટમર એકાઉન્ટ ]
echo    - Customer Login:      http://localhost:5000/login.html     (or /login)
echo    - Customer Register:   http://localhost:5000/register.html  (or /register)
echo    - Instagram Profile:   http://localhost:5000/profile.html   (or /profile)
echo.
echo  [ ADMIN PORTALS / એડમિન પોર્ટલ ]
echo    - Custom Admin Login:  http://localhost:5000/admin-login.html (or /admin-login)
echo    - Custom Admin Panel:  http://localhost:5000/admin.html       (or /admin)
echo    - Django SuperAdmin:   http://localhost:5000/django-admin/
echo.
echo  [ ADMIN CREDENTIALS / એડમિન લૉગિન વિગત ]
echo    - Admin Email:         admin@deluxtour.com
echo    - Django Username:     admin
echo    - Password:            Admin@123
echo.
echo  [ DATA & EXPORT APIS ]
echo    - Packages API:        http://localhost:5000/api/packages
echo    - Export Bookings CSV: http://localhost:5000/api/admin/export/bookings
echo.
echo ========================================================================
echo  Server is starting on http://localhost:5000
echo  Press Ctrl+C to stop the server anytime.
echo ========================================================================
echo.

:: Automatically open default browser after brief delay
start "" http://localhost:5000/

:: Run Django server
python manage.py runserver 0.0.0.0:5000
pause
