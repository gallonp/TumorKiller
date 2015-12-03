import dataparser
import datastorage as ds
import fourierTransformer
import numpy as np
from sknn.mlp import Classifier, Layer
from sklearn.externals import joblib
from sklearn import svm


def checkSamples(samples):
    # Make sure that there are an equal number of inputs and outputs.
    sampleInputs = samples[0]
    sampleOutputs = samples[1]
    assert len(sampleInputs) == len(sampleOutputs)
    # Make sure that at least one sample was provided.
    if len(sampleInputs) == 0:
        raise Exception('Must provide at least one file for classifier training.')
    # Samples are okay
    return samples


def trainSVM(samples, C=1, kernel='rbf', probability=False):
    sampleInputs, sampleOutputs = checkSamples(samples)
    clf = svm.SVC(C=C, kernel=kernel, probability=probability)
    clf.fit(sampleInputs, sampleOutputs)
    return clf


def useSVM(clf, sample):
    return clf.predict(sample)


def TrainNeuralNetwork(samples, nn=None, learning_rate=0.001, n_iter=25):
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
    sampleInputs, sampleOutputs = checkSamples(samples)

    # Create a new classifier if necessary.
    if nn is None:
        n_features = len(sampleInputs[0])
        nn = Classifier(
            layers=[
                Layer("Maxout", units=n_features, pieces=2),
                Layer("Softmax")],
            learning_rate=learning_rate,
            n_iter=n_iter)

    # Train the classifier.
    nn.fit(sampleInputs, sampleOutputs)
    return nn


def saveClassifier(classifier, name):
    joblib.dump(clf, name+'.pkl', compress=9)
    return True


#name would be something like 'neuralnetone.pkl'
#assumes a .pkl file
def loadClassifier(name):
    return joblib.load(name)