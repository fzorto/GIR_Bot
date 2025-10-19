@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

REM ========= CONFIGURA ESTAS 2 VARIABLES =========
set "PROJECT_DIR=C:\Users\ferna\OneDrive\Desktop\feed-cenaos"
set "REMOTE_URL=https://github.com/fzorto/GIR_Bot.git"
REM ==============================================

REM 1) Ir a la carpeta del proyecto
cd /d "%PROJECT_DIR%" || (echo [ERROR] No se pudo ir a %PROJECT_DIR% & pause & exit /b 1)

REM 2) Detectar Python
set "PY_CMD=python"
%PY_CMD% -c "import sys" 2>nul 1>nul || set "PY_CMD=py -3"
%PY_CMD% -c "import sys" 2>nul 1>nul || (
  echo [ERROR] Python no encontrado. Instala Python o agrega 'python' o 'py -3' al PATH.
  pause
  exit /b 1
)

REM 3) Generar feed.xml (usa el script sin dependencias externas)
if not exist "feed_cenaos.py" (
  echo [ERROR] No se encontro feed_cenaos.py en %CD%
  pause
  exit /b 1
)
%PY_CMD% "feed_cenaos.py"
if errorlevel 1 (
  echo [ERROR] El script feed_cenaos.py fallo.
  pause
  exit /b 1
)
if not exist "feed.xml" (
  echo [ERROR] No se genero feed.xml
  pause
  exit /b 1
)

REM 4) Inicializar git si es la primera vez
if not exist ".git" (
  echo [INFO] Inicializando repositorio Git...
  git init || (echo [ERROR] git init fallo & pause & exit /b 1)
  git branch -M main
  git add feed.xml
  git commit -m "init: primer feed" || (echo [ERROR] git commit fallo & pause & exit /b 1)
  git remote add origin "%REMOTE_URL%" || (echo [ERROR] git remote add fallo & pause & exit /b 1)
) else (
  REM 5) Actualizar cambios
  git add feed.xml
  git commit -m "chore(feed): update %DATE% %TIME%" 1>nul 2>nul
  if errorlevel 1 (
    echo [INFO] No hay cambios nuevos en feed.xml (nada que commitear).
  )
)

REM 6) Subir a GitHub
git push -u origin main
if errorlevel 1 (
  echo.
  echo [ERROR] git push fallo. Verifica:
  echo   - Que el REMOTE_URL sea correcto: %REMOTE_URL%
  echo   - Que hayas iniciado sesion (GitHub te pedira en el navegador)
  echo.
  pause
  exit /b 1
)

echo.
echo ✅ Listo: feed.xml actualizado y publicado en GitHub.
echo Si ya activaste GitHub Pages, tu RSS estara disponible en:
echo   https://fzorto.github.io/GIR_Bot/feed.xml  (ajusta segun tu repo)
echo.
pause
exit /b 0