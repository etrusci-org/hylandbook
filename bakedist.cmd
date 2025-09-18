@echo off

:: bake hylandbook.exe

pyinstaller ^
    --distpath "./dist" ^
    --workpath "./.build" ^
    --specpath "./.build" ^
    --icon "../app.ico" ^
    --name hylandbook ^
    --console ^
    --clean ^
    --onefile ^
    "./hylandbook/__main__.py"

certutil ^
    -hashfile "./dist/hylandbook.exe" ^
    SHA256 ^
    | findstr /v "hash" ^
    > "./dist/hylandbook.exe.sha256"


:: bake update_*_database_to_next.exe

pyinstaller ^
    --distpath "./dist" ^
    --workpath "./.build" ^
    --specpath "./.build" ^
    --icon "../app.ico" ^
    --name update_v1.0.0_database_to_next ^
    --console ^
    --clean ^
    --onefile ^
    "./hylandbook/update_v1.0.0_database_to_next.py"

certutil ^
    -hashfile "./dist/update_v1.0.0_database_to_next.exe" ^
    SHA256 ^
    | findstr /v "hash" ^
    > "./dist/update_v1.0.0_database_to_next.exe.sha256"
