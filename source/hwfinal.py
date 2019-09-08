# -*- coding: utf-8 -*-
"""pinojoke-piol-carlos.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1eykJEI_eYtrGqRoORVtcpqYz2PNJjG2-

#Gesture Identification from Inertial Sensors

##Download of segmented data
"""

import urllib.request
import os.path
import numpy as np

if not os.path.exists('X_janelas.npy'):
  urllib.request.urlretrieve('https://github.com/xpiolx/stanvcic_data/raw/master/X_janelas.npy?raw=true', 
                             'X_janelas.npy')
if not os.path.exists('Y_janelas.npy'):
  urllib.request.urlretrieve('https://github.com/xpiolx/stanvcic_data/blob/master/Y_janelas.npy?raw=true', 
                             'Y_janelas.npy')  
X = np.load('X_janelas.npy', allow_pickle=True)
y = np.load('Y_janelas.npy', allow_pickle=True)
train_len = int(y.shape[0]*8/10)
X_train, y_train, X_test, y_test = X[:train_len], y[:train_len], X[train_len:], y[train_len:]

"""##Feature Extraction Models"""

from sklearn.base import TransformerMixin
import numpy as np
import scipy.stats as stats

# roor mean square
def rms(x):
  x = np.array(x)
  return np.sqrt(np.mean(np.square(x)))
# square root amplitude
def sra(x):
  x = np.array(x)
  return np.mean(np.sqrt(np.absolute(x)))**2
# peak to peak value
def ppv(x):
  x = np.array(x)
  return np.max(x)-np.min(x)
# crest factor
def cf(x):
  x = np.array(x)
  return np.max(np.absolute(x))/rms(x)
# impact factor
def ifa(x):
  x = np.array(x)
  return np.max(np.absolute(x))/np.mean(np.absolute(x))
# margin factor
def mf(x):
  x = np.array(x)
  return np.max(np.absolute(x))/sra(x)
# shape factor
def sf(x):
  x = np.array(x)
  return rms(x)/np.mean(np.absolute(x))
# kurtosis factor
def kf(x):
  x = np.array(x)
  return stats.kurtosis(x)/(np.mean(x**2)**2)

class StatisticalTime(TransformerMixin):
  def __init__(self):
    pass
  def fit(self, X, y=None):
    return self
  def transform(self, X, y=None):
    features = None
    for signal in range(X_train.shape[2]):
      feats = np.array([[rms(x), sra(x), stats.kurtosis(x), stats.skew(x), ppv(x), cf(x), ifa(x), mf(x), sf(x), kf(x)] for x in X[:,:,signal]])
      if features is None:
        features = feats
      else:
        features = np.concatenate((features,feats),axis=1)
    return features
  
class StatisticalFrequency(TransformerMixin):
  def __init__(self):
    pass
  def fit(self, X, y=None):
    return self
  def transform(self, X, y=None):
    features = None
    for signal in range(X_train.shape[2]):
      featarray = []
      for x in X[:,:,signal]:
        fx = np.absolute(np.fft.fft(x))
        fc = np.mean(fx)
        featarray.append([fc, rms(fx), rms(fx-fc)])
      feats = np.array(featarray)
      if features is None:
        features = feats
      else:
        features = np.concatenate((features,feats),axis=1)
    return features

class Statistical(TransformerMixin):
  def __init__(self):
    pass
  def fit(self, X, y=None):
    return self
  def transform(self, X, y=None):
    st = StatisticalTime()
    stfeats = st.transform(X)
    sf = StatisticalFrequency()
    sffeats = sf.transform(X)
    return np.concatenate((stfeats,sffeats),axis=1)
   
import pywt
class WaveletPackage(TransformerMixin):
  def __init__(self):
    pass
  def fit(self, X, y=None):
    return self
  def transform(self, X, y=None):
    def Energy(coeffs, k):
      return np.sqrt(np.sum(np.array(coeffs[-k]) ** 2)) / len(coeffs[-k])
    def getEnergy(wp):
      coefs = np.asarray([n.data for n in wp.get_leaf_nodes(True)])
      return np.asarray([Energy(coefs,i) for i in range(2**wp.maxlevel)])
    features = None
    for signal in range(X_train.shape[2]):
      feats = np.array([getEnergy(pywt.WaveletPacket(data=x, wavelet='db4', mode='symmetric', maxlevel=4)) for x in X[:,:,signal]])
      if features is None:
        features = feats
      else:
        features = np.concatenate((features,feats),axis=1)
    return features

