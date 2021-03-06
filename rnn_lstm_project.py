# -*- coding: utf-8 -*-
"""RNN_LSTM_PROJECT.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xsINdnIXY6UNxFtJYAgQ-38uZ5kFfyL8
"""

import numpy as np 
import pandas as pd
import os

import datetime as dt
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
from keras.layers import Dropout
from pymongo import MongoClient
import urllib.parse

path = r"/content/drive/MyDrive/dataset"

class LSTMmodel:
  def __init__(self, df, filename):
    self.filename = filename
    self.df = df
    self.create_Train_Valid(df, filename)

  def mongodb_append(self, mongopred, filename):
    username = urllib.parse.quote_plus('Madhur_123')
    password = urllib.parse.quote_plus('madhur123') 
    client =  MongoClient("mongodb://Madhur_123:madhur123@cluster0-shard-00-00.vw0td.mongodb.net:27017,cluster0-shard-00-01.vw0td.mongodb.net:27017,cluster0-shard-00-02.vw0td.mongodb.net:27017/?ssl=true&replicaSet=atlas-fa8mpf-shard-0&authSource=admin&retryWrites=true&w=majority") 
    fileindex = [filename] * len(mongopred)
    mongopreds = mongopred.to_frame()
    mongopreds["Filename"] = fileindex
    mongopreds = mongopreds.reset_index()
    mongopreds.set_index(['Filename', 'Date'])
    print(mongopreds.head())
    db = client['stockdata']
    collection = db['stockdata1']
    data_dict = mongopreds.to_dict("records")
    #print(data_dict)
    collection.insert_many(data_dict)

  def plotting_output(self, train ,valid, all_data, preds, filename):
    size, temp = all_data.shape
    ini_train = int(0.4*size)
    train_size = int(0.75*size)

    train = all_data[ini_train:train_size]
    valid = all_data[train_size:]
    valid['Predictions'] = preds
    plt.figure(figsize=(20,8))
    plt.plot(train['Close'])
    plt.plot(valid['Close'], color = 'blue', label = 'Real Price')
    plt.plot(valid['Predictions'], color = 'red', label = 'Predicted Price')
    plt.title( filename + 'price prediction')
    plt.legend()
    plt.show() 
    self.mongodb_append(valid['Predictions'], filename)

  def test_data(self, model ,train, scaler , scaled_data ,valid, all_data, filename):
    inputs = all_data[len(all_data) - len(valid)-90:].values
    inputs = inputs.reshape(-1,1)
    inputs  = scaler.transform(inputs)
    # Preparing the Test data for prediction
    X_test = []
    for i in range(90,inputs.shape[0]):
        X_test.append(inputs[i-90:i,0])
    X_test = np.array(X_test)
    #print(X_test)
    X_test = np.reshape(X_test, (X_test.shape[0],X_test.shape[1],1))
    preds = model.predict(X_test)
    preds = scaler.inverse_transform(preds)
    #print(preds)
    #calculating root mean squared error
    rms=np.sqrt(np.mean(np.power((valid-preds),2)))
    self.plotting_output(train ,valid, all_data, preds, filename)

  def fit_Model(self, model, x_train, y_train, train, scaler ,scaled_data ,valid, all_data, filename):
    model.compile(loss='mean_squared_error', optimizer='adam')
    model.fit(x_train, y_train, epochs=100, batch_size=64, verbose=1)                               
    self.test_data(model ,train, scaler ,scaled_data ,valid, all_data, filename)

  def build_Model(self, x_train, y_train, train, scaler ,scaled_data, valid, all_data, filename):
    # create and fit the LSTM network
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1],1)))
    model.add(Dropout(rate = 0.2))

    model.add(LSTM(units=50, return_sequences = True))
    model.add(Dropout(rate = 0.2))

    model.add(LSTM(units=50, return_sequences = True))
    model.add(Dropout(rate = 0.2))

    model.add(LSTM(units=50, return_sequences = False))
    model.add(Dropout(rate = 0.2))

    model.add(Dense(1))
    self.fit_Model(model, x_train, y_train, train, scaler ,scaled_data ,valid, all_data, filename)

  def create_Sliding_Window(self, train, scaler ,scaled_data ,valid, all_data, filename):
    x_train, y_train = [], []
    for i in range(90,len(train)):
        x_train.append(scaled_data[i-90:i,0])
        y_train.append(scaled_data[i,0])
    x_train, y_train = np.array(x_train), np.array(y_train)
    #reshaping data
    x_train = np.reshape(x_train, (x_train.shape[0],x_train.shape[1],1))
    self.build_Model(x_train, y_train, train, scaler ,scaled_data ,valid, all_data, filename)

  def featureScaling(self, dataset ,train, valid, all_data, filename):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(dataset)
    self.create_Sliding_Window(train, scaler ,scaled_data ,valid, all_data, filename)

  def create_Train_Valid(self, df, filename):
    features = ["Date", "Close"]
    all_data = df[features] 
    all_data.index = all_data.Date
    all_data.drop('Date', axis=1, inplace=True)
    size, temp = all_data.shape
    ini_train = int(0.4*size)
    train_size = int(0.75*size)
    dataset = all_data.values
    train = dataset[ini_train:train_size,:]
    valid = dataset[train_size:,:]
    self.featureScaling(dataset, train, valid, all_data, filename)

def readstock(filename):
  df = pd.read_csv(os.path.join(path, filename))
  df['Date'] = pd.to_datetime(df.Date,format='%Y-%m-%d')
  df.index = df['Date']
  #plot
  plt.figure(figsize=(20,8))
  plt.plot(df['Close'], label='Historical Close Price')
  plt.title(filename)
  ob = LSTMmodel(df, filename)

for filenames in os.listdir(path):
  #print(filenames)
  i = 0
  if(filenames != "stock_metadata.csv" and filenames != "NIFTY50_all.csv"):
    i+=1
    readstock(filenames)
    if i==3:
      break

