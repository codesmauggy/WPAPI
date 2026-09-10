# Check Installed Versions
python --version
node --version
npm --version
git --version
docker --version

# venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# if execution-policy error
#Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip
python --version
pip --version

# Install our initial backend packages
pip install django djangorestframework python-dotenv requests psycopg[binary]
django-admin --version

# Backend
mkdir backend
.\.venv\Scripts\Activate.ps1
cd backend
python manage.py runserver

# django project
django-admin startproject config .

# django app
python manage.py startapp whatsapp

# Clean Project
python manage.py clean_project
# Delete Datebase
rm -r db.sqlite3
# Start Frest Project and Database
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
# Start Backend
python manage.py runserver

# cloudflared tunnel
cloudflared tunnel --url http://127.0.0.1:8000
# url:- https://contract-healing-vessel-angels.trycloudflare.com 

# After Adding Templates
python manage.py sync_whatsapp_templates

# Token Check
curl.exe -G "https://graph.facebook.com/v26.0/1323610190832852" ` -H "Authorization: Bearer EAANOLrzKQX8BSaZB7N7ZBfvzy4uS95d3HuSMLS7YugH2d7zkRIFfGnxRdo84J7yJi3y6ZB3BGyjsVGas9vSZBFLdKxKZCPrYYjgkrggy89cUCkTgFzVxZBdlF7Ghnf0dsW6BRw2FLwEq46hvJZBqmSraWhUZATfdtr0ZB0YNWdnvRLnOOGmxQ6aoP4kyktfxTAArdr8li1VwzDB9ObMIGH0akYEIU2ZCN594NtMfbkOXsZB6hEyVcTFJvSRy1OECwwu6IPnZA6n00j2YfmoU2YPVlW64H1KaIqQLcAhHpwZDZD" `--data-urlencode "fields=id,display_phone_number,verified_name,quality_rating"

# Docker
# New Container
docker run -d `
  --name wpapi-redis `
  -p 6379:6379 `
  redis:7-alpine
# Check the stopped container
docker ps -a
# Run
docker start wpapi-redis
docker ps
docker exec wpapi-redis redis-cli ping

# Start/Restart Celery
celery -A config worker --loglevel=INFO --pool=solo
celery -A config inspect registered


# Zipping Project
& "C:\Program Files\7-Zip\7z.exe" a -tzip ".\wp_api_zip.zip" ".\wp_api\*" `
  "-xr!node_modules" `
  "-xr!.venv" `
  "-xr!__pycache__" `
  "-xr!.git" `
  "-xr!dist" `
  "-xr!build" `
  "-xr!db.sqlite3" `
  "-x!.env"