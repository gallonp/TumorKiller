import dataparser
import datastorage as ds
import fourierTransformer
import numpy as np
from sknn.mlp import Classifier, Layer


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
    # Make sure that there are an equal number of inputs and outputs.
    sampleInputs = samples[0]
    sampleOutputs = samples[1]
    assert len(sampleInputs) == len(sampleOutputs)
    # Make sure that at least one sample was provided.
    if len(sampleInputs) == 0:
        raise Exception('Must provide at least one file for classifier training.')

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
