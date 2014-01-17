#!/bin/bash
mysql -u comoto --password=you_arent_so_lucky -e "drop table migrate_version;" comoto
paster drop_sql development_cemeyer2_local_mysql.ini
paster setup-app development_cemeyer2_local_mysql.ini 
python manage_migrations_development_cemeyer2_mysql.py version_control
python manage_migrations_development_cemeyer2_mysql.py upgrade
