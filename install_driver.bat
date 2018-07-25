@ECHO OFF
setlocal
set DRIVER_FOLDER=%~dp0
set DRIVER_NAME="{{cookiecutter.project_slug}}"
set QS_PYTHON_REGEXP="^2.7.*"
set QS_PYTHON="%DRIVER_FOLDER%\..\..\python"
set DRIVER_PYTHON="%DRIVER_FOLDER%\Scripts\python.exe"
set PACKAGES="%DRIVER_FOLDER%\packages"

for /F %%x in ('dir /b %QS_PYTHON%') do echo %%x|findstr %QS_PYTHON_REGEXP%>nul&&set QS_PYTHON=%QS_PYTHON%\%%x\python.exe&&goto INSTALL_VIRTUALENV

:INSTALL_VIRTUALENV
if not exist %DRIVER_PYTHON% %QS_PYTHON% -m virtualenv --system-site-packages "%DRIVER_FOLDER%\"
if exist %PACKAGES% %DRIVER_PYTHON% -m pip install -r "%DRIVER_FOLDER%\requirements.txt" --no-index -f "%PACKAGES%"
if not exist %PACKAGES% %DRIVER_PYTHON% -m pip install -r "%DRIVER_FOLDER%\requirements.txt"
copy "%DRIVER_FOLDER%\driver_exe_template" "%DRIVER_FOLDER%\..\%DRIVER_NAME%.exe"
endlocal