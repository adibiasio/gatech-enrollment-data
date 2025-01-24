# Pyinstaller Packaging Instructions
Ensure pyinstaller is installed (via pip) and run the following command
```
pyinstaller --onefile --windowed app.py
```

Note that there may be package resolution issues with `ray`, so if needed, comment out all usage of ray in client.py before packaging. 