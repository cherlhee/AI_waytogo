::press.bat; real code;
::----- -----


:: Set the root path to your Anaconda installation
::set root=C:\Users\JCR1\anaconda3
set root=C:\Users\user\anaconda3


:: Call conda.bat to initialize conda
CALL %root%\condabin\conda.bat activate megacom

:: Change to the directory where your script is located
:: cd /d D:\__PROJECTed\__KIS\__AI\megacom
::cd /d D:\__PROJECTed\__KIS\__AI\megacom\AI_waytogo\GUI
cd C:\CHERLHEE\AI_waytogo\GUI


:: Run the Python script
python megacom.py

:: Keep the window open to see output
pause

