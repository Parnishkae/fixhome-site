' Запуск «Мисы» как приложения — без окна консоли.
' Двойной клик по этому файлу. Можно сделать ярлык на рабочий стол.
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = scriptDir

pyw = """" & scriptDir & "\.venv\Scripts\pythonw.exe"""
If Not fso.FileExists(scriptDir & "\.venv\Scripts\pythonw.exe") Then
    MsgBox "Сначала запусти install.bat", vbExclamation, "Миса"
    WScript.Quit
End If

' 0 = скрытое окно (консоли не будет), False = не ждать завершения
sh.Run pyw & " -m assistant.app", 0, False
