Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
userProfile = WshShell.ExpandEnvironmentStrings("%USERPROFILE%")
scriptDir = userProfile & "\Desktop\.cursor"
pythonwPath = userProfile & "\AppData\Local\Programs\Python\Python313\pythonw.exe"
If Not fso.FileExists(pythonwPath) Then pythonwPath = "pythonw"
cmd = """" & pythonwPath & """ """ & scriptDir & "\data_pc_watchdog.py"" --script-dir """ & scriptDir & """"
WshShell.Run cmd, 0, False
