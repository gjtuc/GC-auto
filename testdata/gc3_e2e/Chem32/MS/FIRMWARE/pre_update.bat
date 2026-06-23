  @echo off
  setlocal

REM "pre_update.bat"
REM This script is designed to be invoked by InstallShield to do a
REM firmware-only installation (update) to the MSD SmartCard.
REM This script is written for execution by the Windows NT Command Shell
REM on a PC that does not necessarily have MSD ChemStation installed.
REM This script uses relative path names and therefore assumes the
REM script resides in the Shell's present working directory.

REM Typical invocation from within Midrosoft Windows Command Shell:
REM    call pre_update.bat IP_addr > pre_update.log  2>&1

REM   ("call" it to allow it to pass a RETURN_STATUS variable back to
REM    its parent process and do re-direction of stdout, stderr to
REM    same log file.  For more information about the special
REM    "endlocal" syntax used below and other syntax used in this script,
REM    see "Windows NT Shell Scripting", by Tim Hill,
REM    copyright 1998, MacMillan Technical Publishing.)

REM MODIFICATION HISTORY:
REM 02Mar2004 KK  (Knute Kresie) derived this from the smart3plus
REM           "publish_build.bat" script and the current
REM           msexe\msconfig.mac macro.
REM 19Apr2004 KK  Added creation of a completion STATUS_FILE having a name
REM           indicating the success or failure of this script to a parent
REM           process such as InstallShield.  Changed most messages to use
REM           short form of path name of this script.  Changed msupdate.exe
REM           error handling and checking for valid OSVtext.


REM  The following string will be automatically updated during check-in
REM  to SoftCM.

  set PGMVERS=$Id: pre_update.bat,v 1.2 2004-04-19 13:26:42-07 knute Exp $

REM  When printing the PGMVERS string, remove the 1st four characters to
REM  prevent the printed string from being modified if it is captured in a
REM  log file that is subsequently checked into SoftCM/RCS.

  echo "%~nx0: PGMVERS=%PGMVERS:~4%"

REM Initialize some variables

  set RETURN_STATUS=0

REM Define filenames like "pre_update_SUCCESS.log" or "pre_update_FAILURE.log" 
REM for communicating completion status of this script to a parent process
REM such as InstallShield.  Make sure those files do not exist initially.

  set FNAME_SUCCESS="%~n0_SUCCESS.log"
  if exist %FNAME_SUCCESS% del /F /Q %FNAME_SUCCESS%
  set FNAME_FAILURE="%~n0_FAILURE.log"
  if exist %FNAME_FAILURE% del /F /Q %FNAME_FAILURE%


  echo "%~nx0: Start date, time follow"
  date /t  &  time /t


  set IPADDR=%1%
  echo "%~nx0: IPADDR = %IPADDR%"
  if defined IPADDR goto :begin_processing
     echo "%~nx0: IPADDR (IP address) global variable is not defined!"
     goto error_exit

:begin_processing

REM === DEBUG exit ====
REM   goto error_exit

  set LOG1=pre_update_temp1.log
  set LOG2=pre_update_temp2.log
  set LOG3=pre_update_temp3.log

  msupdate.exe %IPADDR% time  >  %LOG1%  2>&1

REM parse the log file to get the OS version string.  See Tim Hill's book, p.136.

  set OSVtext=UNKNOWN
  FOR /F "tokens=4" %%I IN ('findstr /R "OS.*version" %LOG1%') DO @set OSVtext=%%I 
  echo "%~nx0: OSVtext = |%OSVtext%|"
  if %OSVtext% NEQ UNKNOWN goto OSVtext_OK
    echo "%~nx0: Not a running SmartCard at IPADDR."
    set RETURN_STATUS=11
    goto error_exit2

:OSVtext_OK

REM Parse the SmartCard OS version string to determine if it contains a "T"
REM (e.g. "1.2/22T") indicating the DUAL (SC3/SC3+) OS.
REM See sc3_type.mac for similar logic.
REM This is clumsy here because this shell does not have a string in string search. 
  echo "%~nx0: %OSVtext%" > %LOG2%
  set OStype=SC3ONLY 
  FOR /F %%I IN ('findstr "T" %LOG2%')  DO set OStype=DUAL
  if %ERRORLEVEL% NEQ 0 goto error_exit
  echo "%~nx0: OStype=%OStype%"

  call update.bat %IPADDR% %OStype% %LOG3%
  if %RETURN_STATUS% NEQ 0 goto error_exit
   
  echo "%~nx0: continuing before done:"
  set RETURN_STATUS=0
  set STATUS_FILE=%FNAME_SUCCESS%
  goto done

:error_exit

  set saved_EL=%ERRORLEVEL%
  if %saved_EL% EQU 0 goto error_exit2
    echo "%~nx0: ERRORLEVEL=%saved_EL%"
    set old_RT=%RETURN_STATUS%
    set RETURN_STATUS=%saved_EL%
    echo "%~nx0: Changing RETURN_STATUS from %old_RT% to %RETURN_STATUS%"

:error_exit2

  set STATUS_FILE=%FNAME_FAILURE%"
  echo "%~nx0: *** ABORTED ***"
   
:done

  date /t  &  time /t
  date /t  >>  %STATUS_FILE%
  time /t  >>  %STATUS_FILE%
  echo "%0: Done. RETURN_STATUS=%RETURN_STATUS%"
  echo "%0: Done. RETURN_STATUS=%RETURN_STATUS%"  >>  %STATUS_FILE%
  pause

REM The following achieves returning only the RETURN_STATUS variable into
REM the calling environment.  See Tim Hill's book, p.79-80.

  endlocal & set RETURN_STATUS=%RETURN_STATUS%
