# -*- coding: utf-8 -*-
"""BiLSTM_CRF.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Q1l22Rg4VecRR0h-M_QG7yWDutbOVwdz
"""

!pip install tf2crf

pip install -U 'scikit-learn<0.24'

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
import matplotlib.pyplot as plt
plt.style.use('ggplot')

from itertools import chain
import numpy as np

import nltk
import sklearn
import scipy.stats
from sklearn.metrics import make_scorer
from sklearn.model_selection import cross_val_score
from nltk.tokenize import word_tokenize
import numpy as np

import keras 
from tf2crf import CRF 
from tf2crf import ModelWithCRFLoss

from keras.models import Sequential,Model
from keras.layers import LSTM,Bidirectional,Dense,Input,Embedding,TimeDistributed
from keras.callbacks import EarlyStopping, ModelCheckpoint

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

from google.colab import drive,files
drive.mount("/content/drive")
dataM='/content/drive/My Drive/Colab Notebooks/MODELS/'
filepath = dataM+'BiLSTM_CRF.ml'

XTr=['Google wants a backend developer with good coding skills','There is a position open for machine learning engineer, Meta is looking for people with machine learning background']
XVal=['Amazon is looking for DevOps engineer']
org_b={'google':'C','amazon':'C','meta':'C','microsoft':'C','qualcomm':'C'}
skills_b={'coding':'S','machine':'S','learning':'S'}
jobs_b={'backend':'J','developer':'J','engineer':'J','manager':'J','devops':'J'}

def make(X,org_b,skills_b,jobs_b):
  big=[]
  for sentence in X:
    token=word_tokenize(sentence)
    small=[]
    token_t=nltk.pos_tag(token)
    for f,s in token_t:
      tag='O'
      if f.lower() in org_b:
        tag=org_b[f.lower()]
      if f.lower() in skills_b:
        tag=skills_b[f.lower()]
      if f.lower() in jobs_b:
        tag=jobs_b[f.lower()]
      small.append((f,s,tag))
    big.append(small)
  return big
XTr_=make(XTr,org_b,skills_b,jobs_b)
XVal_=make(XVal,org_b,skills_b,jobs_b)

msgLen=10

def fixMsg(X):
  global msgLen
  Xc=[]
  for i in range(len(X)):
    if len(X[i])<msgLen:
      while len(X[i])<msgLen:
        X[i].append(('UNK','UNK','UNK'))
    elif len(X[i])>msgLen:
      temp=X[i]
      del X[i]
      lb=0;chunk=msgLen
      while lb<len(temp):
        split=[]
        for j in range(lb,lb+chunk):
          if j<len(temp):
            split.append(temp[j])
          else:
            split.append(('UNK','UNK','UNK'))
        X.append(split)
        print(X)
        lb+=chunk
  return X 

XTr_t=fixMsg(XTr_)
XVal_t=fixMsg(XVal_)

for x in XTr_t:
  assert(len(x)==msgLen)
print(XTr_t)
for x in XVal_t:
  assert(len(x)==msgLen)
print(XVal_t)

dict_={}
dict_1={}
token=1;token1=0
for x in XTr_t:
  for a,b,c in x:
    if a not in dict_:
      dict_[a]=token
      token=token+1
    if c not in dict_1:
      if c=='K':
        print(a,b,c)
      dict_1[c]=token1
      token1=token1+1
for x in XVal_t:
  for a,b,c in x:
    if a not in dict_:
      dict_[a]=token
      token=token+1
    if c not in dict_1:
      dict_1[c]=token1
      token1=token1+1
print('No of tokens words[{}] labels[{}]'.format(token,token1))

XTr_fin=np.array([[dict_[element[0]] for element in sentence] for sentence in XTr_t])
XVal_fin=np.array([[dict_[element[0]] for element in sentence] for sentence in XVal_t])

yTr=np.array([[dict_1[element[2]] for element in sentence] for sentence in XTr_t])
yVal=np.array([[dict_1[element[2]] for element in sentence] for sentence in XVal_t])

embedding_dim = 100
input=Input(shape=(msgLen,))
mo=Embedding(input_dim=token,output_dim=embedding_dim)(input)
frwd=LSTM(64,return_sequences=True)
back=LSTM(64,return_sequences=True,go_backwards=True)
mo=Bidirectional(frwd,backward_layer=back)(mo)
mo=TimeDistributed(Dense(32,activation='relu'))(mo)
output=CRF(units=token1)(mo)
mo=Model(input,output)
mo.summary()

model=ModelWithCRFLoss(mo, sparse_target=True)
model.compile(optimizer ='rmsprop')

es = EarlyStopping(monitor = "val_loss_val", mode = "min", verbose = True, restore_best_weights=True, patience = 1)
cp = ModelCheckpoint(filepath,monitor="val_loss_val",mode = "min",verbose=True,save_best_only=True)

# history = model.fit(XTr_fin,yTr,validation_data=[XVal_fin,yVal],epochs=2,batch_size=1,callbacks=[cp,es])
history = model.fit(XTr_fin,yTr,epochs=10,validation_data=[XVal_fin,yVal],batch_size=1)

import matplotlib.pyplot as plt

plt.rcParams["figure.figsize"] = (16,8)
plt.plot(history.history['val_loss_val'])
plt.plot(history.history['loss'])
plt.xlabel('Epochs ->')
plt.ylabel('Losses ->')
plt.title('Losses v/s epochs.')
plt.legend(['Val Loss','Train Loss'])
plt.show()

dict_1R={}
for k,v in dict_1.items():
  dict_1R[v]=k

labels_=model.predict(XVal_fin)
i=0 # i-th example from val dataset.
cnt=0
print()
for x in XVal_[0]:
  print('{} {}'.format(x[0],dict_1R[labels_[i][cnt]]))
  cnt+=1

dict_1

!pip install sklearn-crfsuite

import sklearn_crfsuite
from sklearn_crfsuite import scorers
from sklearn_crfsuite import metrics

def labelIt(yVal):
  yVal_lis=[]
  for y1 in yVal:
    temp=[]
    for y2 in y1:
      temp.append(dict_1R[y2])
    yVal_lis.append(temp)
  return yVal_lis 

yVal_=labelIt(yVal)
yPred_=labelIt(labels_)
labls=['C','J','S','O','UNK']
metrics.flat_f1_score(yVal_,yPred_,average='weighted',labels=labls)

print(metrics.flat_classification_report(yVal_,yPred_,labels=labls,digits=3))