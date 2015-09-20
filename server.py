"""Backend server for Brain Tumor Classification."""

import argparse
import datastorage as ds
import jinja2
import logging
import os
import paste.httpserver as httpserver
import sys
import uuid
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

LOGGER = logging.getLogger(__name__)


class Homepage(webapp2.RequestHandler):
    """Handler for website's home page."""

    def get(self):
        """Renders the home page."""
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())


class UploadFiles(webapp2.RequestHandler):
    """Handler for data file uploads."""

    def get(self):
        """Renders web page where the user can upload files."""
        template = JINJA_ENVIRONMENT.get_template('trainclassifier.html')
        self.response.write(template.render())

    def post(self):
        """Saves user-uploaded files to the database."""
        # Get raw file contents from request.
        file_name = self.request.POST['myfile'].filename
        file_contents = buffer(self.request.POST['myfile'].file.read())
        # Generate a random UUID for the file.
        file_id = str(uuid.uuid4().hex)

        # Establish database connection.
        conn = ds.CreateSQLiteConnection()
        # Save file to the database.
        LOGGER.debug('Saving file to database...')
        ds.SaveFile(conn, file_id, file_name, file_contents)
        LOGGER.debug('File saved to database.')

        # Signal upload success to the user.
        self.response.out.write('<p>File \"%s\" was uploaded.</p>' % file_name)
        self.response.out.write('<p>File ID: %s</p>' % file_id)


class ListUploadedFiles(webapp2.RequestHandler):
    """Handler for listing uploaded data files."""

    def get(self):
        """Displays list of files uploaded to the server."""
        # Establish database connection.
        conn = ds.CreateSQLiteConnection()
        # Query for files in the database.
        LOGGER.debug('Querying for all files in database...')
        files = ds.ListFiles(conn)
        LOGGER.debug('Found %d files in database.', len(files))

        # Display the list of files.
        self.response.out.write('<h2>Uploaded Files</h2>')
        for file in files:
            self.response.out.write('<p>%s (%s)</p>' % (file[0], file[1]))


class ReadFiles(webapp2.RequestHandler):
    """Handler for reading uploaded data files."""

    def get(self):
        """Reads specified file from the database."""
        # Get file ID from request.
        file_id = self.request.GET['file_id']
        # Establish database connection.
        conn = ds.CreateSQLiteConnection()
        # Read the file from the database.
        file_contents = ds.ReadFile(conn, file_id)
        # Return file contents in the response.
        self.response.out.write(file_contents)


APP = webapp2.WSGIApplication([
    ('/', Homepage),
    ('/file_list', ListUploadedFiles),
    ('/file_read', ReadFiles),
    ('/file_upload', UploadFiles),
], debug=True)


def main(argv):
    """Initialize the server."""
    # Command-line args.
    parser = argparse.ArgumentParser()
    parser.add_argument('-loglevel', action="store", type=str, default='INFO')
    args = parser.parse_args(argv)

    # Set logging level.
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    LOGGER.setLevel(numeric_level)

    # Direct log messages to the console.
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        fmt='%(asctime)s:%(name)s: %(levelname)-8s %(message)s',
        datefmt='%b %d %H:%M:%S')
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)

    # Start ther server.
    httpserver.serve(APP, host='127.0.0.1', port='8080')


if __name__ == '__main__':
    main(sys.argv[1:])
