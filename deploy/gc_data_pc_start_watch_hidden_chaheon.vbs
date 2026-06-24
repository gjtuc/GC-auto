Set WshShell = CreateObject("WScript.Shell")
userProfile = WshShell.ExpandEnvironmentStrings("%USERPROFILE%")
scriptDir = userProfile & "\Desktop\.cursor"
cmd = "pythonw """ & scriptDir & "\data_pc_watchdog.py"" --script-dir """ & scriptDir & """"
WshShell.Run cmd, 0, False
