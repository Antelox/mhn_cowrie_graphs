import cowrie_update_config as conf
import pymongo
import sqlite3
import sys
import pymysql


def usage():
    """Function to print how to use the script"""
    print "Python Script to create the cowrie databases, username and passwords to keep the log data centralized, " \
          "run it every time you deploy a new cowrie sensor."
    print "Usage:\n" \
          "\tpython cowrie_update_mysql.py [-h|clean]\n" \
          "\t\tUse -h to print this help\n" \
          "\t\tUse \"clean\" without quotes to clean the cowrie databases of sensors that are not deployed anymore\n" \
          "\t\tIf no option is selected the script will create the new MySQL databases, " \
          "username and passwords for each deployed cowrie sensor"


def sanitizeString(string):
    return string.replace('-', '_')


def getMongoCowrieData():
    """Function to connect to the mongodb and retrieve the cowrie sensor identifiers and secrets"""
    try:
        client = pymongo.MongoClient('mongodb://' + conf.MONGO_HOST + ':' + str(conf.MONGO_PORT))
    except pymongo.errors.ConnectionFailure:
        print ('Error Connecting to the database...')
        print ('Check the cowrie_update_config file to change the configuration...')
        sys.exit(1)
    db = client.hpfeeds
    auth_keys = db.auth_key
    return auth_keys.find({"publish": ["cowrie.sessions"]}, {"identifier": 1, "secret": 1, "_id": 0})


def getSensorIP(ident):
    """Function to get the ip address of the sensor from sqlite3 db"""
    try:
        conn = sqlite3.connect(conf.SQLITE_DB)
    except sqlite3.OperationalError as e:
        print e
        sys.exit(1)
    cur = conn.cursor()
    sql = "SELECT COUNT(*) FROM sensors WHERE uuid = '%s'" % ident
    cur.execute(sql)
    if cur.fetchone()[0] != 0:
        sql = "SELECT ip FROM sensors WHERE uuid = '%s'" % ident
        cur.execute(sql)
        conn.commit()
        ip = cur.fetchone()[0]
        conn.close()
        return ip
    else:
        conn.close()
        print 'The sensor was not found on mhn.db and the ip address could not be determined...'
        sys.exit(1)


def getMySQLCowrieData():
    """Function to connect to the MySQL db and retrieve the cowrie databases already created"""
    try:
        conn = pymysql.connect(host=conf.MYSQL_HOST, port=conf.MYSQL_PORT, user=conf.MYSQL_USER, passwd=conf.MYSQL_PWD)
    except pymysql.MySQLError as e:
        print e.args[1]
        sys.exit(1)
    cur = conn.cursor()
    sql = "SHOW DATABASES"
    cur.execute(sql)
    cowrieDbs = []
    for (db,) in cur:
        if db.startswith('cowrie'):
            cowrieDbs.append(db)
    cur.close()
    conn.close()
    return cowrieDbs


def createCowrieDb(db, pwd, ipAddr):
    """Function to create the Cowrie Database, the username and password"""
    try:
        conn = pymysql.connect(host=conf.MYSQL_HOST, port=conf.MYSQL_PORT, user=conf.MYSQL_USER, passwd=conf.MYSQL_PWD)
    except pymysql.MySQLError as e:
        print e.args[1]
        sys.exit(1)
    cur = conn.cursor()
    sql = "CREATE DATABASE IF NOT EXISTS %s" % db
    cur.execute(sql)
    sql = "CREATE USER 'cowrie'@'%s' IDENTIFIED BY '%s'" % (ipAddr, pwd)
    cur.execute(sql)
    sql = "GRANT ALL ON %s.* TO 'cowrie'@'%s' IDENTIFIED BY '%s'" % (db, ipAddr, pwd)
    cur.execute(sql)
    sql = "FLUSH PRIVILEGES"
    cur.execute(sql)
    cur.close()
    conn.close()
    createCowrieTables(db)


def createCowrieTables(database):
    """Function to create the tables on the Cowrie Databases"""
    try:
        conn = pymysql.connect(host=conf.MYSQL_HOST, port=conf.MYSQL_PORT, user=conf.MYSQL_USER, passwd=conf.MYSQL_PWD, db=database)
    except pymysql.MySQLError as e:
        print e.args[1]
        sys.exit(1)
    cur = conn.cursor()
    f = open(conf.COWRIE_SQL, 'r')
    sql = ''
    for line in f:
        if not line.endswith(';\n'):
            sql = sql + line[:-1]
        else:
            sql = sql + line[:-2]
            cur.execute(sql)
            sql = ''
    cur.close()
    conn.close()


