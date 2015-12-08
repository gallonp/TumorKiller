"""Methods for training various scikit-learn machine learning classifiers."""

from sknn.mlp import Classifier, Layer
from sklearn.externals import joblib
from sklearn import svm


def check_samples(samples):
    """Checks the format of the given sample data.

    Args:
        samples: Tuple containing (sample inputs, sample outputs).

    Returns:
        Samples if they are in a valid format.

    Raises:
        Exception if the sample data has invalid format.
    """
    # Make sure that there are an equal number of inputs and outputs.
    sample_inputs = samples[0]
    sample_outputs = samples[1]
    assert len(sample_inputs) == len(sample_outputs)
    # Make sure that at least one sample was provided.
    if len(sample_inputs) == 0:
        raise Exception('Must provide at least one file for classifier training.')
    # Samples are okay
    return samples


def train_svm(samples, C=1, kernel='rbf', probability=False): #pylint:disable=invalid-name
    """Trains a SVM classifier using the given sample data.

    Args:
        samples: Tuple containing (sample inputs, sample outputs).
        C: Penalty parameter C of the error term.
        kernel: Specifies the kernel type to be used in the algorithm.
        probability: Whether to enable probability estimates.

    Returns:
        The trained SVM classifier.
    """
    sample_inputs, sample_outputs = check_samples(samples)
    clf = svm.SVC(C=C, kernel=kernel, probability=probability)
    clf.fit(sample_inputs, sample_outputs)
    return clf


def use_svm(clf, sample):
    """Uses given SVM to classify given data sample.

    Args:
        clf: An SVM classifier.
        sample: Data sample to classify.

    Returns:
        The SVM's classification for the given data sample.
    """
    return clf.predict(sample)


def train_neural_network(samples, nn=None, learning_rate=0.001, n_iter=25): #pylint:disable=invalid-name
    """Trains a neural network using the given sample data.

    Args:
        samples: Tuple containing (sample inputs, sample outputs).
        nn: Neural network that should be trained. If this is none, a new NN
            will be created.
        learning_rate: Neural network learning rate.
        n_iter: Number of training iterations to use.

    Returns:
        The trained neural network.
    """
    sample_inputs, sample_outputs = check_samples(samples)

    # Create a new classifier if necessary.
    if nn is None:
        n_features = len(sample_inputs[0])
        nn = Classifier(
            layers=[
                Layer("Maxout", units=n_features, pieces=2),
                Layer("Softmax")],
            learning_rate=learning_rate,
            n_iter=n_iter)

    # Train the classifier.
    nn.fit(sample_inputs, sample_outputs)
    return nn


def save_classifier(classifier, name):
    """Saves given classifier in a .pkl file with specified name.

    Args:
        classifier: Classifier to save to file.
        name: Name of the file.
    """
    joblib.dump(classifier, name+'.pkl', compress=9)


def load_classifier(name):
    """Loads a classifier from the specified .pkl file.

    Args:
        name: Name of the file. Something like 'neuralnetone.pkl'.

    Returns:
        Classifier that was saved in the specified file.
    """
    return joblib.load(name)
