@echo off
REM Script para el Programador de Tareas de Windows - Evangelio del Dia
REM Corre el pipeline completo y guarda un log con la fecha, para poder
REM revisar despues si algo fallo.
REM
REM Se dispara con el desencadenador "Al iniciar sesion" (en vez de una
REM hora fija), asi que puede llegar a correr varias veces el mismo dia
REM si abris la notebook mas de una vez. Por eso primero revisamos si
REM el video de HOY ya existe, y si es asi, no volvemos a generar/subir
REM todo de nuevo.

cd /d "C:\VivaLaFe\evangelio_del_dia_proyecto\mensajes_virgen"

if not exist "logs" mkdir "logs"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set FECHA_LOG=%%i

if exist "output\video_%FECHA_LOG%.mp4" (
    echo [%date% %time%] El video de hoy ^(%FECHA_LOG%^) ya existe. No se vuelve a correr. >> "logs\log_%FECHA_LOG%.txt"
    exit /b 0
)

echo ============================================== >> "logs\log_%FECHA_LOG%.txt"
echo Ejecucion iniciada: %date% %time% >> "logs\log_%FECHA_LOG%.txt"
echo ============================================== >> "logs\log_%FECHA_LOG%.txt"

python generar_todo.py >> "logs\log_%FECHA_LOG%.txt" 2>&1

echo. >> "logs\log_%FECHA_LOG%.txt"
echo Ejecucion finalizada: %date% %time% >> "logs\log_%FECHA_LOG%.txt"

