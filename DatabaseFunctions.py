import os.path
# Access to SQLlite as the database management system (dbms).
# Statements developed here map readily to MySQL.
import sqlite3
from sqlite3 import Error

# Save search results to disk for use by selection program.
def store_search_results(search_results):
  try:
    filename = os.path.realpath("./data/BookList.txt")
    with open(filename, "w", encoding="utf-8", errors="ignore") as file:
      for result in search_results:
        file.write(result[0] + "\n")
        file.write(result[1] + "\n")
        #file.write(result[4] + "\n")
      file.close()
  except Exception as e:
    print(e)
    exit(1)
  #########################################

# Connect to an SQLite database.
# Create the database if it does not exist at the end of the path.
# https://www.sqlitetutorial.net/sqlite-python/creating-database
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        #print("SQLite3 Version: " + sqlite3.version)
    except Error as e:
        print("\n")
        print(e)
        print("create_connection: Path does not exist to file (" + db_file + ")\n")

    return conn
#########################################

# Add a table to the database
# https://www.sqlitetutorial.net/sqlite-python/create-tables
def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)
#########################################

# Insert record into database
# https://www.sqlitetutorial.net/sqlite-python/insert
# https://www.w3resource.com/sqlite/sqlite-insert-into.php
def insert_record(conn, record):
    insertion_command = r"INSERT OR REPLACE INTO BooksIndex(Title, Author, Abstract, Link, ID) VALUES(?,?,?,?,?)"
    cur = conn.cursor()
    cur.execute(insertion_command, record)
    conn.commit()
    return cur.lastrowid
#########################################

# Display all records
# https://www.sqlitetutorial.net/sqlite-python/sqlite-python-select
def display_all_records(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM BooksIndex")
    rows = cur.fetchall()
    for row in rows: print(row)
#########################################

# Parse words and phrases.
def parseInput(words_phrases):
    words_phrases = words_phrases.strip()
    if len(words_phrases) == 0: words_phrases =  []
    else:
      words_phrases = words_phrases.split(",")
      for i in range (len(words_phrases)):
        if len(words_phrases[i]) < 3: words_phrases[i] = "*"
      if "*" in words_phrases: words_phrases.remove("*")
      if len(words_phrases) == 0: print("Words and phrases must be at least three characters long")
      for w in range(len(words_phrases)):
        words_phrases[w] = words_phrases[w].replace("\'", '')
        words_phrases[w] = words_phrases[w].replace('\"', '')
        words_phrases[w] = words_phrases[w].strip()
    return words_phrases

# Retrieve selected records from the database
# https://www.sqlitetutorial.net/sqlite-python/sqlite-python-select
def query_database(conn, stack_search_include, stack_search_exclude):
    query = "SELECT * FROM BooksIndex WHERE (("
    stack_search_include = parseInput(stack_search_include)
    if len(stack_search_include) > 0:
      query += "Title LIKE \'%" + stack_search_include[0] + "%\'"
      for word in stack_search_include[1:]:
        query += "AND Title LIKE \'%" + word + "%\'"
      query += ") OR (Abstract LIKE \'%" + stack_search_include[0] + "%\'"
      for word in stack_search_include[1:]:
        query += " AND Abstract LIKE \'%" + word + "%\'"
      query += "))"

    stack_search_exclude = parseInput(stack_search_exclude)
    if len(stack_search_exclude) > 0:
      if len(stack_search_include) > 0: query += " AND "
      query += "NOT (("
      query += "Title LIKE \'%" + stack_search_exclude[0] + "%\'"
      for word in stack_search_exclude[1:]:
        query += " OR Title LIKE \'%" + word + "%\'"
      query += ") OR (Abstract LIKE \'%" + stack_search_exclude[0] + "%\'"
      for word in stack_search_exclude[1:]:
        query += " OR Abstract LIKE \'%" + word + "%\'"
      query += "))"

    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchall()
 #########################################

# Close the database
def close_connection(conn):
    if conn is not None:
        conn.close()
        conn = None
    return conn
#########################################
