@echo off

:: RUN FROM repo root directory

pyinstaller ^
    --distpath "./dist" ^
    --workpath "./.build" ^
    --specpath "./.build" ^
    --icon "../src/app.ico" ^
    --name hylandbook ^
    --console ^
    --clean ^
    --onefile ^
    "./src/hylandbook.py"

certutil ^
    -hashfile "./dist/hylandbook.exe" ^
    SHA256 ^
    | findstr /v "hash" ^
    > "./dist/hylandbook.exe.sha256"
