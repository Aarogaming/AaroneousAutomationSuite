Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get script directory
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(scriptDir)
venvPython = projectRoot & "\.venv\Scripts\pythonw.exe"
trayScript = scriptDir & "\aas_tray.py"

' Set environment and run tray (hidden)
WshShell.CurrentDirectory = projectRoot
WshShell.Run """" & venvPython & """ """ & trayScript & """", 0, False
