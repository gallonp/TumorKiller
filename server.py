"""Backend server for Brain Tumor Classification."""

import argparse
import jinja2
import logging
import numpy as np
import os
import paste.cascade as cascade
import paste.httpserver as httpserver
import paste.urlparser as urlparser
import sys
import time
import uuid
import webapp2

import datastorage as ds
import dataparser
import fourierTransformer
import trainclassifier as trainer


# Directory containing jinja templates.
JINJA_TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/templates'

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(JINJA_TEMPLATE_DIR),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

LOGGER = logging.getLogger(__name__)

# Use this dictionary as a cache.
# NOTE: This global variable is not shared among app instances.
CACHE = {}


class Homepage(webapp2.RequestHandler):
    """Handler for website's home page."""

    def get(self):
        """Renders the home page."""
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())


class MRSDataUploader(webapp2.RequestHandler):
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
        ds.StoreMRSData(conn, database_id, file_name, file_contents, group_label)
        LOGGER.debug('MRS data saved to database.')
        # Signal upload success to the user.
        self.response.out.write('<p>MRS data \"%s\" (%s) was uploaded.</p>' %
            (file_name, group_label))
        self.response.out.write('<p>Database ID: %s</p>' % database_id)
        self.response.out.write('<a href="/">return</a>')

class MRSDataList(webapp2.RequestHandler):
    """Handler for listing uploaded MRS data."""

    def get(self):
        """Displays list of MRS data entries uploaded to the server."""
        # Establish database connection.
        conn = ds.CreateSQLiteConnection()
        # Query for all MRS data entries in the database.
        LOGGER.debug('Querying for all MRS data in database...')
        db_entries = ds.FetchAllMRSData(conn)
        LOGGER.debug('Found %d MRS data entries in database.', len(db_entries))

        # Display the list of MRS data.
        self.response.out.write('<h2>Uploaded MRS Data</h2>')
        for entry in db_entries:
            self.response.out.write('<p>[%s] %s (ID: %s)</p>' %
                (entry[3], entry[1], entry[0]))


class MRSDataReader(webapp2.RequestHandler):
    """Handler for reading uploaded MRS data files."""

    def get(self):
        """Reads the specified MRS data file from the database."""
        # Get database ID from request.
        db_id = self.request.GET['db_id']
        # Establish database connection.
        conn = ds.CreateSQLiteConnection()
        # Query database for MRS data with specified ID.
        db_entry = ds.FetchMRSData(conn, db_id)
        file_contents = db_entry[2] if db_entry else None
        # Return file contents in the response.
        self.response.out.write(file_contents)


class ClassifierUploader(webapp2.RequestHandler):
    """Handler for uploading ML classifiers."""

    def post(self):
        """Stores specified classifier in the database."""
        # Get request parameters.
        classifier_id = self.request.POST['classifier_id']
        classifier_name = self.request.POST['classifier_name']
        classifier_type = self.request.POST['classifier_type']
        LOGGER.debug('Got save classifier request: %s, %s, %s' % (
            classifier_id, classifier_name, classifier_type))

        # Retrieve classifier from the "cache".
        classifier = CACHE[classifier_id]
        if classifier is None:
            self.response.out.write('No classifier with ID %s' % classifier_id)

        # Save the classifier in the database.
        conn = ds.CreateSQLiteConnection()
        ds.StoreClassifier(
            conn, classifier_id, classifier_name, classifier_type, classifier)
        self.response.out.write("<p>Classifier was saved.</p>")
        self.response.out.write('<a href="/">return</a>')


