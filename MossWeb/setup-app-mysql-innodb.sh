#!/bin/bash
mysql -u comoto -pdooooodthisisntthepassword -e "drop database comoto2; create database comoto2;"
paster setup-app development_cemeyer2_local_mysql_innodb.ini 
python manage_migrations_development_innodb.py version_control
python manage_migrations_development_innodb.py upgrade
