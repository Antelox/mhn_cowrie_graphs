#!/bin/bash

set -e
set -x

# Install MySQL and matplotlib dependencies
sudo apt-get update
sudo apt-get install -y python-dev mysql-server libpng12-dev libfreetype6-dev libxft-dev

# Modifying Mysql configuration to allow connection from everywhere
sed -i 's/127.0.0.1/0.0.0.0/g' /etc/mysql/my.cnf
sudo service mysql restart

# Getting MHN directory
MHN_HOME=`dirname $0`/../..
cd $MHN_HOME
MHN_HOME=`pwd`

# Installing pymysql numpy matplotlib and PILLOW
. env/bin/activate
pip install pymysql numpy matplotlib>=1.4.3 PILLOW

# Downloading the sql file to create tables on the databases
cd scripts/
sudo wget https://github.com/micheloosterhof/cowrie/raw/master/doc/sql/mysql.sql -O cowrie_mysql.sql

# Creating the directory inside mhn server app
mkdir -p $MHN_HOME/server/mhn/static/img/cowrie_graphs
sudo chown www-data:www-data $MHN_HOME/server/mhn/static/img/cowrie_graphs

# Adding the cowrie with mysql support to mhn app
cd mhn_cowrie_graphs/
sudo python insert_deploy_cowrie.py $MHN_HOME/server/mhn.db

# Creating CronTab to run the generating graph script every 5 minutes
crontab -l | grep -v  cowrie_generate_graphs.py | crontab -
crontab -l | { cat; echo "*/5 * * * * $MHN_HOME/env/bin/python $MHN_HOME/scripts/mhn_cowrie_graphs/cowrie_generate_graphs.py"; } | crontab -

# Modifying Web Application
# Modifying configuration file to add channel cowrie-mysql
if [ -f $MHN_HOME/server/config.py~ ];
then
    echo "Config.py File exists, replacing it"
    sudo mv $MHN_HOME/server/config.py~ $MHN_HOME/server/config.py
    sed -i~ '$i\    '\''cowrie-mysql'\'' : ['\''cowrie.sessions'\'']' $MHN_HOME/server/config.py
    sudo chown www-data:www-data $MHN_HOME/server/config.py
else
    sed -i~ '$i\    '\''cowrie-mysql'\'' : ['\''cowrie.sessions'\'']' $MHN_HOME/server/config.py
fi

# Removing blank lines in base.html
sed -i "/^\s*$/d" $MHN_HOME/server/mhn/templates/base.html


if [ -f $MHN_HOME/server/mhn/templates/base.html~ ];
then
    echo "Base.html File exists, replacing it"
    sudo mv $MHN_HOME/server/mhn/templates/base.html~ $MHN_HOME/server/mhn/templates/base.html
    sed -i -r "s#(<!-- Right Nav Section -->)#<!-- Right Nav Section --> \ \n                <li><a href=\"{{ url_for('kg.cowrie_graph') }}\">Cowrie-Graph</a></li>#" $MHN_HOME/server/mhn/templates/base.html
    chown www-data:www-data $MHN_HOME/server/mhn/templates/base.html
else
    sed -i -r "s#(<!-- Right Nav Section -->)#<!-- Right Nav Section --> \ \n                <li><a href=\"{{ url_for('kg.cowrie_graph') }}\">Cowrie-Graph</a></li>#" $MHN_HOME/server/mhn/templates/base.html
fi

# Registering Blueprint with Flask app
if [ -f $MHN_HOME/server/mhn/__init__.py~ ];
then
    echo "_init__.py File exists, replacing it"
    sudo mv $MHN_HOME/server/mhn/__init__.py~ $MHN_HOME/server/mhn/__init__.py
    sed -i~ '
/mhn.register_blueprint(auth)/ a\
\
from mhn.kg.views import kg\
mhn.register_blueprint(kg)
' $MHN_HOME/server/mhn/__init__.py
    sudo chown www-data:www-data $MHN_HOME/server/mhn/__init__.py
else
    sed -i~ '
/mhn.register_blueprint(auth)/ a\
\
from mhn.kg.views import kg\
mhn.register_blueprint(kg)
' $MHN_HOME/server/mhn/__init__.py
fi

#Copying blueprint and templates and changing the ownerships
cd $MHN_HOME/scripts/mhn_cowrie_graphs
mkdir -p $MHN_HOME/server/mhn/kg/
sudo cp mhn/kg/* $MHN_HOME/server/mhn/kg/
mkdir -p $MHN_HOME/server/mhn/templates/kg/
sudo cp mhn/templates/kg/* $MHN_HOME/server/mhn/templates/kg/
sudo chown -R www-data:www-data $MHN_HOME/server/mhn/kg/
sudo chown -R www-data:www-data $MHN_HOME/server/mhn/templates/kg/

#Restart uwsgi
sudo supervisorctl restart mhn-uwsgi

# Remember to run this script
echo "Remember, each time a cowrie sensor with MySQL support is installed you should run the following command:"
echo "sudo /opt/mhn/env/bin/python /opt/mhn/scripts/mhn_cowrie_graphs/cowrie_update_mysql.py"
