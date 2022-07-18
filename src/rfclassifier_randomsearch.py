# -*- coding: utf-8 -*-

# RF classifier model
# Random search implementation
# improves output by ignoring warnings
import warnings
warnings.filterwarnings('ignore')
# imported the required modules
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, plot_confusion_matrix
from pprint import pprint
import matplotlib.pyplot as plt
%matplotlib inline
# Module for hyperparameter tuning
from sklearn.model_selection import RandomizedSearchCV

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
x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.33)
# test_size defines test data to be split from train data
# 1/3rd of training dataset is used as testing dataset

# RF classifier model
# called with default values
classifier=RandomForestClassifier()

# fit the training data into the base model
classifier.fit(x_train, y_train)

# predicted values from the model
y_pred=classifier.predict(x_test)

# accuracy prediction for base model
print("BASE MODEL")
accuracy = accuracy_score(y_test, y_pred)
print("Accuracy: %.2f%%" % (accuracy * 100.0))

# classification report
print("Classification report:\n")
print(classification_report(y_test, y_pred))

# confusion matrix
conf_g=confusion_matrix(y_test, y_pred)
print("Confusion matrix:\n", conf_g)

# confusion matrix plot
print("Confusion matrix plot:\n")
plot_confusion_matrix(classifier, x_test, y_test)  
plt.show()

# Look at parameters used by our current forest
print('Parameters currently in use:')
pprint(classifier.get_params())

# Hyperparameter tuning using RandomizedsearchCV
# Setting range of parameters
# Number of trees in random forest
n_estimators = [int(x) for x in np.linspace(start = 200, stop = 2000, num = 10)]
# Number of features to consider at every split
max_features = ['auto', 'sqrt']
# Maximum number of levels in tree
max_depth = [int(x) for x in np.linspace(10, 110, num = 11)]
max_depth.append(None)
# Minimum number of samples required to split a node
min_samples_split = [2, 5, 10]
# Minimum number of samples required at each leaf node
min_samples_leaf = [1, 2, 4]
# Method of selecting samples for training each tree
bootstrap = [True, False]
# Create the random grid
param = {'n_estimators': n_estimators,
               'max_features': max_features,
               'max_depth': max_depth,
               'min_samples_split': min_samples_split,
               'min_samples_leaf': min_samples_leaf,
               'bootstrap': bootstrap}

print('Range of parameters used for hyperparameter tuning:')
pprint(param)

# implemented grid search on RF classifier
classifier_random=RandomizedSearchCV(estimator = classifier, param_distributions = param, n_iter = 100, cv = 3, verbose=2, random_state=42, n_jobs = -1)

# fit the training data into the random search model
classifier_random.fit(x_train, y_train)

# Best hyperparameter values
print('Best parameter values:')
print(classifier_random.best_params_)

# predicted values from the random search model using best parameters
cl_r=classifier_random.best_estimator_
pred=cl_r.predict(x_test)

# accuracy prediction for random search model
accuracy = accuracy_score(y_test, pred)
print("\nRANDOM SEARCH MODEL")
print("Accuracy: %.2f%%" % (accuracy * 100.0))

#classification report
print("Classification report:\n")
print(classification_report(y_test, y_pred))

# confusion matrix
conf_r=confusion_matrix(y_test, pred)
print("Confusion matrix:\n", conf_r)

# confusion matrix plot
print("Confusion matrix plot:\n")
plot_confusion_matrix(classifier_random, x_test, y_test)  
plt.show()