
from flask import Flask, render_template
import os


app = Flask(__name__)

# Produces index.html from Catalog.txt.
def GenerateMainPage(fullDirectoryPath):
  with (open("./templates/index.html", "w", encoding='utf-8',  errors="ignore") as html_file):

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

    footer = \
      """
      
        </body>
        </html>
      """

    html_file.write(header + "\n")

    with open(fullDirectoryPath + "/static/Books/Catalog.txt", "r", encoding='utf-8',  errors="ignore") as catalog_file:
        while True:
            Title = catalog_file.readline().strip()
            if not Title: break
            Abstract = catalog_file.readline().strip()
            Filename = catalog_file.readline().strip()
            entry = "<p style=\"font-size:20px\">" \
                    + "<a href=\"{{ url_for('static', filename='Books/" + Filename + "') }}\">" \
                    + Title + "</a></p>\n" + Abstract + "<br><br>\n\n"
            html_file.write(entry)
        html_file.write(footer)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':

  directory = os.getcwd().replace("\\", "/")
  index = directory.find(":")
  if index != -1: directory = directory[index+1 :]

  # This code not needed.
  #if sys.platform == "win32":
  #  print("Running on Windows")
  # elif sys.platform == "linux":
  #   print("Running on Linux")
  # else
  #   print("System not recognized")

  GenerateMainPage(directory)
  app.run(host='0.0.0.0', port=5001, debug=True)
