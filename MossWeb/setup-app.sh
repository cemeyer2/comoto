#!/bin/bash
rm development.db
paster setup-app development.ini
python manage_migrations_development.py version_control
python manage_migrations_development.py upgrade
