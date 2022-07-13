# -*- coding: utf-8 -*-
"""RF.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WPFurDRYx9p6OvYM1hAmK2Ald3DE4jKD
"""

# RF classification model
import numpy as np
# data
# loaded the dna2vec word embedding file data
# opened and read the respective files
f_pos=open('Positive.w2v','r')
f_neg=open('Negative.w2v','r')
file_p=f_pos.read()
file_n=f_neg.read()
# took file content as a list of sequences
# seperated by newline according to the indexing
lis_p=[x.split() for x in file_p.split('\n')[1:-1]]
lis_n=[x.split() for x in file_n.split('\n')[1:-1]]
# converted the sequence values(string) into numerical values(float) 
list_p=[[float(x) for x in y[1:]] for y in lis_p]
list_n=[[float(x) for x in y[1:]] for y in lis_n]
# labelled natural sequence embeddings as 1
l_pos=[x+[1] for x in list_p]
# labelled synthetic sequence embeddings as 0
l_neg=[x+[0] for x in list_n]
# merged both the lists together
l_whole = l_pos+l_neg
# converted the list to arrray for model implementation
dataset = np.array([np.array(x) for x in l_whole])

# split data into X and Y
# sequence embeddings
X = dataset[:,:-1]
# label of sequence embeddings
Y = dataset[:,-1]
# split the data into train and test using sklearn
from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.20)
# test_size defines test data to be split from train data

# RF classifier model
from sklearn.ensemble import RandomForestClassifier
classifier=RandomForestClassifier(n_estimators=200, random_state=42, max_depth=1)

# fit the training data into the model
classifier.fit(x_train, y_train)

# predicted values from the model
y_pred=classifier.predict(x_test)

# accuracy prediction
from sklearn.metrics import accuracy_score
accuracy = accuracy_score(y_test, y_pred)
print("Accuracy: %.2f%%" % (accuracy * 100.0))

# confusion matrix
from sklearn.metrics import confusion_matrix
conf=confusion_matrix(y_test, y_pred)
print("Confusion matrix\n", conf)
