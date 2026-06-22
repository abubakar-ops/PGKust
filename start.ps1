# Start backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "c:\Users\abuba\PGkust\venv\Scripts\python.exe c:\Users\abuba\PGkust\backend\manage.py runserver"

# Start frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location c:\Users\abuba\PGkust\frontend; npm run dev"
