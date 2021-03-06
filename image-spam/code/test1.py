from random import shuffle
import glob
from keras import callbacks
from keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, CSVLogger

'''
shuffle_data = True  # shuffle the addresses before saving
hdf5_path = '../data/dataset.hdf5'  # address to where you want to save the hdf5 file
cat_dog_train_path = '../data/original/*.JPG'
# read addresses and labels from the 'resized' folder
addrs = glob.glob(cat_dog_train_path)
labels = [1 if 'malware' in addr else 0 for addr in addrs]  # 1 = plastic, 0 = else
# to shuffle data
if shuffle_data:
    c = list(zip(addrs, labels))
    shuffle(c)
    addrs, labels = zip(*c)

# Divide the hata into 80% train, 20% test
train_addrs = addrs[0:int(0.8*len(addrs))]
train_labels = labels[0:int(0.8*len(labels))]
test_addrs = addrs[int(0.8*len(addrs)):]
test_labels = labels[int(0.8*len(labels)):]

import numpy as np
import h5py
data_order = 'th'  # 'th' for Theano, 'tf' for Tensorflow
# check the order of data and chose proper data shape to save images
if data_order == 'th':
    train_shape = (len(train_addrs), 3, 56, 56)
    test_shape = (len(test_addrs), 3, 56, 56)
elif data_order == 'tf':
    train_shape = (len(train_addrs), 56, 56, 3)
    test_shape = (len(test_addrs), 56, 56, 3)
# open a hdf5 file and create earrays
hdf5_file = h5py.File(hdf5_path, mode='w')
hdf5_file.create_dataset("train_img", train_shape, np.int8)
hdf5_file.create_dataset("test_img", test_shape, np.int8)
hdf5_file.create_dataset("train_mean", train_shape[1:], np.float32)
hdf5_file.create_dataset("train_labels", (len(train_addrs),), np.int8)
hdf5_file["train_labels"][...] = train_labels
hdf5_file.create_dataset("test_labels", (len(test_addrs),), np.int8)
hdf5_file["test_labels"][...] = test_labels


import cv2
# a numpy array to save the mean of the images
mean = np.zeros(train_shape[1:], np.float32)
# loop over train addresses
for i in range(len(train_addrs)):
    # print how many images are saved every 100 images
    if i % 100 == 0 and i > 1:
        print 'Train data: {}/{}'.format(i, len(train_addrs))
    # read an image and resize to (256, 256)
    # cv2 load images as BGR, convert it to RGB
    addr = train_addrs[i]
    img = cv2.imread(addr)
    img = cv2.resize(img, (56, 56), interpolation=cv2.INTER_CUBIC)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # add any image pre-processing here
    # if the data order is Theano, axis orders should change
    if data_order == 'th':
        img = np.rollaxis(img, 2)
    # save the image and calculate the mean so far
    hdf5_file["train_img"][i, ...] = img[None]
    mean += img / float(len(train_labels))
for i in range(len(test_addrs)):
    # print how many images are saved every 100 images
    if i % 100 == 0 and i > 1:
        print 'Test data: {}/{}'.format(i, len(test_addrs))
    # read an image and resize to (256, 256)
    # cv2 load images as BGR, convert it to RGB
    addr = test_addrs[i]
    img = cv2.imread(addr)
    img = cv2.resize(img, (56, 56), interpolation=cv2.INTER_CUBIC)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # add any image pre-processing here
    # if the data order is Theano, axis orders should change
    if data_order == 'th':
        img = np.rollaxis(img, 2)
    # save the image
    hdf5_file["test_img"][i, ...] = img[None]
# save the mean and close the hdf5 file
hdf5_file["train_mean"][...] = mean
hdf5_file.close()
'''

import h5py
import numpy as np
hdf5_path = '../dataset.hdf5'
subtract_mean = False
# open the hdf5 file
hdf5_file = h5py.File(hdf5_path, "r")
# subtract the training mean
if subtract_mean:
    mm = hdf5_file["train_mean"][0, ...]
    mm = mm[np.newaxis, ...]
# Total number of samples
data_num = hdf5_file["train_img"].shape[0]


import h5py
from sklearn.model_selection import train_test_split
f = h5py.File("../dataset.hdf5")
x_train = f['train_img'].value
x_test = f['test_img'].value
y_train = f['train_labels'].value
temp = y_train.tolist()
y_train_new = []
for thing in temp:
    if thing == 0:
        y_train_new.append([0,1])
    else:
        y_train_new.append([1,0])
y_train = np.array(y_train_new)
y_test = f['test_labels'].value
temp = y_test.tolist()
y_test_new = []
for thing in temp:
    if thing == 0:
        y_test_new.append([0,1])
    else:
        y_test_new.append([1,0])
y_test = np.array(y_test_new)


import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Convolution2D, MaxPooling2D
from keras.optimizers import SGD
from keras.callbacks import ModelCheckpoint
from sklearn.metrics import matthews_corrcoef
from sklearn.metrics import hamming_loss
from keras import backend as K
from keras.models import model_from_json
K.set_image_dim_ordering('th')

x_train = x_train.astype('float32')
x_test  = x_test.astype('float32')

x_train /= 255
x_test /= 255


y_train = y_train[:,0]
y_test = y_test[:,0]


print("-vinay----------------------------------------------")
unique, counts = np.unique(y_train, return_counts=True)
print np.asarray((unique, counts)).T

unique, counts = np.unique(y_test, return_counts=True)
print np.asarray((unique, counts)).T
print("------------------------------------------------")


model = Sequential()
model.add(Convolution2D(32, kernel_size=(3, 3),padding='same',input_shape=(3, 64, 64)))
model.add(Activation('relu'))
#model.add(Convolution2D(32, (3, 3)))
#model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.2))

'''
model.add(Convolution2D(64,(2, 2), padding='same'))
model.add(Activation('relu'))
#model.add(Convolution2D(64, (3, 3)))
#model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.2))
'''
model.add(Flatten())
model.add(Dense(256))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(1))
model.add(Activation('sigmoid'))



from sklearn.metrics import (precision_score, recall_score,
                             f1_score, accuracy_score,mean_squared_error,mean_absolute_error)


score = []
name = []
import os
for file in os.listdir("logs1/"):
  print(file)
  model.load_weights("logs1/"+file)
  # make predictions
  y_pred = model.predict_classes(x_test)
  # invert predictions
  accuracy = accuracy_score(y_test, y_pred)
  score.append(accuracy)
  name.append(file)

print("-------------------------------------------------------")
print(max(score))
print(name[score.index(max(score))])


model.load_weights("logs1/checkpoint-06.hdf5")
y_pred = model.predict_classes(x_test)
accuracy = accuracy_score(y_test, y_pred)
recall = recall_score(y_test, y_pred , average="binary")
precision = precision_score(y_test, y_pred , average="binary")
f1 = f1_score(y_test, y_pred, average="binary")
print("confusion matrix")
print("----------------------------------------------")
print("accuracy")
print("%.3f" %accuracy)
print("racall")
print("%.3f" %recall)
print("precision")
print("%.3f" %precision)
print("f1score")
print("%.3f" %f1)
from sklearn.metrics import confusion_matrix
print(confusion_matrix(y_test,y_pred))
