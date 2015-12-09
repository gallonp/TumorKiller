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
import fourier_transformer
import trainclassifier as trainer

# pylint:disable=no-member

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


class MRSDataManager(webapp2.RequestHandler):
    """Handler for MRS data management."""

    def get(self):
        """Renders web page where the user can manage MRS data."""
        template = JINJA_ENVIRONMENT.get_template('managedata.html')
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
        conn = ds.create_sqlite_connection()
        LOGGER.debug('Saving MRS data to database...')
        ds.store_mrs_data(conn, database_id, file_name, file_contents, group_label)
        LOGGER.debug('MRS data saved to database.')
        # Signal upload success to the user.
        template = JINJA_ENVIRONMENT.get_template('uploadcomplete.html')
        self.response.write(template.render(
            file_name=file_name,
            group_label=group_label,
            database_id=database_id))


class MRSDataDownloader(webapp2.RequestHandler):
    """Handler for MRS data downloads."""

    def get(self):
        """Shows all MRS data on download page."""
        # Query for all MRS data entries in the database.
        conn = ds.create_sqlite_connection()
        LOGGER.debug('Querying for all MRS data in database...')
        db_entries = ds.fetch_all_mrs_data(conn)
        LOGGER.debug('Found %d MRS data entries in database.', len(db_entries))

        # Render download page.
        template = JINJA_ENVIRONMENT.get_template('downloaddata.html')
        self.response.write(template.render(mrs_data=db_entries))

    def post(self):
        """Serves requested file to the client."""
        # Retrieve specified MRS data from the database.
        mrs_data_id = self.request.get('mrs_data_id')
        db_entry = ds.fetch_mrs_data(ds.create_sqlite_connection(), mrs_data_id)

        # Set response headers.
        self.response.headers['Content-Type'] = 'application/octet-stream'
        self.response.headers['Content-Description'] = 'File Transfer'
        self.response.headers['Content-Transfer-Encoding'] = 'binary'
        self.response.headers['Content-Disposition'] = 'attachment; filename=\"%s\"' % db_entry[1]
        self.response.headers['Content-Length'] = sys.getsizeof(db_entry[2])
        # Set response content.
        self.response.out.write(db_entry[2])


class ClassifierUploader(webapp2.RequestHandler):
    """Handler for uploading ML classifiers."""

    def post(self):
        """Stores specified classifier in the database."""
        # Get request parameters.
        classifier_id = self.request.POST['classifier_id']
        classifier_name = self.request.POST['classifier_name']
        classifier_type = self.request.POST['classifier_type']
        LOGGER.debug(
            'Got save classifier request: %s, %s, %s',
            classifier_id, classifier_name, classifier_type)

        # Retrieve classifier from the "cache".
        classifier = CACHE[classifier_id]
        if classifier is None:
            self.response.out.write('No classifier with ID %s' % classifier_id)

        # Save the classifier in the database.
        conn = ds.create_sqlite_connection()
        ds.store_classifier(
            conn, classifier_id, classifier_name, classifier_type, classifier)

        # Signal save success to user.
        template = JINJA_ENVIRONMENT.get_template('classifiersaved.html')
        self.response.write(template.render())


