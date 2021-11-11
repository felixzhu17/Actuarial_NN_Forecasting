import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from .data_methods import prepare_results, split_Y, linear_error


def get_NN_results(model, data, val_steps, test_steps, look_back, data_info, batch_size, epochs, executions=3, error_function=linear_error, data_name='transformed_data'):

    model.save_weights('temp.h5')  # Stores the weights

    if val_steps == 0:
        train_X = data['train_X']
        train_Y = data['train_Y']
    else:
        train_X = np.concatenate((data['train_X'], data['val_X']), axis=0)
        train_Y = np.concatenate((data['train_Y'], data['val_Y']), axis=0)

    full_X = np.concatenate((train_X, data['test_X']), axis=0)
    full_Y = np.concatenate((train_Y, data['test_Y']), axis=0)

    predictions = []

    for i in range(executions):

        # Retrain on training and validation
        print(f'Fitting: {i+1}')
        history = model.fit(x=train_X, y=train_Y, verbose=0, epochs=epochs, batch_size=batch_size, callbacks=[
                            tf.keras.callbacks.EarlyStopping("loss", patience=5)])
        predictions.append(model.predict(full_X, batch_size=batch_size))
        model.load_weights('temp.h5')

    full_pred_Y = np.mean(predictions, axis=0)
    full_actual_Y = full_Y

    pred_Y = split_Y(full_pred_Y, val_steps, test_steps)
    actual_Y = split_Y(full_actual_Y, val_steps, test_steps)

    data_length = len(data_info[data_name])

    train_results = prepare_results(pred_Y['train'], actual_Y['train'], error_function,
                                    data_info['target_variables'], data_info['Y_variables'])
    train_dates = data_info[data_name].index[look_back -
                                             1:(data_length - test_steps - val_steps)]
    train_dates = train_dates[-len(data['train_X']):]
    test_dates = data_info[data_name].index[(
        data_length - test_steps):]

    test_results = prepare_results(pred_Y['test'], actual_Y['test'], error_function, data_info['target_variables'],
                                   data_info['Y_variables'])

    if val_steps > 0:

        val_loss = []

        for _ in range(executions):
            val_history = model.fit(x=data['train_X'], y=data['train_Y'], verbose=0, epochs=epochs, batch_size=batch_size, validation_data=(
                data['val_X'], data['val_Y']), callbacks=[tf.keras.callbacks.EarlyStopping("loss", patience=5)])
            val_loss.append(val_history.history['val_loss'][-1])
            model.load_weights('temp.h5')

        val_loss = np.mean(val_loss)
        val_results = prepare_results(pred_Y['val'], actual_Y['val'], error_function,
                                      data_info['target_variables'], data_info['Y_variables'])
        val_dates = data_info[data_name].index[(len(
            data_info[data_name]) - test_steps - val_steps):(data_length - test_steps)]

        output = {'train': train_results, 'val': val_results, 'test': test_results, 'val_loss': val_loss,
                  'dates': {'train': train_dates, 'val': val_dates, 'test': test_dates}}

    else:
        output = {'train': train_results, 'test': test_results,
                  'dates': {'train': train_dates, 'test': test_dates}}

    return output


def visualize_loss(history, title):
    loss = history.history["loss"]
    epochs = range(len(loss))
    plt.figure()
    plt.plot(epochs, loss, "b", label="Training loss")
    try:
        val_loss = history.history["val_loss"]
        plt.plot(epochs, val_loss, "r", label="Validation loss")
    except:
        pass
    plt.title(title)
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.legend()
    plt.show()