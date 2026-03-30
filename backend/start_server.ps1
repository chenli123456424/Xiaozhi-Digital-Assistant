param(
    [string]$Backend = "d:\资料\实习材料\项目经历\Xiaozhi-Digital-Assistant\backend"
)

Set-Location -Path $Backend
& ".\venv\Scripts\python.exe" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