class Heterogeneous(TransformerMixin):
  def __init__(self):
    pass
  def fit(self, X, y=None):
    return self
  def transform(self, X, y=None):
    st = StatisticalTime()
    stfeats = st.transform(X)
    sf = StatisticalFrequency()
    sffeats = sf.transform(X)
    wp = WaveletPackage()
    wpfeats = wp.transform(X)
    return np.concatenate((stfeats,sffeats,wpfeats),axis=1)

"""## Adaptation to no extract features"""

class SignalAdapter(TransformerMixin):
    def __init__(self):
      pass
    def fit(self, X, y=None):
      return self
    def transform(self, X, y=None):
      return X.reshape(X.shape[0],-1)

"""## Function to plot confusion matrix"""

import itertools
from sklearn.metrics import confusion_matrix
from matplotlib import pyplot as plt

def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Greys):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    #print(cm)

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    #plt.title(title)
    #plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('Classe verdadeira')
    plt.xlabel('Classe estimada')

"""##3-dimentional Standar Scaler"""

import numpy as np
from sklearn.base import TransformerMixin
from sklearn.preprocessing import StandardScaler


class NDStandardScaler(TransformerMixin):
    def __init__(self):
        self._scaler = StandardScaler(copy=True)
        self._orig_shape = None

    def fit(self, X, y=None):
        X = np.array(X)
        # Save the original shape to reshape the flattened X later
        # back to its original shape
        if len(X.shape) > 1:
            self._orig_shape = X.shape[1:]
        X = self._flatten(X)
        self._scaler.fit(X)
        return self

    def transform(self, X, y=None):
        X = np.array(X)
        X = self._flatten(X)
        X = self._scaler.transform(X)
        X = self._reshape(X)
        return X

    def _flatten(self, X):
        # Reshape X to <= 2 dimensions
        if len(X.shape) > 2:
            n_dims = np.prod(self._orig_shape)
            X = X.reshape(-1, n_dims)
        return X

    def _reshape(self, X):
        # Reshape X back to it's original shape
        if len(X.shape) >= 2:
            X = X.reshape(-1, *self._orig_shape)
        return X

"""## F1-Score macro for Keras"""

from keras import backend as K
def f1_score_macro(y_true,y_pred):
    def recall(y_true, y_pred):
        true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
        recall = true_positives / (possible_positives + K.epsilon())
        return recall
    def precision(y_true, y_pred):
        true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
        precision = true_positives / (predicted_positives + K.epsilon())
        return precision
    precision = precision(y_true, y_pred)
    recall = recall(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))

"""## ANN definition"""

from keras import layers
from keras import Input
from keras.models import Model
from keras.callbacks import EarlyStopping,ReduceLROnPlateau
from keras.utils import to_categorical

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils import shuffle
class ANNConv1D(BaseEstimator, ClassifierMixin):
  def __init__(self, filters=16, kernel_size=22, shape=X_train.shape):
    self.shape = shape
    self.filters = filters
    self.kernel_size = kernel_size

  def fit(self, X, y=None):
    y_cat = to_categorical(y)
    signal_input = Input(shape=(self.shape[1],self.shape[-1]),
                         dtype='float32', name='signal')
    x = layers.Conv1D(filters=self.filters, 
                      kernel_size=self.kernel_size, 
                      activation='relu', 
                      name='conv1d_1')(signal_input)
    x = layers.MaxPooling1D(self.kernel_size, 
                            name='max_pooling1d_1')(x)
    x = layers.Flatten(name='flatten')(x)
    condition_output = layers.Dense(7,activation='softmax',
                                    name='condition')(x)
    self.model = Model(signal_input, condition_output) 
    self.model.compile(optimizer='rmsprop',
                       loss='mean_squared_error', 
                       metrics=['accuracy',f1_score_macro])
      
    self.history = self.model.fit(X ,y_cat, epochs=50, 
                                  validation_split=0.3,
                                  callbacks=[EarlyStopping(patience=3),
                                             ReduceLROnPlateau()],
                                  verbose=1)
    return self

  def predict(self, X, y=None):
    return np.argmax(self.model.predict(X), axis=1)

"""## Setup of pipelines and grid searches"""

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import StratifiedKFold

# K-NN with Feateure Extraction
p_knn = Pipeline([('feature_extraction', Heterogeneous()),
                  ('std_scaler', StandardScaler()),
                  ('knn', KNeighborsClassifier()),
                 ])
grid_knn = GridSearchCV(p_knn, param_grid={"knn__n_neighbors": [1,3,5,7,9,11]}, 
                        cv=StratifiedKFold(3), verbose=2)

