@echo off

:: RUN FROM repo root directory

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
