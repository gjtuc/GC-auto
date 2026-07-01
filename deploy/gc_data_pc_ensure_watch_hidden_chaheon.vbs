Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
userProfile = WshShell.ExpandEnvironmentStrings("%USERPROFILE%")
scriptDir = userProfile & "\Desktop\.cursor"
pythonwPath = userProfile & "\AppData\Local\Programs\Python\Python313\pythonw.exe"
If Not fso.FileExists(pythonwPath) Then pythonwPath = "pythonw"
wifiCmd = """" & pythonwPath & """ """ & scriptDir & "\data_pc_wifi_autoconnect.py"" --script-dir """ & scriptDir & """"
ensureCmd = """" & pythonwPath & """ -m data_pc_runtime --script-dir """ & scriptDir & """ --ensure-once"
WshShell.Run wifiCmd, 0, True
WshShell.Run ensureCmd, 0, True
