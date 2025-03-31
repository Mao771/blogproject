#!/bin/bash
python manage.py wait_for_db  # optional: add custom command
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