# Random Forest without Feature Extraction
p_rf = Pipeline([('signal_adapter', SignalAdapter()),
                 ('std_scaler', StandardScaler()),
                 ('rf', RandomForestClassifier()),
                ])
grid_rf = GridSearchCV(p_rf, param_grid={"rf__n_estimators": [10, 20], 
                                         "rf__max_features": [4, 8, None],
                                        },
                       cv=StratifiedKFold(3), verbose=2)

# Random Forest with Feature Extraction
p_rf_wfe = Pipeline([('feature_extraction', Heterogeneous()),
                 ('std_scaler', StandardScaler()),
                 ('rf', RandomForestClassifier()),
                ])
grid_rf_wfe = GridSearchCV(p_rf_wfe, param_grid={"rf__n_estimators": [10, 20],
                                                 "rf__max_features": [4, 8, None],
                                                },
                           cv=StratifiedKFold(3), verbose=2)

# Artificial Neural Network - Conv1d
p_ann = Pipeline([('std_scaler', NDStandardScaler()),
                  ('conv1d', ANNConv1D(shape=X_train.shape)),
                 ])
grid_ann = GridSearchCV(p_ann, 
                        param_grid={'conv1d__filters': [64, 128], 
                                    'conv1d__kernel_size': [13, 27, 55],
                                   }, 
                        cv=StratifiedKFold(3), verbose=2)

# List of Classifiers
clfs = [("K-NN with Feateure Extraction", grid_knn),
        ("Random Forest without Feature Extraction", grid_rf),
        ("Random Forest with Feature Extraction", grid_rf_wfe),
        ("Artificial Neural Network - Conv1d", grid_ann),
       ]

"""## Perform the experiments"""

from sklearn.metrics import f1_score, accuracy_score

class_names = list(set(y_train))
class_names = ['Neutral', 'Gesture 1', 'Gesture 2', 'Gesture 3', 'Gesture 4', 'Gesture 5', 'Gesture 6']
figprop = np.linspace(1, 0.5, 25)
tam = len(class_names) * figprop[len(class_names)]


results = {}
models = {}
genconfmat = True
results['st'] = {}
models['st'] = {}

for clfname, model in clfs:
    print(clfname, end=":\t")
    '''
    if not clfname in results['st']:
        results['st'][clfname] = []
    '''
    history = model.fit(X_train ,y_train)
    print(model.best_params_)
    '''
    y_pred = model.predict(X_test)
    results['st'][clfname].append([accuracy_score(y_test,y_pred),f1_score(y_test,y_pred,average='macro')])
    print(results['st'][clfname][-1])
    if genconfmat:
        cnf_matrix = confusion_matrix(y_test, y_pred)
        print(cnf_matrix)
        plt.figure(figsize=(tam,tam))
        plot_confusion_matrix(cnf_matrix, classes=class_names, title=clfname, normalize=False)
        plt.show()
        plot_confusion_matrix(cnf_matrix, classes=class_names, title=clfname, normalize=True)
        #plt.savefig('cnfmatrix_st'+clfname+str(fold)+'round'+str(j)+'.png')
        plt.show()
    '''

"""# Ploting Confusion Matrices"""

results = {}
models = {}
genconfmat = True
results['st'] = {}

for clfname, model in clfs:
    print(clfname, end=":\t")
    if not clfname in results['st']:
        results['st'][clfname] = []
    y_pred = model.predict(X_test)
    results['st'][clfname].append([accuracy_score(y_test,y_pred),f1_score(y_test,y_pred,average='macro')])
    print(results['st'][clfname][-1])
    if genconfmat:
        cnf_matrix = confusion_matrix(y_test, y_pred)
        print(cnf_matrix)
        plt.figure(figsize=(tam,tam))
        plot_confusion_matrix(cnf_matrix, classes=class_names, title=clfname, normalize=False)
        plt.show()
        plot_confusion_matrix(cnf_matrix, classes=class_names, title=clfname, normalize=True)
        #plt.savefig('cnfmatrix_st'+clfname+str(fold)+'round'+str(j)+'.png')
        plt.show()

"""## Display Results"""

print(y_test.shape)
for evaluation in results.keys():
  print("\n"+30*"#"+"\n"+evaluation+"\n"+30*"#")
  for clfname,model in clfs:
    print("\n\t"+clfname+" Results\nAccuracy\tF1-Score")
    for i,r in enumerate(results[evaluation][clfname]):
      print("{}\t".format(i+1),end="")
      print(r)