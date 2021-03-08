"""Implement Feed Forward neural network where the parameters are
   number of hidden layers and number of neurons in each hidden layer"""

import copy
from keras.datasets import fashion_mnist
from grad import *
from activation import *
from loss import *
from optimiser import *

""" get training and testing vectors
    Number of Training Images = 60000
    Number of Testing Images = 10000 """
(trainX, trainy), (testX, testy) = fashion_mnist.load_data()

last = 2
# network is a list of all the learning parameters in every layer and gradient is its copy
network = []
gradient = []
# store gradient w.r.t a single datapoint
transient_gradient = []
# will contain the total amount of loss for each timestep(1). timestep defined during lecture.
loss = 0


def forward_propagation(n, x):
    for i in range(n):
        if i == 0:
            network[i]['a'] = network[i]['weight'] @ x + network[i]['bias']
        else:
            network[i]['a'] = network[i]['weight'] @ network[i - 1]['h'] + network[i]['bias']

        network[i]['h'] = activation_function(network[i]['a'], context=network[i]['context'])  # last layer


def backward_propagation(number_of_layers, x, y, number_of_datapoint, clean=False):
    transient_gradient[number_of_layers - 1]['h'] = output_grad(network[number_of_layers - 1]['h'], y)
    transient_gradient[number_of_layers - 1]['a'] = last_grad(network[number_of_layers - 1]['h'], y)
    for i in range(number_of_layers - 2, -1, -1):
        transient_gradient[i]['h'] = h_grad(network=network, transient_gradient=transient_gradient, layer=i)
        transient_gradient[i]['a'] = a_grad(network=network, transient_gradient=transient_gradient, layer=i)
    for i in range(number_of_layers - 1, -1, -1):
        transient_gradient[i]['weight'] = w_grad(network=network, transient_gradient=transient_gradient, layer=i, x=x)
        transient_gradient[i]['bias'] = gradient[i]['a']
    if clean:
        gradient[number_of_layers - 1]['h'] = transient_gradient[number_of_layers - 1]['h'] / float(number_of_datapoint)
        gradient[number_of_layers - 1]['a'] = transient_gradient[number_of_layers - 1]['a'] / float(number_of_datapoint)
        for i in range(number_of_layers - 2, -1, -1):
            gradient[i]['h'] = transient_gradient[i]['h'] / float(number_of_datapoint)
            gradient[i]['a'] = transient_gradient[i]['a'] / float(number_of_datapoint)
        for i in range(number_of_layers - 1, -1, -1):
            gradient[i]['weight'] = transient_gradient[i]['weight'] / float(number_of_datapoint)
            gradient[i]['bias'] = transient_gradient[i]['bias'] / float(number_of_datapoint)
    else:

        gradient[number_of_layers - 1]['h'] += transient_gradient[number_of_layers - 1]['h'] / float(
            number_of_datapoint)
        gradient[number_of_layers - 1]['a'] += transient_gradient[number_of_layers - 1]['a'] / float(
            number_of_datapoint)
        for i in range(number_of_layers - 2, -1, -1):
            gradient[i]['h'] += transient_gradient[i]['h'] / float(number_of_datapoint)
            gradient[i]['a'] += transient_gradient[i]['a'] / float(number_of_datapoint)
        for i in range(number_of_layers - 1, -1, -1):
            gradient[i]['weight'] += transient_gradient[i]['weight'] / float(number_of_datapoint)
            gradient[i]['bias'] += transient_gradient[i]['bias'] / float(number_of_datapoint)


# this function is used for validation, useful during hyperparameter tuning or model change.
def validate(number_of_layer, validateX, validateY, loss_func='cross_entropy'):
    loss = 0
    acc = 0
    if loss_func == 'cross_entropy':
        for x, y in zip(validateX, validateY):
            forward_propagation(number_of_layer, x.reshape(784, 1) / 255.0)
            # adding loss w.r.t to a single datapoint
            loss += cross_entropy(label=y, softmax_output=network[number_of_layer - 1]['h'])
            max_prob = np.argmax(network[number_of_layer - 1]['h'])
            if max_prob == y:
                acc += 1
    average_loss = loss / float(len(validateX))
    acc = acc / float(len(validateX))
    return [average_loss, acc]


