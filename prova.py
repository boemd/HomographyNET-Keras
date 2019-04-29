from keras.models import Sequential
from keras.layers import InputLayer, Dense, Conv2D, BatchNormalization, Activation, MaxPooling2D, Flatten, Dropout
import MY_Generator
import keras
import tensorflow as tf
import numpy as np
from os import scandir

FLAGS = tf.flags.FLAGS

tf.flags.DEFINE_string('input_dir', 'C:/Users/gabro/Documents/3D/Dataset/db_train_set', 'Input directory')
tf.flags.DEFINE_string('test_dir', 'C:/Users/gabro/Documents/3D/Dataset/db_test_set', 'Test directory')
tf.flags.DEFINE_string('val_dir', 'C:/Users/gabro/Documents/3D/Dataset/db_vsl_set', 'Validation directory')


def build_model(batch_size):
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
    model1.add(InputLayer(input_shape=(128, 128, 2), batch_size=batch_size, name='input_layer'))

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
    model = model1
    model1.summary()

    return model


def _lr_callback(epochs, lr):
    updated_lr = lr
    #il primo epochs è 0 che ha resto 0
    if ((epochs+1) % 2) == 0:
        updated_lr /= 10
    return updated_lr


def data_reader(input_dir):
    """
    scans the input folder and organizes the various paths
    :param input_dir: directory containing images (.png) of type A and B and their respective homography matrices (.mat)
    :return: lists of paths of images (types A and B) and homography matrices
    """
    images_A_paths = []
    images_B_paths = []
    homographies_paths = []

    for file in scandir(input_dir):
        if file.name.endswith('A.png'):
            images_A_paths.append(file.path)
        elif file.name.endswith('B.png'):
            images_B_paths.append(file.path)
        elif file.name.endswith('.mat'):
            homographies_paths.append(file.path)

    cond_1 = len(images_A_paths) != len(images_B_paths)
    cond_2 = len(images_B_paths) != len(homographies_paths)
    cond_3 = len(homographies_paths) != len(images_A_paths)

    # check correct correspondences between lists
    if cond_1 or cond_2 or cond_3:
        raise Exception('Paths not corresponding. Length mismatch.')

    for i in range(len(homographies_paths)):
        a = images_A_paths[i].split('\\')[-1].split('A')[0]
        b = images_B_paths[i].split('\\')[-1].split('B')[0]
        c = homographies_paths[i].split('\\')[-1].split('.')[0]
        if a != b or b != c or c != a:
            raise Exception('Paths not corresponding. Not corresponding files.')

    # everything is matched
    return images_A_paths, images_B_paths, homographies_paths


def train(batch_size, epochs):
    lr = 0.005
    momentum = 0.9
    a_train, b_train, mat_train = data_reader(FLAGS.input_dir)
    x_val = np.load('x_val.npy')
    y_val = np.load('y_val.npy')

    callback_learning_rate = keras.callbacks.LearningRateScheduler(_lr_callback)
    callbacks_early_stopping = keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=10, verbose=1,
                                                             mode='min', baseline=None, restore_best_weights=False)
    my_training_batch_generator = MY_Generator.Generator(a_train, b_train, mat_train, batch_size)
    model = build_model(batch_size)
    sgd = keras.optimizers.SGD(lr=lr, momentum=momentum, decay=0.0, nesterov=False)
    model.compile(optimizer=sgd, loss="msle", metrics=["mse"], loss_weights=None,
                  sample_weight_mode=None, weighted_metrics=None, target_tensors=None)
    num_training_samples = len(a_train)
    num_validation_samples = len(y_val)

    model.fit_generator(generator=my_training_batch_generator,
                        steps_per_epoch=(num_training_samples//batch_size),
                        epochs=epochs,
                        verbose=1,
                        callbacks=[callbacks_early_stopping, callback_learning_rate],
                        validation_data=(x_val, y_val),
                        validation_steps=(num_validation_samples//batch_size),
                        class_weight=None,
                        max_queue_size=10,
                        workers=1,
                        use_multiprocessing=True,
                        shuffle=True,
                        initial_epoch=0)
    x_test = np.load('x_test.npy')
    y_test = np.load('x_test.npy')
    [loss, mtr] = model.evaluate(x_test, y_test, batch_size=64, verbose=1)
    # lr = 0.005
    # momentum = 0.9
    # callback_learning_rate = keras.callbacks.LearningRateScheduler(_lr_callback)
    # callbacks_early_stopping = keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=10, verbose=1,
    #                                                          mode='min', baseline=None, restore_best_weights=False)
    # model = build_model()
    # sgd = keras.optimizers.SGD(lr=lr, momentum=momentum, decay=0.0, nesterov=False)
    # model.compile(optimizer=sgd, loss="msle", metrics=["mse"], loss_weights=None,
    #               sample_weight_mode=None, weighted_metrics=None, target_tensors=None)
    # model.fit(x=(x_train_1, x_train_2),
    #           y=y_train,
    #           batch_size=batch_size,
    #           epochs=epochs,
    #           verbose=1,
    #           callbacks=[callbacks_early_stopping, callback_learning_rate],
    #           validation_split=0.1,
    #           validation_data=None,
    #           shuffle=True,
    #           class_weight=None,
    #           sample_weight=None,
    #           initial_epoch=0,
    #           steps_per_epoch=None,)
    # #validation_steps=None,
    # #validation_freq=1)
    # a_test, b_test, mat_test = data_reader(FLAGS.test_dir)
    # x_test = image_matrix_creation(a_test, b_test)
    # y_test = mat_matrix_creation(mat_test)
    # [loss, mtr] = model.evaluate(x=x_test, y=y_test, batch_size=None, verbose=1, sample_weight=None, steps=None,)
    # print(loss, mtr)
    return loss, mtr


if __name__ == '__main__':
    train(64, 6)



    #datagen = ImageDataGenerator()
    # # load and iterate training dataset
    # train_it = datagen.flow_from_directory(FLAGS.input_dir, class_mode=None, batch_size=64)
    # # load and iterate validation dataset
    # val_it = datagen.flow_from_directory(FLAGS.val_dir, class_mode=None, batch_size=64)
    # # load and iterate test dataset
    # test_it = datagen.flow_from_directory(FLAGS.test_dir, class_mode='binary', batch_size=64)
    # model = build_model()
    # num_training_samples = len(a_train)