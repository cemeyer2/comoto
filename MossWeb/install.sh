sudo apt-get install python-setuptools python-svn python-ldap python-pygraphviz python-matplotlib python-pygments
sudo python setup.py develop

echo "CREATE USER 'comoto'@'localhost' IDENTIFIED BY 'got_rid_of_the_real_password'; CREATE DATABASE comoto; CREATE DATABASE comoto2; GRANT ALL PRIVILEGES ON *.* to 'comoto'@'localhost';" > tmp.sql
mysql -u root -p < tmp.sql
rm tmp.sql

./setup-app-mysql-innodb.sh
