  @echo off
  setlocal

REM Update the firmware on SmartCard.

REM Input parameters:
REM    %1% = SmartCard IP address
REM    %2% = SmartCard operating system type
REM          (i.e. "SC3ONLY", a VxWorks OS for SC3 only
REM             or    "DUAL", the newer VxWorks OS for SC3 and SC3+)
REM    %3% = Full path to a log file

REM If the SmartCard is running a VxWorks OS for SC3 only
REM rather than the newer VxWorks OS for SC3 and SC3+,
REM then install new bootROM code before installing the
REM new OS and application firmware update.

REM MODIFICATION HISTORY:
REM 15Sep2003 KK  (Knute Kresie) Created original version
REM 17Sep2003 KK  Omit "update" optional_command parameter to msupdate
REM           to obtain default interactive update process.
REM 01Mar2004 KK  Added use of %RETURN_STATUS% to pass that to caller
REM

REM Use "~nx" to get the "fname.ext" portion of the full path in %0
  set  ID=%~nx0
  set  RETURN_STATUS=0

  set IP=%1%
  echo %ID%: IP=%IP%
  if {%IP%} NEQ {} goto :IP_OK
  echo %ID%: IP is missing
  goto error_exit

:IP_OK

  set SC3_OSTYPE=%2%
  echo %ID%: SC3_OSTYPE=%SC3_OSTYPE%
  if {%SC3_OSTYPE%} NEQ {} goto :SC3_OSTYPE_OK
  echo %ID%: SC3_OSTYPE is missing
  goto error_exit

:SC3_OSTYPE_OK

  set LOGF=%3%
  echo %ID%: LOGF=%LOGF%
  if {%LOGF%} NEQ {} goto :LOGF_OK
  echo %ID%: LOGF is missing
  goto error_exit

:LOGF_OK

REM Use single ">" below to force replacement of previous file content, if any.
REM Use       ">>" below to append to existing file or create new file if needed.

  echo %ID%: IP=%IP%                  >> %LOGF%
  echo %ID%: SC3_OSTYPE=%SC3_OSTYPE%  >> %LOGF%
  date /t  >> %LOGF%
  time /t  >> %LOGF%

  echo %ID%: ====== Set real time clock in the SmartCard .....
  echo %ID%: ====== Set real time clock in the SmartCard ..... >> %LOGF%

  @echo on
  msupdate.exe  %IP%  time
  @echo off
  echo
  echo %ID%: ERRORLEVEL=%ERRORLEVEL%           >> %LOGF%
  if %ERRORLEVEL% NEQ 0 goto error_exit 


  if {%SC3_OSTYPE%} NEQ {SC3ONLY} goto DO_FW_UPDATE

  echo %ID%: ====== Update the bootROM .....
  echo %ID%: ====== Update the bootROM ..... >> %LOGF%

  @echo on
  msupdate.exe  %IP%  bootrom
  @echo off
  echo
  echo %ID%: ERRORLEVEL=%ERRORLEVEL%           >> %LOGF%
  if %ERRORLEVEL% NEQ 0 goto error_exit 

:DO_FW_UPDATE

  echo %ID%: ====== Update the firmware (other than bootROM) .....
  echo %ID%: ====== Update the firmware (other than bootROM) ..... >> %LOGF%

REM omission of msupdate optional_command parameter implies interactive update

  @echo on
  msupdate.exe  %IP%
  @echo off
  echo
  echo %ID%: ERRORLEVEL=%ERRORLEVEL%           >> %LOGF%
  if %ERRORLEVEL% NEQ 0 goto error_exit 


  echo %ID%: Firmware update completed.  >> %LOGF%

  goto done
:error_exit

  set RETURN_STATUS=%ERRORLEVEL%
  echo %ID%: ABORTED. Firmware update NOT successful.
  echo %ID%: ABORTED. Firmware update NOT successful.  >> %LOGF%

:done

  echo %ID%: RETURN_STATUS=%RETURN_STATUS%
  echo %ID%: RETURN_STATUS=%RETURN_STATUS%  >>  %LOGF%
  echo %ID%: Ending at  >> %LOGF%
  date /t >> %LOGF%
  time /t >> %LOGF%
  echo %ID%: =====================================  >>  %LOGF%

  pause

  endlocal & set RETURN_STATUS=%RETURN_STATUS%
