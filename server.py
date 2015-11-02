"""Backend server for Brain Tumor Classification."""

import argparse
import datastorage as ds
import dataparser
import jinja2
import logging
import os
import paste.httpserver as httpserver
import sys
import uuid
import webapp2
import fourierTransformer


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


class UploadMRSData(webapp2.RequestHandler):
    """Handler for MRS data uploads."""

    def get(self):
        """Renders web page where the user can upload MRS data."""
        template = JINJA_ENVIRONMENT.get_template('uploaddata.html')
        self.response.write(template.render())

    def post(self):
        """Saves user-uploaded MRS data to the database."""
        # Get raw file contents from request.
        file_name = self.request.POST['myfile'].filename
        file_contents = buffer(self.request.POST['myfile'].file.read())
        # Label for this data's therapy group (e.g. "groupA", "groupB").
        group_label = self.request.POST['grouplabel']
        # Generate a random UUID for the file.
        database_id = str(uuid.uuid4().hex)

        # Save MRS data to the database.
        conn = ds.CreateSQLiteConnection()
        LOGGER.debug('Saving MRS data to database...')
        ds.SaveMRSData(conn, database_id, file_name, file_contents, group_label)
        LOGGER.debug('MRS data saved to database.')
        # Signal upload success to the user.
        self.response.out.write('<p>MRS data \"%s\" (%s) was uploaded.</p>' %
            (file_name, group_label))
        self.response.out.write('<p>Database ID: %s</p>' % database_id)


class ListUploadedMRSData(webapp2.RequestHandler):
    """Handler for listing uploaded MRS data."""

    def get(self):
        """Displays list of MRS data entries uploaded to the server."""
        # Establish database connection.
        conn = ds.CreateSQLiteConnection()
        # Query for all MRS data entries in the database.
        LOGGER.debug('Querying for all MRS data in database...')
        db_entries = ds.ListMRSData(conn)
        LOGGER.debug('Found %d MRS data entries in database.', len(db_entries))

        # Display the list of MRS data.
        self.response.out.write('<h2>Uploaded MRS Data</h2>')
        for entry in db_entries:
            self.response.out.write('<p>[%s] %s (ID: %s)</p>' %
                (entry[3], entry[1], entry[0]))


class ReadMRSData(webapp2.RequestHandler):
    """Handler for reading uploaded MRS data files."""

    def get(self):
        """Reads the specified MRS data file from the database."""
        # Get database ID from request.
        db_id = self.request.GET['db_id']
        # Establish database connection.
        conn = ds.CreateSQLiteConnection()
        # Query database for MRS data with specified ID.
        db_entry = ds.ReadMRSData(conn, db_id)
        file_contents = db_entry[2] if db_entry else None
        # Return file contents in the response.
        self.response.out.write(file_contents)


class TestFileParser(webapp2.RequestHandler):
    """Handler for testing MRS data file parser."""

    def get(self):
        """Reads and parses specified MRS data file in database."""
        # Query the database for MRS data with specified ID.
        db_id = self.request.GET['db_id']
        # Establish database connection.
        conn = ds.CreateSQLiteConnection()
        # Read the file from the database.
        db_entry = ds.ReadMRSData(conn, db_id)

        # Make sure the file exists.
        if db_entry is None:
            self.response.out.write('ID (%s) not found in database.' % db_id)
        else:
            # Parse the file contents.
            file_contents = db_entry[2]
            file_header = dataparser.get_header_data(str(file_contents))
            file_values = dataparser.get_xy_data(str(file_contents))
            # Display parsed file contents.
            # self.response.out.write(file_header)
            # self.response.out.write(file_values)
            real = [x.real for x in file_values];

            self.response.out.write(fourierTransformer.getFFT(real))


APP = webapp2.WSGIApplication([
    ('/', Homepage),
    ('/data_list', ListUploadedMRSData),
    ('/data_read', ReadMRSData),
    ('/data_upload', UploadMRSData),
    ('/test_parser', TestFileParser)
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
