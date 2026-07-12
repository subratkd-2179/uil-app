"""Run the MySQL initialization script against a MySQL server.

Usage:
    python init_mysql_db.py

Defaults: host=localhost, user=root, password=admin, port=3306
"""
import logging
import os
import mysql.connector
from mysql.connector import errorcode
from pathlib import Path
from dotenv import load_dotenv
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mysql_init')

ROOT = Path(__file__).resolve().parent
SQL_PATH = ROOT / 'mysql_init.sql'
load_dotenv(ROOT / '.env')

# Update these if your MySQL credentials differ
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', '127.0.0.1'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', 'admin'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'autocommit': True,
}


def run_sql_file(config, sql_file: Path):
    if not sql_file.exists():
        logger.error("SQL file not found: %s", sql_file)
        return 1

    with sql_file.open('r', encoding='utf-8') as f:
        sql = f.read()

    try:
        logger.info("Connecting to MySQL at %s:%s as user %s", config['host'], config['port'], config['user'])
        # connect without specifying database so we can CREATE DATABASE
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        logger.info("MySQL connection successful.")

        # MySQL connector does not support executescript; split statements
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except mysql.connector.Error as e:
                # Ignore 'DROP' or 'CREATE' warnings and continue
                logger.warning("Statement warning: %s", e.msg)

        cursor.close()
        conn.close()
        logger.info("MySQL initialization script executed successfully.")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Access denied: check your username/password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.error("Database does not exist and could not be created")
        else:
            logger.error("MySQL error: %s", err)
        return 2

    return 0


if __name__ == '__main__':
    rc = run_sql_file(MYSQL_CONFIG, SQL_PATH)
    sys.exit(rc)