class ClassifierTrainer(webapp2.RequestHandler):
    """Handler for training classifiers."""

    def get(self):
        """Renders a page where the user can configure classifier training."""
        # Get list of saved classifiers.
        conn = ds.CreateSQLiteConnection()
        classifiers = ds.FetchAllClassifiers(conn)
        # Get list of available MRS data.
        mrs_data = ds.FetchAllMRSData(conn)

        # Render the web page.
        template = JINJA_ENVIRONMENT.get_template('trainclassifier.html')
        self.response.write(template.render(
            classifiers=classifiers, mrs_data=mrs_data))

    def post(self):
        """Trains a classifier as specified by the user."""
        # Get classifier type.
        classifier_type = self.request.POST['classifier']
        # Get classifier parameters.
        learning_rate = float(self.request.POST['learning_rate'])
        n_iter = int(self.request.POST['n_iter'])
        # Get training data IDs.
        training_data_ids = self.request.get_all("training_data_ids")
        # Get load classifer option.
        load_classifier = self.request.POST['load_classifier'] == 'true'

        LOGGER.debug('TrainClassifier: type=%s, load_classifier=%s, num_samples=%d' % (
            classifier_type, load_classifier, len(training_data_ids)))

        # Load a saved classifier if specified by the user.
        classifier = None
        classifier_name = None
        if load_classifier:
            # Query database for classifier with specified ID.
            classifier_id = self.request.POST['classifier_id']
            conn = ds.CreateSQLiteConnection()
            db_entry = ds.FetchClassifier(conn, classifier_id)
            classifier = db_entry[3]
            classifier_type = db_entry[2]
            classifier_name = db_entry[1]

        # Retrieve specified training data from the database.
        conn = ds.CreateSQLiteConnection()
        db_entries = [ds.FetchMRSData(conn, data_id) for data_id in training_data_ids]

        # For each MRS data file, parse the data points and apply FFT.
        # TODO: make this pre-processing step an option in the UI?
        sampleInputs = []
        sampleOutputs = []
        for entry in db_entries:
            # Parse data points from the file contents.
            d = dataparser.get_xy_data(str(entry[2]))
            # Apply FFT to the data points.
            fftd = fourierTransformer.getFFT(d)
            sampleInputs.append(fftd)
            # Get the group label.
            sampleOutputs.append(entry[3])

        # Format the data for classifier input.
        n_samples = len(sampleInputs)
        n_features = len(sampleInputs[0])
        sampleInputs = np.array(sampleInputs)  # convert before using as buffer
        sampleInputs = np.ndarray(
            shape=(n_samples, n_features), dtype=float, buffer=sampleInputs)
        # Output labels for training.
        sampleOutputs = np.array(sampleOutputs)
        # Bundle inputs and outputs together.
        samples = (sampleInputs, sampleOutputs)

        print 'n_features: %d' % n_features
        # Train the classifier.

        # Record total training time.
        if classifier:
            print classifier.layers
        t_start = time.time()
        # TODO: pick trainer method / params based on classifier type
        classifier = trainer.TrainNeuralNetwork(
            samples, nn=classifier, n_iter=n_iter, learning_rate=learning_rate)
        t_end = time.time()
        training_time = t_end - t_start  # seconds
        LOGGER.debug('Training %s complete.' % classifier_type)

        #TODO: Add test classifier option?
        training_accuracy = classifier.score(sampleInputs, sampleOutputs)

        # Cache the trained classifier.
        classifier_id = str(uuid.uuid4().hex)
        CACHE[classifier_id] = classifier

        # Signal training completion to user. Prompt user to save classifier.
        template = JINJA_ENVIRONMENT.get_template('trainingcomplete.html')
        self.response.write(template.render(
            classifier_id=classifier_id,
            classifier_name=classifier_name,
            classifier_type=classifier_type,
            training_accuracy=training_accuracy,
            training_time=training_time))


class DataClassifier(webapp2.RequestHandler):
    """Handler for classifying MRS data."""

    def get(self):
        """Renders a page where the user can classify MRS data."""
        # Get list of saved classifiers.
        conn = ds.CreateSQLiteConnection()
        classifiers = ds.FetchAllClassifiers(conn)

        # Render the web page.
        template = JINJA_ENVIRONMENT.get_template('classifydata.html')
        self.response.write(template.render(classifiers=classifiers))

    def post(self):
        """Classifies given data using specified classifier."""
        # Retrieve specified classifier from database.
        classifier_id = self.request.POST['classifier_id']
        conn = ds.CreateSQLiteConnection()
        db_entry = ds.FetchClassifier(conn, classifier_id)
        classifier = db_entry[3]
        # Transform given MRS data for classifier input.
        raw_data = self.request.POST['myfile'].file.read()
        d = dataparser.get_xy_data(raw_data)
        fftd = fourierTransformer.getFFT(d)
        # Classify the transformed MRS data.
        test_input = np.array([fftd])
        classification = classifier.predict(test_input)
        self.response.write('classification: %s' % classification)


WEB_APP = webapp2.WSGIApplication([
    ('/', Homepage),
    ('/classify_data', DataClassifier),
    ('/data_list', MRSDataList),
    ('/data_viewer', MRSDataReader),
    ('/data_upload', MRSDataUploader),
    ('/save_classifier', ClassifierUploader),
    ('/train_classifier', ClassifierTrainer),
], debug=True)

# Static file server.
STATIC_APP = urlparser.StaticURLParser('static/')

# Create a cascade that looks for static files first, then tries the webapp.
APP = cascade.Cascade([STATIC_APP, WEB_APP])


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
