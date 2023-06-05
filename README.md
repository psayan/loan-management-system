Pre-Requisites: Python3.7 or any other higher python version

Start up using virtualenv 
    - Start the virtualenv (based on your OS)
        For Linux only create virtualenv:
            - virtualenv -p /usr/bin/python3.10 .venv
              source .venv/bin/activate
    - Install Dependencies:
        - pip install -r requirements.txt
    - Create django-project and django-app
        - django-admin startproject lms
        - python manage.py startapp api
    - Make database changes
        - python manage.py makemigrations
        - python manage.py migrate
    - Run Server
        - python manage.py runserver

        
