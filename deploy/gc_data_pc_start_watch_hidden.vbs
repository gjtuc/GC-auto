Set WshShell = CreateObject("WScript.Shell")
userProfile = WshShell.ExpandEnvironmentStrings("%USERPROFILE%")
cmd = "cmd /c """ & userProfile & "\gc-data-pc\gc_data_pc_watch_loop.bat"""
WshShell.Run cmd, 0, False
