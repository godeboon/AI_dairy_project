# setup_env.ps1
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8 # 한글깨지는거 방지


Write-Host "✅ 가상환경 생성 중..."
python -m venv venv

Write-Host "✅ 가상환경 활성화..."
& .\venv\Scripts\Activate.ps1

Write-Host "✅ requirements.txt 설치 중..."
pip install -r requirements.txt

Write-Host "✅ .env 로딩 및 SECRET_KEY 확인 중..."
python -c "import os; from dotenv import load_dotenv; load_dotenv(dotenv_path=os.path.abspath('.env')); print('SECRET_KEY:', os.getenv('SECRET_KEY'))"

Write-Host "✅ 모든 준비 완료! 이제 아래 명령으로 실행하세요:"
Write-Host "`nuvicorn main:app --reload`n"