# 1 epoch = 1 pass over the data
def train(datapoints, batch, epochs, labels, f, learning_rate):
    n = len(network)  # number of layers
    d = len(datapoints)  # number of data points
    """this variable will be used to separate , training and validation set
        1) we take 10 % of the data as suggested in the question. -->int(d * .1)
        2) we also add any extra remaining data to validation set so that,
        training data is exactly divisible by batch size -->((d - int(d * .1)) % batch
    """
    border = d - ((d - int(d * .1)) % batch + int(d * .1))
    # separating the validation data
    validateX = datapoints[border:]
    validateY = labels[border:]
    # deleting copied datapoints
    datapoints = datapoints[:border]
    labels = labels[:border]
    # updating d
    d = border
    # is used to stochastically select our data.
    shuffler = np.arange(0, d)
    # creating simple gradient descent optimiser
    opt = MomentumGradientDescent(eta=learning_rate, layers=n, gamma=.99)
    # loop for epoch iteration
    for k in range(epochs):
        # iteration for different starting point for epoch
        # shuffler at the start of each epoch
        np.random.shuffle(shuffler)
        for i in range(0, d - batch + 1, batch):
            clean = True
            # initiating loss for current epoch
            global loss
            loss = 0
            # iterate over a batch
            for j in range(i, i + batch, 1):
                # creating a single data vector and normalising color values between 0 to 1
                x = datapoints[shuffler[j]].reshape(784, 1) / 255.0
                y = labels[shuffler[j]]
                forward_propagation(n, x)
                backward_propagation(n, x, y, number_of_datapoint=batch, clean=clean)
                clean = False

            opt.descent(network=network, gradient=gradient)
            average_loss = validate(number_of_layer=n, validateX=validateX, validateY=validateY)
            # printing average loss.
            print(average_loss)
    # anneal if required
    opt.anneal(loss=average_loss[0])


""" Adds a particular on top of previous layer , the layers are built in a incremental way.
    Context denotes the type of layer we have.Eg - Sigmoid or Tanh etc.
    Passing any number to input_dim it we counted as the first layer
 """


def add_layer(number_of_neurons, context, input_dim=None):
    # Initialize an Empty Dictionary: layer
    layer = {}
    if input_dim != None:
        layer['weight'] = np.random.normal(size=(number_of_neurons, input_dim))
        glorot = input_dim
    else:
        # get number of neurons in the previous layer
        previous_lay_neuron_num = network[-1]['h'].shape[0]
        layer['weight'] = np.random.normal(size=(number_of_neurons, previous_lay_neuron_num))
        glorot = previous_lay_neuron_num
    layer['weight'] = layer['weight'] * math.sqrt(2 / float(glorot))
    # initialise a 1-D array of size n with random samples from a uniform distribution over [0, 1).
    layer['bias'] = np.zeros((number_of_neurons, 1))
    # initialises a 2-D array of size [n*1] and type float with element having value as 1.
    layer['h'] = np.zeros((number_of_neurons, 1))
    layer['a'] = np.zeros((number_of_neurons, 1))
    layer['context'] = context
    network.append(layer)


"""master() is used to intialise all the learning parameters 
   in every layer and then start the training process"""


def master(layers, neurons_in_each_layer, batch, epochs, output_dim, x, y, learning_rate):
    n = neurons_in_each_layer

    """intializing number of input features per datapoint as 784, 
       since dataset consists of 28x28 pixel grayscale images """
    n_features = 784
    # adding layers
    add_layer(number_of_neurons=16, context='sigmoid', input_dim=784)
    add_layer(number_of_neurons=8, context='sigmoid')
    add_layer(number_of_neurons=output_dim, context='softmax')

    global gradient
    """Recursively make a copy of network. Changes made to the copy will not reflect in the original network."""
    gradient = copy.deepcopy(network)
    global transient_gradient
    transient_gradient = copy.deepcopy(network)
    train(datapoints=trainX, labels=trainy, batch=batch, epochs=epochs, f=n_features, learning_rate=learning_rate)


master(layers=3, neurons_in_each_layer=8, epochs=50, batch=32, output_dim=10, x=trainX, y=trainy, learning_rate=.001)
