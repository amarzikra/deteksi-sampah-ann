Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
shell.Run "cmd /c py -3.11 -m streamlit run apk_sampah_suara.py --server.headless true", 0, False
WScript.Sleep 6000
shell.Run "http://localhost:8501/#deteksi", 1, False
