@cd %~dp0
@pipenv install --skip-lock
@pipenv run pip install pyinstaller
@pipenv run pip install -r requirements.txt
@pipenv run pyinstaller -i "./favicon.ico" --noconfirm --onefile "./CMLD.py"
@pause