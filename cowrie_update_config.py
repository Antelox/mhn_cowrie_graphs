# Sqlite3 DB configuration
SQLITE_DB = '/opt/mhn/server/mhn.db'

# Mongo DB configuration
MONGO_HOST = 'localhost'
MONGO_PORT = 27017

# MySQL DB configuration
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PWD = 'password'

# Cowrie sql file path
COWRIE_SQL = '/opt/mhn/scripts/cowrie_mysql.sql'

# Graph configuration
COWRIE_GRAPH_PATH = '/opt/mhn/server/mhn/static/img/cowrie_graphs/'
COWRIE_GRAPH_RES = 100
COWRIE_GRAPH_FORMAT = 'png'
COWRIE_FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
COWRIE_FONT_SIZE = 48
COWRIE_THUMB_FACTOR = 2

#You could choose from bmh, dark_background, fivethirtyeight, ggplot or grayscale, visit matplotlib documentation for more information
COWRIE_STYLE = 'ggplot'

__author__ = 'Antelox'
