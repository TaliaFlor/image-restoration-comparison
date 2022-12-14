# -*- coding: utf-8 -*-
"""Restauração de Imagens com Deep Learning: Uma Comparação entre Técnicas.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1a_V8JgDADzc4DnRziOVm9FWgQwrsLeOf

# Fetch Dataset

Downloads and unzips the data
"""

!wget https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/BSR/BSR_full.tgz

!tar zxvf BSR_full.tgz

"""Moves the data"""

!mkdir BSD/

!mv ./BSR/BSDS500/data/images/* BSD/

"""Removes old files and folders"""

!rm -r ./BSR_full.tgz ./sample_data/ ./BSR/

"""# Imports"""

!python --version

import time

import numpy as np
import tensorflow as tf

from tensorflow.keras import layers, losses, Sequential
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Layer
from tensorflow.keras import backend as K
from typing import Any, Tuple, List
from dataclasses import dataclass

"""# Variables"""

WIDTH: int = 128       # pixels
HEIGHT: int = 128      # pixels
COLORS: int = 3        # 3 - colors; 1 - gray scale

PATH: str = 'BSD'
EXT: str = 'jpg'

TRAIN_DIR: str = 'train'
VAL_DIR: str = 'val'
TEST_DIR: str = 'test'

NUM_IMGS_TO_SHOW: int = 5
FIGSIZE: Tuple[float, float] = (20, 4)

EPOCHS: int = 100

"""# Dataclasses

## Dataset
"""

@dataclass
class Dataset:
  x_train: np.ndarray
  x_val: np.ndarray
  x_test: np.ndarray

  def print_info(self) -> None:
    print(self.x_train.shape)
    print(self.x_val.shape)
    print(self.x_test.shape)

    print(type(self.x_train.dtype))
    print(type(self.x_val.dtype))
    print(type(self.x_test.dtype))

"""# Functions

## Misc

### Display Duration
"""

def display_duration(start, end) -> None:
  duration = divmod(end - start, 60)
  print('\n--------------------------------------------------------------')
  print(f'Duration: {duration[0]} minutes and {duration[1]} seconds')
  print('--------------------------------------------------------------\n')

"""## Dataset

### Load Dataset
"""

import glob
from PIL import Image


def _load_data(dir: str) -> np.ndarray:
  imgs = []
  for file in glob.glob(f'./{PATH}/{dir}/*.{EXT}'):
    img = Image.open(file)
    img = img.resize((WIDTH, HEIGHT))
    img = np.array(img)
    img = img.astype('float32')
    
    if COLORS == 1:         # gray scale
      img = img[:, :, 0]
    

    imgs.append(img)

  return np.array(imgs, dtype=np.float32) / 255.0



def load_dataset() -> Dataset:
  x_train: np.ndarray = _load_data(TRAIN_DIR)
  x_val: np.ndarray = _load_data(VAL_DIR)
  x_test: np.ndarray = _load_data(TEST_DIR)

  return Dataset(x_train, x_val, x_test)

"""### Create Noisy Data"""

def _create_noisy_data(data: np.ndarray, noise_factor: float) -> np.ndarray:
  # adds noise
  noisy_data = data + (noise_factor * np.random.normal(size=data.shape)) 
  
  # normalize the noise factor
  noisy_data = np.clip(noisy_data, a_min=0.0, a_max=1.0)

  return noisy_data.astype('float32')


def create_noisy_dataset(dataset: Dataset, noise_factor: float = 0.2) -> Dataset:
  x_train_noisy = _create_noisy_data(dataset.x_train, noise_factor)
  x_val_noisy = _create_noisy_data(dataset.x_val, noise_factor)
  x_test_noisy = _create_noisy_data(dataset.x_test, noise_factor)

  return Dataset(x_train_noisy, x_val_noisy, x_test_noisy)

"""### Get Data"""

def get_data() -> Tuple[Dataset, Dataset]:
  dataset: Dataset = load_dataset()
  noisy_dataset: Dataset = create_noisy_dataset(dataset)

  return dataset, noisy_dataset

"""## Graphs

### Display Outputs
"""

import math
import matplotlib.pyplot as plt
from matplotlib.axes import Axes


def display_output(label: str, data: np.ndarray) -> None:
  plt.figure(figsize=FIGSIZE)
  
  for i in range(NUM_IMGS_TO_SHOW):
    # creates the image
    ax: Axes = plt.subplot(1, NUM_IMGS_TO_SHOW, i + 1)
    plt.imshow(data[i])
    
    # sets the color map to gray if image is in gray scale
    if COLORS == 1:
      plt.gray()

    # disables the axis lines
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    # adds the title if figure is the middle one
    if i == math.floor(NUM_IMGS_TO_SHOW / 2):
      ax.set_title(label)

  plt.show()

"""### Display Noisy Data"""

def display_noisy_data(noisy_dataset: Dataset) -> None:
  display_output('Original + Noise', noisy_dataset.x_test)

"""### Display Results"""

def display_results(dataset: Dataset, noisy_dataset: Dataset, decoded_imgs: np.ndarray) -> None:
  items: List[Tuple[str, np.ndarray]] = [
      ('Original', dataset.x_test),
      ('Original + Noise', noisy_dataset.x_test),
      ('Reconstructed', decoded_imgs)
  ]

  # display output
  for item in items:
    display_output(item[0], item[1])

"""## Model

### Train Model
"""

def train_model(model: Model, dataset: Dataset, noisy_dataset: Dataset) -> Model:
  # train
  start = time.time()             # seconds

  model.fit(
      x=noisy_dataset.x_train,
      y=dataset.x_train,
      epochs=EPOCHS,
      shuffle=True,
      validation_data=(noisy_dataset.x_val, dataset.x_val)
  )

  end = time.time()

  # display elapsed time
  display_duration(start, end)

  return model

"""# Models

## Shallow Autoencoder

### Load Data
"""

# load data
dataset, noisy_dataset = get_data()
display_noisy_data(noisy_dataset)

"""### Configure Model"""

# local variables
LATENT_DIM: int = 512


# configure model
class ShallowAutoencoder(Model):
  def __init__(self):
    super().__init__(name='shallow_autoencoder')
    
    self.encoder = Sequential([
      layers.Flatten(),
      layers.Dense(LATENT_DIM, activation='relu', name='code'),
    ], name='encoder')

    self.decoder = Sequential([
      layers.Dense(WIDTH * HEIGHT * COLORS, activation='sigmoid'),
      layers.Reshape((WIDTH, HEIGHT, COLORS))
    ], name='decoder')

  def call(self, x):
    encoded = self.encoder(x)
    decoded = self.decoder(encoded)
    return decoded


# compile model
model = ShallowAutoencoder() 
model.compile(optimizer='adam', loss=losses.MeanSquaredError())

"""### Train Model"""

# train model
train_model(model, dataset, noisy_dataset)

"""### Display Model Summary"""

model.summary()

model.encoder.summary()

model.decoder.summary()

"""### Test Model"""

# test model
start = time.time()

encoded_imgs = model.encoder(noisy_dataset.x_test).numpy()
decoded_imgs = model.decoder(encoded_imgs).numpy()

end = time.time()


# display elapsed time
display_duration(start, end)

"""### Display Results"""

display_results(dataset, noisy_dataset, decoded_imgs)

"""## Convolutional Denoising Autoencoder

### Load Data
"""

# load data
dataset, noisy_dataset = get_data()
display_noisy_data(noisy_dataset)

"""### Configure Model"""

# local variables
PADDING: str = 'same'
ACTIVATION: str = 'relu'

KERNEL_SIZE: int = 3
STRIDES: int = 2

LAYER_1: int = 128
LAYER_2: int = 64
LAYER_3: int = 32


# configure model
class ConvolutionalDenoisingAutoencoder(Model):
  def __init__(self):
    super().__init__(name='convolutional_denoising_autoencoder')

    self.encoder = Sequential([
      layers.Input(shape=(WIDTH, HEIGHT, COLORS), name='input'),
      layers.Conv2D(LAYER_1, KERNEL_SIZE, STRIDES, activation=ACTIVATION, padding=PADDING, name='layer_1'),
      layers.Conv2D(LAYER_2, KERNEL_SIZE, STRIDES, activation=ACTIVATION, padding=PADDING, name='layer_2'),
      layers.Conv2D(LAYER_3, KERNEL_SIZE, STRIDES, activation=ACTIVATION, padding=PADDING, name='layer_3'),
    ], name='encoder')

    self.decoder = Sequential([
      layers.Conv2DTranspose(LAYER_3, KERNEL_SIZE, STRIDES, activation=ACTIVATION, padding=PADDING, name='layer_3'),
      layers.Conv2DTranspose(LAYER_2, KERNEL_SIZE, STRIDES, activation=ACTIVATION, padding=PADDING, name='layer_2'),
      layers.Conv2DTranspose(LAYER_1, KERNEL_SIZE, STRIDES, activation=ACTIVATION, padding=PADDING, name='layer_1'),
      layers.Conv2D(COLORS, kernel_size=1, activation='sigmoid', padding=PADDING, name='output')
    ], name='decoder')

  def call(self, x):
    encoded = self.encoder(x)
    decoded = self.decoder(encoded)
    return decoded


# compile model
model = ConvolutionalDenoisingAutoencoder()
model.compile(optimizer='adam', loss=losses.MeanSquaredError())

"""### Train Model"""

# train model
train_model(model, dataset, noisy_dataset)

"""### Display Model Summary"""

model.summary()

model.encoder.summary()

model.decoder.summary()

"""### Test Model"""

# test model
start = time.time()

encoded_imgs = model.encoder(noisy_dataset.x_test).numpy()
decoded_imgs = model.decoder(encoded_imgs).numpy()

end = time.time()


# display elapsed time
display_duration(start, end)

"""### Display Results"""

display_results(dataset, noisy_dataset, decoded_imgs)

"""## SegNet

Deep Convolutional Autoencoder With No Fully Connected Layer

### Load Data
"""

# load data
dataset, noisy_dataset = get_data()
display_noisy_data(noisy_dataset)

"""### Configure Model"""

# local variables
PADDING: str = 'same'
ACTIVATION: str = 'relu'

KERNEL_SIZE: int = 3
STRIDES: int = 2
POOL_SIZE: int = 2

BLOCK_1: int = 64
BLOCK_2: int = 128
BLOCK_3: int = 256



# layers
class MaxPoolingWithArgmax2D(Layer):
    def __init__(self, name = None, **kwargs):
        super().__init__(name=name, **kwargs)

    def call(self, inputs, **kwargs):
        ksize = [1, POOL_SIZE, POOL_SIZE, 1]
        strides = [1, STRIDES, STRIDES, 1]
        
        output, argmax = tf.nn.max_pool_with_argmax(
            inputs, ksize=ksize, strides=strides, padding='SAME'
        )
        argmax = K.cast(argmax, K.floatx())
        
        return [output, argmax]

    def compute_output_shape(self, input_shape):
        ratio = (1, 2, 2, 1)
        output_shape = [
            dim // ratio[idx] if dim is not None else None
            for idx, dim in enumerate(input_shape)
        ]
        output_shape = Tuple(output_shape)
        return [output_shape, output_shape]

    def compute_mask(self, inputs, mask=None):
        return 2 * [None]

class MaxUnpooling2D(Layer):
    def __init__(self, name = None, **kwargs):
        super().__init__(name=name, **kwargs)

    def call(self, inputs, output_shape=None):
        updates, mask = inputs[0], inputs[1]
        with tf.compat.v1.variable_scope(self.name):
            mask = K.cast(mask, "int32")
            input_shape = tf.shape(updates)
            #  calculation new shape
            if output_shape is None:
                output_shape = (
                    input_shape[0],
                    input_shape[1] * POOL_SIZE,
                    input_shape[2] * POOL_SIZE,
                    input_shape[3],
                )
            self.output_shape1 = output_shape

            # calculation indices for batch, height, width and feature maps
            one_like_mask = K.ones_like(mask, dtype="int32")
            batch_shape = K.concatenate([[input_shape[0]], [1], [1], [1]], axis=0)
            batch_range = K.reshape(
                tf.range(output_shape[0], dtype="int32"), shape=batch_shape
            )
            b = one_like_mask * batch_range
            y = mask // (output_shape[2] * output_shape[3])
            x = (mask // output_shape[3]) % output_shape[2]
            feature_range = tf.range(output_shape[3], dtype="int32")
            f = one_like_mask * feature_range

            # transpose indices & reshape update values to one dimension
            updates_size = tf.size(updates)
            indices = K.transpose(K.reshape(K.stack([b, y, x, f]), [4, updates_size]))
            values = K.reshape(updates, [updates_size])
            ret = tf.scatter_nd(indices, values, output_shape)
            return ret

    def compute_output_shape(self, input_shape):
        mask_shape = input_shape[1]
        return (
            mask_shape[0],
            mask_shape[1] * POOL_SIZE,
            mask_shape[2] * POOL_SIZE,
            mask_shape[3],
        )


# configure model
def segnet():
  # input
  inputs = layers.Input(shape=(WIDTH, HEIGHT, COLORS), name='input')
  
  
  # encoder
  x = layers.Conv2D(BLOCK_1, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_1_layer_1_encoder')(inputs)
  x = layers.BatchNormalization()(x)
  x = layers.Conv2D(BLOCK_1, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_1_layer_2_encoder')(x)
  x = layers.BatchNormalization()(x)
  pool_1, mask_1 = MaxPoolingWithArgmax2D(name='pool_1')(x)
  
  x = layers.Conv2D(BLOCK_2, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_2_layer_3_encoder')(pool_1)
  x = layers.BatchNormalization()(x)
  x = layers.Conv2D(BLOCK_2, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_2_layer_4_encoder')(x)
  x = layers.BatchNormalization()(x)
  pool_2, mask_2 = MaxPoolingWithArgmax2D(name='pool_2')(x)
  
  x = layers.Conv2D(BLOCK_3, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_3_layer_5_encoder')(pool_2)
  x = layers.BatchNormalization()(x)
  x = layers.Conv2D(BLOCK_3, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_3_layer_6_encoder')(x)
  x = layers.BatchNormalization()(x)
  x = layers.Conv2D(BLOCK_3, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_3_layer_7_encoder')(x)
  x = layers.BatchNormalization()(x)
  pool_3, mask_3 = MaxPoolingWithArgmax2D(name='pool_3')(x)
  
  
  # decoder
  unpool_3 = MaxUnpooling2D(name='unpool_3')([pool_3, mask_3])
  x = layers.Conv2DTranspose(BLOCK_3, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_3_layer_7_decoder')(unpool_3)
  x = layers.BatchNormalization()(x)
  x = layers.Conv2DTranspose(BLOCK_3, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_3_layer_6_decoder')(x)
  x = layers.BatchNormalization()(x)
  x = layers.Conv2DTranspose(BLOCK_3, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_3_layer_5_decoder')(x)
  x = layers.BatchNormalization()(x)
  
  x = layers.Conv2DTranspose(BLOCK_2, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_2_layer_4_decoder')(x)
  x = layers.BatchNormalization()(x)


  unpool_2 = MaxUnpooling2D(name='unpool_2')([x, mask_2])
  x = layers.Conv2DTranspose(BLOCK_2, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_2_layer_3_decoder')(unpool_2)
  x = layers.BatchNormalization()(x)
  
  x = layers.Conv2DTranspose(BLOCK_1, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_1_layer_2_decoder')(x)
  x = layers.BatchNormalization()(x)


  unpool_1 = MaxUnpooling2D(name='unpool_1')([x, mask_1])
  x = layers.Conv2DTranspose(BLOCK_1, KERNEL_SIZE, activation=ACTIVATION, padding=PADDING, name='block_1_layer_1_decoder')(unpool_1)
  x = layers.BatchNormalization()(x)


  # output
  x = layers.Conv2D(COLORS, kernel_size=1, activation=ACTIVATION, padding='valid', name='output')(x)
  x = layers.BatchNormalization()(x)
  x = layers.Reshape((WIDTH, HEIGHT, COLORS), name='reshape')(x)
  outputs = layers.Activation(activation='sigmoid')(x)


  return Model(inputs, outputs, name="SegNet")




# compile model
model = segnet()
model.compile(optimizer='adam', loss=losses.MeanSquaredError())

"""### Train Model"""

# train model
train_model(model, dataset, noisy_dataset)

"""### Display Model Summary"""

model.summary()

"""### Test Model"""

# test model
start = time.time()
decoded_imgs = model(noisy_dataset.x_test).numpy()
end = time.time()

# display elapsed time
display_duration(start, end)

"""### Display Results"""

display_results(dataset, noisy_dataset, decoded_imgs)

"""## U-Net

Convolutional Network with Max Pooling

### Load Data
"""

# load data
dataset, noisy_dataset = get_data()
display_noisy_data(noisy_dataset)

"""### Configure Model"""

# local variables
LAYER_DEPTH: int = 3              # total depth of unet

NUM_FILTERS_ROOT: int = 64        # number of filters in top unet layer 
KERNEL_SIZE: int = 3              # size of convolutional layers
PADDING: str = 'same'             # padding to be used in convolutions
ACTIVATION: str = 'relu'          # activation to be used
POOL_SIZE: int = 2                # size of maxplool layers
STRIDES: int = 1

NUM_BLOCKS: int = 2



# functions
def _get_filter_count(layer_idx: int) -> int:
    return (2 ** layer_idx) * NUM_FILTERS_ROOT


# layers
class ConvBlock(Layer):
  def __init__(self, layer_idx: int, name = None, **kwargs):
    super().__init__(name=name, **kwargs)

    self.layer_idx = layer_idx

    self.convs = []

    num_filters = _get_filter_count(layer_idx)
    for _ in range(NUM_BLOCKS):
      conv = layers.Conv2D(num_filters, KERNEL_SIZE, STRIDES, PADDING, activation=ACTIVATION)
      self.convs.append(conv)

  def call(self, inputs, **kwargs):
    x = inputs
    for conv in self.convs:
      x = conv(x)
    return x

class UpconvBlock(Layer):
  def __init__(self, layer_idx: int, name = None, **kwargs):
    super().__init__(name=name, **kwargs)

    self.layer_idx = layer_idx

    num_filters = _get_filter_count(layer_idx + 1)
    self.upconv = layers.Conv2DTranspose(num_filters // 2,
                                          kernel_size=POOL_SIZE,
                                          strides=POOL_SIZE,
                                          padding=PADDING,
                                          activation=ACTIVATION)

  def call(self, inputs, **kwargs):
    return self.upconv(inputs)

class CropConcatBlock(Layer):
  def __init__(self, name = None, **kwargs):
    super().__init__(name=name, **kwargs)

  def call(self, x, down_layer, **kwargs):
    x1_shape = tf.shape(down_layer)
    x2_shape = tf.shape(x)

    height_diff = (x1_shape[1] - x2_shape[1]) // 2
    width_diff = (x1_shape[2] - x2_shape[2]) // 2

    down_layer_cropped = down_layer[:,
                                    height_diff: (x2_shape[1] + height_diff),
                                    width_diff: (x2_shape[2] + width_diff),
                                    :]

    x = tf.concat([down_layer_cropped, x], axis=-1)
    return x


# configure model
def unet():
  layer_idx = 0
  contracting_layers = []

  # input
  inputs = layers.Input(shape=(WIDTH, HEIGHT, COLORS), name='input')

  # encoder
  x = inputs
  for layer_idx in range(LAYER_DEPTH):
    x = ConvBlock(layer_idx, name=f'conv_{layer_idx + 1}_encoder')(x)
    contracting_layers.append(x)
    x = layers.MaxPooling2D(POOL_SIZE, name=f'pool_{layer_idx + 1}_encoder')(x)

  # code
  x = ConvBlock(layer_idx + 1, name='code')(x)

  # decoder
  for layer_idx in range(layer_idx, -1, -1):
    x = UpconvBlock(layer_idx, name=f'upconv_{layer_idx + 1}_decoder')(x)
    x = CropConcatBlock(name=f'crop_{layer_idx + 1}_decoder')(x, contracting_layers[layer_idx])
    x = ConvBlock(layer_idx, name=f'conv_{layer_idx + 1}_decoder')(x)

  # output
  x = layers.Conv2D(COLORS, kernel_size=1, padding='valid', activation=ACTIVATION, name='output')(x)
  x = layers.BatchNormalization()(x)
  outputs = layers.Activation(activation='sigmoid')(x)
  
  
  return Model(inputs, outputs, name="U-Net")



# compile model
model = unet()
model.compile(optimizer='adam', loss=losses.MeanSquaredError())

"""### Train Model"""

# train model
train_model(model, dataset, noisy_dataset)

"""### Display Model Summary"""

model.summary()

"""### Test Model"""

# test model
start = time.time()
decoded_imgs = model(noisy_dataset.x_test).numpy()
end = time.time()

# display elapsed time
display_duration(start, end)

"""### Display Results"""

display_results(dataset, noisy_dataset, decoded_imgs)