# To setup backend for Obmennik, make next steps

## Clone the repository
```
git clone https://github.com/DiazzzU/obmennik_backend
```

## Setup database 
```
docker-compose up
```

## Install requirements
```
pip install -r requirements.txt
```

## Make migrations and Run server
```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 8000
```