class ClassifierTrainer(webapp2.RequestHandler):
    """Handler for training classifiers."""

    def get(self):
        """Renders a page where the user can configure classifier training."""
        # Get list of saved classifiers.
        conn = ds.create_sqlite_connection()
        classifiers = ds.fetch_all_classifiers(conn)
        # Get list of available MRS data.
        mrs_data = ds.fetch_all_mrs_data(conn)

        # Render the web page.
        template = JINJA_ENVIRONMENT.get_template('trainclassifier.html')
        self.response.write(template.render(
            classifiers=classifiers, mrs_data=mrs_data))

    def post(self):
        """Trains a classifier as specified by the user."""
        # Load a saved classifier if specified by the user.
        classifier, classifier_name, classifier_type = self.load_specified_classifier() #pylint:disable=line-too-long

        # Prepare MRS data set.
        samples = self.prepare_mrs_data_set()

        LOGGER.debug(
            'TrainClassifier: type=%s, load_classifier=%s, num_samples=%d',
            classifier_type, (classifier != None), len(samples[0]))

        # Train the classifier.
        trained_classifier, training_time = self.train_classifier(
            classifier_type, classifier, samples)

        #TODO: Add test classifier option?
        training_accuracy = trained_classifier.score(samples[0], samples[1])

        # Cache the trained classifier.
        classifier_id = str(uuid.uuid4().hex)
        CACHE[classifier_id] = trained_classifier

        # Signal training completion to user. Prompt user to save classifier.
        template = JINJA_ENVIRONMENT.get_template('trainingcomplete.html')
        self.response.write(template.render(
            classifier_id=classifier_id,
            classifier_name=classifier_name,
            classifier_type=classifier_type,
            training_accuracy=training_accuracy,
            training_time=training_time))

    def load_specified_classifier(self):
        """Loads the user-specified classifier.

        Returns:
            Tuple containing (classifier, classifier_name, classifier_type).
            If the user did not specify a classifier, then classifier and
            classifier_name will be None.
        """
        classifier = None
        classifier_name = None
        classifier_type = self.request.POST['classifier_type']
        # Load a saved classifier if specified by the user.
        if self.request.POST['load_classifier'] == 'true':
            # Query database for classifier with specified ID.
            classifier_id = self.request.POST['classifier_id']
            db_entry = ds.fetch_classifier(
                ds.create_sqlite_connection(), classifier_id)
            classifier = db_entry[3]
            classifier_type = db_entry[2]
            classifier_name = db_entry[1]
        return (classifier, classifier_name, classifier_type)

    def prepare_mrs_data_set(self):
        """Retrieves all specified MRS data entries and processes each entry.

        Each MRS file is parsed and FFT is applied if specified.

        Returns:
            Tuple containing (list of sample inputs, list of sample outputs).
        """
        training_data_ids = self.request.get_all("training_data_ids")
        apply_fft = 'apply_fft' in self.request.POST
        LOGGER.debug('Processing MRS data: apply_fft=%s', apply_fft)
        # Retrieve specified training data from the database.
        conn = ds.create_sqlite_connection()
        db_entries = [ds.fetch_mrs_data(conn, data_id) for data_id in training_data_ids]
        # Separate each database entry into input and output.
        sample_inputs = []
        sample_outputs = []
        for entry in db_entries:
            # Parse data points from the file contents.
            mrs_data = dataparser.get_xy_data(str(entry[2]))
            # Apply FFT to the data points if specified by user.
            if apply_fft:
                mrs_data = fourier_transformer.get_fft(mrs_data)
            # Add input, output pair to separate lists.
            sample_inputs.append(mrs_data)
            sample_outputs.append(entry[3])

        # Format the data for classifier input.
        n_samples = len(sample_inputs)
        n_features = len(sample_inputs[0])
        sample_inputs = np.array(sample_inputs)  # convert before using as buffer
        sample_inputs = np.ndarray(
            shape=(n_samples, n_features), dtype=float, buffer=sample_inputs)
        # Labels for training.
        sample_outputs = np.array(sample_outputs)

        # Return processed MRS data.
        return (sample_inputs, sample_outputs)

    def train_classifier(self, classifier_type, classifier, samples):
        """Trains specified classifier with given arguments and data.

        Args:
            classifier_type: The type of classifier to train.
            classifier: (optional) Classifier model to train.
            samples: Tuple of (sample inputs, sample outputs).

        Returns:
            Tuples containing (trained classifier, training time in seconds).
        """
        # Train the classifier.
        # Record total training time.
        t_start = time.time()
        # Pick trainer method & params based on classifier type.
        if classifier_type == "NeuralNetwork":
            # Train a neural network classifier.
            trained_classifier = trainer.train_neural_network(
                samples, nn=classifier,
                learning_rate=float(self.request.POST['learning_rate']),
                n_iter=int(self.request.POST['n_iter']))
        elif classifier_type == "SVM":
            # Train a SVM classifier.
            trained_classifier = trainer.train_svm(samples)
        else:
            raise Exception("Invalid classifier type: %s" % classifier_type)

        t_end = time.time()
        LOGGER.debug('Training %s complete.', classifier_type)
        training_time = t_end - t_start  # seconds
        return (trained_classifier, training_time)


class DataClassifier(webapp2.RequestHandler):
    """Handler for classifying MRS data."""

    def get(self):
        """Renders a page where the user can classify MRS data."""
        # Get list of saved classifiers.
        conn = ds.create_sqlite_connection()
        classifiers = ds.fetch_all_classifiers(conn)

        # Render the web page.
        template = JINJA_ENVIRONMENT.get_template('classifydata.html')
        self.response.write(template.render(classifiers=classifiers))

    def post(self):
        """Classifies given data using specified classifier."""
        # Retrieve specified classifier from database.
        classifier_id = self.request.POST['classifier_id']
        conn = ds.create_sqlite_connection()
        db_entry = ds.fetch_classifier(conn, classifier_id)
        classifier = db_entry[3]
        # Transform given MRS data for classifier input.
        file_name = self.request.POST['myfile'].filename
        raw_data = self.request.POST['myfile'].file.read()
        d = dataparser.get_xy_data(raw_data)
        fftd = fourier_transformer.get_fft(d)
        # Classify the transformed MRS data.
        test_input = np.array([fftd])
        classification = classifier.predict(test_input)
        # Show classification results.
        template = JINJA_ENVIRONMENT.get_template('classificationresults.html')
        self.response.write(template.render(
            classification=classification, file_name=file_name))


WEB_APP = webapp2.WSGIApplication([
    ('/', Homepage),
    ('/classify_data', DataClassifier),
    ('/data_download', MRSDataDownloader),
    ('/data_manager', MRSDataManager),
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
    parser.add_argument('-port', action="store", type=str, default='8080')
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
    httpserver.serve(APP, host='127.0.0.1', port=args.port)


if __name__ == '__main__':
    main(sys.argv[1:])
