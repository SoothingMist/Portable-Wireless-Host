
from flask import Flask, render_template, request, redirect, url_for
import os, time
import requests
import DatabaseFunctions
from pathlib import Path


# Configure this Flask application.
app = Flask(__name__)


# Location of the database
databaseFilename = "./static/Data/BookIndex.db"


# Define a User-Agent header to identify this program's user.
# For example header variables and values, see
# https://developers.eveonline.com/api-explorer#/operations/GetIndustrySystems.
headers = {
    "X-Compatibility-Date": "2025-12-16",
    "Accept-Language": "en",
    "User-Agent": "BookDownloads (peter_raeth@juno.com)",
    "Accept": "",
    "If-Modified-Since": "",
    "If-None-Match": "",
    "X-Tenant": ""
}


# Class holding a book's search results.
class SearchResults:
  def __init__(self, Title, Abstract, Link):
    self.Title = Title
    self.Abstract = Abstract
    self.Link = Link


# Touch a url to see if it is valid.
# Nothing is downloaded here.
def check_link(url):
  try:
    # HEAD request only fetches headers (faster than GET)
    response = requests.head(url, allow_redirects=True, headers=headers)
    # Status code 200 means the page exists and is reachable
    return response.status_code == 200
  except requests.RequestException: # handles connection errors, timeouts, etc
    return False


# Creates a link from a Project Gutenberg book ID.
def Make_PG_Link(ID):
  fileFormat = "pdf"
  htmlLink = f"https://gutenberg.org/files/{id}/{id}-pdf.pdf"
  valid = check_link(htmlLink)
  if not valid:
    fileFormat = "mobi"
    htmlLink = f"https://www.gutenberg.org/ebooks/{id}.kf8.images"
    valid = check_link(htmlLink)
    if not valid:
      fileFormat = "epub"
      htmlLink = f"https://www.gutenberg.org/ebooks/{id}.epub.images"
      valid = check_link(htmlLink)
      if not valid:
        fileFormat = "txt"
        htmlLink = f"https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"
        valid = check_link(htmlLink)
        if not valid:
          fileFormat = "txt"
          htmlLink = f"https://www.gutenberg.org/ebooks/{id}.txt.utf-8"
          valid = check_link(htmlLink)
          if not valid:
            htmlLink = None
            fileFormat = None
  return htmlLink, fileFormat


# Downloads all selected books.
def download_selected_books(book_list):
  # Multiple program runs and multiple search/select/download
  # are persistent and cumulative. A header is placed at the top
  # of the html file for the very first.
  file_path = Path("./static/Books/Catalog.html")
  if not file_path.is_file():
    with open("./static/Books/Catalog.html", "a", encoding='utf-8', errors='ignore') as catalogHtml:
      header = \
        """
          <!DOCTYPE html>
          <html lang="en">
          <body>

              <h1>Hosted Books</h1>

              <hr>

              <p><i>
                  Click the linked title to access a specific book.
              </i></p>

        """
      catalogHtml.write(header + "\n")

  # Download each selected book.
  # Update the catalog files.
  with open("./static/Books/Catalog.txt", "a", encoding='utf-8', errors='ignore') as catalogText:
    with open("./static/Books/Catalog.html", "a", encoding='utf-8', errors='ignore') as catalogHtml:
      for book in book_list:
        title_index = book.find("',")
        title = book[2 : title_index]
        link_index = book.find("',", title_index+4)
        link = book[title_index+4 : link_index]
        abstract = book[link_index+4 : len(book)-2]
        if not link.endswith(".pdf"):
          link_index = link.find("_")
          if link[:link_index] == "PG":
            link, fileFormat = Make_PG_Link(link[link_index+1:])
          else:
            link = None
            fileFormat = None
        else: fileFormat = "pdf"
        if link is not None:
          title = title.replace(",", "")
          title = title.replace(".", "")
          title = title.replace(":", "")
          title = title.replace('_', "")
          title = title.strip()
          title_displayed = title
          title = title.replace(' ', '_')
          filename = os.path.abspath("./static/Books/" + title + "." + fileFormat)
          if len(filename) > 255:
            print(f"File not salvageable: {filename}")
          else:
            file_path = Path(filename)
            if not file_path.is_file():
              time.sleep(3)
              response = requests.get(link, allow_redirects=True, headers=headers)
              if response.status_code == 200 and len(response.content) > 0:
                with open(filename, "wb") as exportFile:
                  exportFile.write(response.content)
                entry = f"<p style=\"font-size:20px\"><a href=\"{title}.{fileFormat}\" target=\"_blank\" " \
                        + "rel=\"noopener\">" \
                        + title_displayed + "</a></p>\n" \
                        + abstract + "<br><br>\n\n"
                catalogHtml.write(entry)
                catalogText.write(title_displayed + "\n")
                catalogText.write(abstract + "\n")
                catalogText.write(f"{title}.{fileFormat}\n")


# Displays the homepage with unchecked boxes.
@app.route('/')
def index():
  return render_template('index.html', items=FoundTheseBooks)


# Search through the catalog of books.
@app.route('/search', methods=['POST'])
def search_catalog():
  # Get the user's input
  search_results = []
  stack_search_include = request.form['stack_search_include']
  stack_search_exclude = request.form['stack_search_exclude']
  # Connect to the database
  databaseConnection = DatabaseFunctions.create_connection(databaseFilename)
  if databaseConnection is None:
    search_results.append(SearchResults("Cannot Search. Database is missing.","", ""))
  else:
    # Query the database
    database_records = DatabaseFunctions.query_database(databaseConnection, stack_search_include, stack_search_exclude)
    if len(database_records) == 0:
      search_results.append(SearchResults("Search yielded no results.","", ""))
    else:
      for record in database_records:
        search_results.append(SearchResults(f"{record[0]}",f"{record[1]}", f"{record[2]}"))

    # Close the database
    DatabaseFunctions.close_connection(databaseConnection)
  return render_template('index.html', items=search_results)


# Downloads a selected list of books.
@app.route('/download', methods=['POST'])
def download_books():
    selected_books = request.form.getlist('item_links')  # Gets list of IDs from checkboxes
    download_selected_books(selected_books)
    return redirect(url_for('index'))


if __name__ == '__main__':
  FoundTheseBooks = []
  app.run(host='0.0.0.0', port=5002, debug=True)
