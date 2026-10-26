@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Классный монитор - онлайн (туннель)

REM ====================================================================
REM  Запуск для учеников в ДРУГИХ городах (через интернет).
REM  Положи этот файл рядом с TeacherServer.exe и запусти двойным кликом.
REM  Он сам скачает программу-туннель, поднимет сервер и покажет
REM  публичную ссылку https://...trycloudflare.com
REM ====================================================================

if not exist TeacherServer.exe (
  echo ОШИБКА: рядом нет TeacherServer.exe. Положи этот файл в ту же папку.
  pause
  exit /b
)

if not exist cloudflared.exe (
  echo Скачиваю программу-туннель (один раз)...
  curl -L -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
  if not exist cloudflared.exe (
    echo Не удалось скачать туннель. Проверь интернет и запусти снова.
    pause
    exit /b
  )
)

echo Запускаю сервер... (в его окне смотри КЛАСС-КОД)
start "Классный сервер" TeacherServer.exe
timeout /t 4 >nul

echo.
echo ====================================================================
echo  Сейчас появится ПУБЛИЧНАЯ ССЫЛКА вида https://XXXX.trycloudflare.com
echo  1) найди строку с trycloudflare.com ниже;
echo  2) дай эту ссылку ученику (он вписывает её вместо адреса);
echo  3) впиши её же в приложении на телефоне;
echo  4) класс-код возьми из ОКНА СЕРВЕРА.
echo  Это окно НЕ закрывать, пока идёт урок.
echo ====================================================================
echo.

cloudflared.exe tunnel --url http://localhost:8080
pause