def dropMySQLDb(database):
    """Function to drop Cowrie Databases that are no longer used"""
    try:
        conn = pymysql.connect(host=conf.MYSQL_HOST, port=conf.MYSQL_PORT, user=conf.MYSQL_USER, passwd=conf.MYSQL_PWD)
    except pymysql.MySQLError as e:
        print e.args[1]
        sys.exit(1)
    cur = conn.cursor()
    sql = 'DROP DATABASE %s' % database
    cur.execute(sql)
    cur.close()
    conn.close()


def dropMySQLUser(ip):
    """Function to drop Cowrie Users that are no longer used"""
    try:
        conn = pymysql.connect(host=conf.MYSQL_HOST, port=conf.MYSQL_PORT, user=conf.MYSQL_USER, passwd=conf.MYSQL_PWD)
    except pymysql.MySQLError as e:
        print e.args[1]
        sys.exit(1)
    cur = conn.cursor()
    sql = "DROP USER 'cowrie'@'%s'" % ip
    cur.execute(sql)
    cur.close()
    conn.close()


def getMySQLCowrieUsers():
    """Get the cowrie users configured on MySQL"""
    try:
        conn = pymysql.connect(host=conf.MYSQL_HOST, port=conf.MYSQL_PORT, user=conf.MYSQL_USER, passwd=conf.MYSQL_PWD)
    except pymysql.MySQLError as e:
        print e.args[1]
        sys.exit(1)
    cur = conn.cursor()
    sql = "SELECT COUNT(*) FROM mysql.user WHERE User = 'cowrie'"
    cur.execute(sql)
    if cur.fetchone()[0] != 0:
        sql = "SELECT Host FROM mysql.user WHERE User = 'cowrie'"
        cur.execute(sql)
        userCreated = []
        for (host,) in cur.fetchall():
            userCreated.append(host)
        cur.close()
        conn.close()
        return userCreated
    else:
        cur.close()
        conn.close()
        print "There are no cowrie Users configured on MySQL"
        sys.exit(1)


def getHostsSQLite():
    """Function to get all the ip address of the sensor from sqlite3 db"""
    try:
        conn = sqlite3.connect(conf.SQLITE_DB)
    except sqlite3.OperationalError as e:
        print e
        sys.exit(1)
    cur = conn.cursor()
    sql = "SELECT COUNT(*) FROM sensors WHERE honeypot = 'cowrie'"
    cur.execute(sql)
    sensorsRegistered = []
    if cur.fetchone()[0] != 0:
        sql = "SELECT ip FROM sensors WHERE honeypot = 'cowrie'"
        cur.execute(sql)
        conn.commit()
        for (ip,) in cur.fetchall():
            sensorsRegistered.append(ip)
        conn.close()
        return sensorsRegistered
    else:
        conn.close()
        print 'There are not cowrie sensors on mhn.db.'
        return sensorsRegistered


def cleanMySQLDb():
    """Function to clean the Cowrie Database, the username and password"""
    cowrieSensorReg = getMongoCowrieData()
    cowrieDbReg = []
    for sensor in cowrieSensorReg:
        cowrieDbReg.append(sanitizeString('cowrie-' + sensor['identifier']))
    cowrieDbCreated = getMySQLCowrieData()
    for database in cowrieDbCreated:
        if database not in cowrieDbReg:
            dropMySQLDb(database)
            print "MySQL Database %s was dropped." % database
    usersOnMySQL = getMySQLCowrieUsers()
    activeSensors = getHostsSQLite()
    usersToDel = list(set(usersOnMySQL) - set(activeSensors))
    for host in usersToDel:
        dropMySQLUser(host)
        print "MySQL User cowrie@%s dropped" % host


def main():
    """Main Function"""
    if len(sys.argv) == 1:
        cowrieSensorReg = getMongoCowrieData()
        cowrieDbCreated = getMySQLCowrieData()
        for sensor in cowrieSensorReg:
            if sanitizeString('cowrie-' + sensor['identifier']) not in cowrieDbCreated:
                ipAddr = getSensorIP(sensor['identifier'])
                database = sanitizeString('cowrie-' + sensor['identifier'])
                password = sensor['secret']
                createCowrieDb(database, password, ipAddr)
                print 'Created MySQL DB named %s' % database
                print 'Created a username cowrie with a password %s and granted permissions from host %s' % (password, ipAddr)
            else:
                print 'MySQL DB named %s already exists!!!' % sanitizeString('cowrie-' + sensor['identifier'])
    elif len(sys.argv) == 2:
        if sys.argv[1] == '-h':
            usage()
        elif sys.argv[1].lower() == 'clean':
            cleanMySQLDb()
    else:
        usage()


if __name__ == "__main__":
    main()


__author__ = 'Antelox'