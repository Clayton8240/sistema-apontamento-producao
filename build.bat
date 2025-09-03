@echo off
cd /d %~dp0
echo Instalando/Atualizando dependencias...
pip install -r requirements.txt

echo.
echo Criando o executavel com PyInstaller...

pyinstaller --name "SistemaApontaMentor 1.2 BETA" ^
            --onefile ^
            --windowed ^
            --icon="icon.ico" ^
            --add-data "logo.png;." ^
            --add-data "db_config.json;." ^
            main.py

echo.
echo Processo concluido.
echo O executavel se encontra na pasta 'dist'.
pause