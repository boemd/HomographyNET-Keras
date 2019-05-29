from keras.models import Sequential, load_model
from keras.layers import InputLayer, Dense, Conv2D, BatchNormalization, Activation, MaxPooling2D, Flatten, Dropout
from keras import optimizers, callbacks
import usefull_function


class HomographyNN:

    def __init__(self, batch_size, epochs, learning_rate, momentum):
        """
        Set all the parameters of the neural network
        :param batch_size: Dimension of the batch for every epochs
        :param epochs: Number of epochs until the stop
        :param learning_rate: value of the learning rate for the SGD
        :param momentum: momentum for the SGD

        """
        self.batch_size = batch_size
        self.epochs = epochs
        self.model = None
        self.optimizer = None
        self.cb = None
        self.lr = learning_rate
        self.momentum = momentum

    def build_model(self):
        """
        Builds a Sequential model by stacking:
            Input layer
            4 conv layers (num filters: 64, kernel size: 3) with batch normalization and relu activation
            4 conv layers (num filters: 128, kernel size: 3) with batch normalization and relu activation
            Max-Pooling (2x2) is performed every 2 convolutions
            Fully connected layer (depth: 1024)
            Output layer
        :return: the built model
        """
        model1 = Sequential()
        model1.add(InputLayer(input_shape=(128, 128, 2), batch_size=self.batch_size, name='input_layer'))

        model1.add(Conv2D(64, 3, name='conv_64_1'))
        model1.add(BatchNormalization(name='batch_norm_1'))
        model1.add(Activation('relu', name='relu_1'))

        model1.add(Conv2D(64, (3, 3), name='conv_64_2'))
        model1.add(BatchNormalization(name='batch_norm_2'))
        model1.add(Activation('relu', name='relu_2'))

        model1.add(MaxPooling2D(pool_size=(2, 2), name='pool_1'))

        model1.add(Conv2D(64, (3, 3), name='conv_64_3'))
        model1.add(BatchNormalization(name='batch_norm_3'))
        model1.add(Activation('relu', name='relu_3'))

        model1.add(Conv2D(64, (3, 3), name='conv_64_4'))
        model1.add(BatchNormalization(name='batch_norm_4'))
        model1.add(Activation('relu', name='relu_4'))

        model1.add(MaxPooling2D(pool_size=(2, 2), name='pool_2'))

        model1.add(Conv2D(128, (3, 3), name='conv_128_1'))
        model1.add(BatchNormalization(name='batch_norm_5'))
        model1.add(Activation('relu', name='relu_5'))

        model1.add(Conv2D(128, (3, 3), name='conv_128_2'))
        model1.add(BatchNormalization(name='batch_norm_6'))
        model1.add(Activation('relu', name='relu_6'))

        model1.add(MaxPooling2D(pool_size=(2, 2), name='pool_3'))

        model1.add(Conv2D(128, (3, 3), name='conv_128_3'))
        model1.add(BatchNormalization(name='batch_norm_7'))
        model1.add(Activation('relu', name='relu_7'))

        model1.add(Conv2D(128, (3, 3), name='conv_128_4'))
        model1.add(BatchNormalization(name='batch_norm_8'))
        model1.add(Activation('relu', name='relu_8'))

        # model1.add(MaxPooling2D(pool_size=(2, 2)))

        model1.add(Flatten(name='flatten'))

        model1.add(Dropout(0.5))

        model1.add(Dense(1024, name='dense_1'))
        model1.add(Activation('relu', name='relu_9'))
        # model1.add(BatchNormalization())

        model1.add(Dropout(0.5))

        model1.add(Dense(8, name='dense_2'))

        model1.summary()
        self.model = model1
        return

    def get_model(self):
        """
        return the keras model
        :return: keras model file
        """
        return self.model

    def save_all(self, file):
        """
        Saves the model in a .h5 file
        :param file: name of the file in which to save the model
        """
        self.model.save(file + "_model.h5")
        return

    def save_weights(self, file):
        """
        Saves the weights in a .h5 file
        :param file: name of the file in which to save the model
        """
        self.model.save_weights(file + "_weights.h5")
        return

    def load_weights(self, file):
        """
        Loads the saved weights in the model
        :param file: path of the file containing the weights
        """
        self.model.load_weights(file + "_weights.h5")
        return

    def load_all(self, file):
        """
        Load all the parameter of the NN
        :param file: name of the element
        """
        self.model = load_model(file + "_model.h5")

    def set_optimizer_sgd(self,):
        """
        Set the optimizer for the NN
        :param lr: the value of the learning rate
        :param momentum: set the momentum value
        """
        sgd = optimizers.SGD(lr=self.lr, momentum=self.momentum, decay=0.0, nesterov=False)
        self.optimizer = sgd

    def set_callback(self, function):
        """
        Set the callbacks value for the NN
        :param function: the function for the learning rate scheduler
        """
        callback_learning_rate = callbacks.LearningRateScheduler(function)
        callbacks_early_stopping = callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=10, verbose=1,
                                                           mode='min', baseline=None, restore_best_weights=False)
        self.cb = [callback_learning_rate, callbacks_early_stopping]

    def compile(self):
        """
        compile the model
        """
        self.model.compile(optimizer=self.optimizer, loss="msle", metrics=["mse"], loss_weights=None,
                           sample_weight_mode=None, weighted_metrics=None, target_tensors=None)

    def fit(self, training_generator, dimension_train, val_generator, dimension_val):
        """
        Fit the precedent created model
        :param training_generator: the generetor of sample for the training
        :param dimension_train: the dimension of the training set
        :param val_generator: the generetor of sample for the test
        :param dimension_val: the dimension of the validation set
        """
        self.model.fit_generator(generator=training_generator,
                                 steps_per_epoch=(dimension_train // self.batch_size),
                                 epochs=self.epochs,
                                 verbose=1,
                                 callbacks=self.cb,
                                 validation_data=val_generator,
                                 validation_steps=dimension_val//self.batch_size,
                                 class_weight=None,
                                 max_queue_size=10,
                                 workers=1,
                                 use_multiprocessing=True,
                                 shuffle=True,
                                 initial_epoch=0)

    def prediction(self, x):
        """
        Predict the value from a new samples
        :param x: new samples to pass at the NN
        :return: the predicted values
        """
        return self.model.predict(x, batch_size=self.batch_size, verbose=0, steps=len(x)//self.batch_size)

    def prediction_generator(self, generator, dimension_generator):
        """
        Prediction of a list of files
        :param generator:
        :param dimension_generator:
        :return:
        """
        return self.model.predict_generator(generator, steps=dimension_generator//self.batch_size, max_queue_size=10, workers=1,
                                            use_multiprocessing=True, verbose=0)

    def test(self, test_generator, dimension_test):
        """
        Find the error for the prediction on the test set
        :param test_generator: the generetor of sample for the test
        :param dimension_test: the dimension of the test set
        :return: the msle and the mse for the test set
        """
        return self.model.evaluate_generator(generator=test_generator, steps=dimension_test//self.batch_size,
                                             max_queue_size=10, workers=1, use_multiprocessing=True, verbose=1)

    def generate_homography_nn(self):
        """
        generate a complete homography neural network model
        """
        # Create the NN
        self.set_optimizer_sgd()
        self.set_callback(usefull_function.lr_callback)
        self.build_model()
        self.compile()

