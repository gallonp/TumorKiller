#Brain Tumor Analysis Interface

##Setup Instructions

#### 1. Install Dependencies

Please use [pip](https://pip.pypa.io/en/stable/installing/) to install the following dependencies:

1. webapp2
2. webob
3. paste
4. jinja2
5. scikit-neuralnetwork

#### 2. Start the Application Server

Download the latest project source code from GitHub.

Navigate to the project's root directory in your terminal, and run the following command:

`python server.py`

This will start the application locally, and you should then be able to see the homepage by navigating to `127.0.0.1:8000` in your web browser.

######Additional Server Parameters

Use the `-port` argument to change the server port number:

`python server.py -port=8088`

Use the `-loglevel` argument to control logging verbosity:

`python server.py -loglevel=debug`

##Testing the Code

Python [unittest](https://docs.python.org/2/library/unittest.html) was used for some of the core application components. By convention, tests for `component.py` are in `component_test.py` located in the same directory.

To execute unit tests for `component.py`, run the following command from the root directory of the project:

`python -m unittest component_test`

To execute all unit tests, run:

`python -m unittest discover "*_test.py"`

##Checking Code Format

All Python files in this project should comply with [PEP8](https://www.python.org/dev/peps/pep-0008/) coding standards. [Pylint](http://www.pylint.org/)  can be used to to check the format of `module.py` by running the following command in your terminal:

`pylint module.py`
