@echo off
cd /d d:\资料\实习材料\项目经历\Xiaozhi-Digital-Assistant\backend
call venv\Scripts\activate.bat
python -m uvicorn main:app --reload
