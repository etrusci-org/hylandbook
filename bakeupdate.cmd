@echo off

:: RUN FROM repo root directory

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
