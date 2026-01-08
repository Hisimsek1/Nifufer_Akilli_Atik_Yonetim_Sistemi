@echo off
REM Nilufer Belediyesi AI Atik Yonetim Sistemi - Hizli Baslangic
REM Windows icin otomatik baslatma scripti

echo ================================================================================
echo     NILUFER BELEDIYESI - AI ATIK YONETIM SISTEMI
echo ================================================================================
echo.

REM Proje kontrolu
echo [1/3] Proje kontrol ediliyor...
python check_setup.py
if errorlevel 1 (
    echo.
    echo HATA: Proje kontrolu basarisiz!
    echo Lutfen eksik dosyalari tamamlayin.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo [2/3] Flask sunucusu baslatiliyor...
echo ================================================================================
echo.
echo   Admin Panel acilacak adres: http://localhost:5000/admin
echo   Ana Sayfa: http://localhost:5000/
echo.
echo   Sunucuyu durdurmak icin: CTRL+C
echo ================================================================================
echo.

REM Sunucuyu baslat
python app_ai.py

echo.
echo Sunucu durduruldu.
pause
