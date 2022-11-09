import pandas as pd
import numpy as np
import fastaparser
import wandb
import random
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV, cross_val_score, StratifiedKFold, cross_validate
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, plot_confusion_matrix
from pprint import pprint
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, plot_confusion_matrix 
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from yellowbrick.text import FreqDistVisualizer
from sklearn.metrics import RocCurveDisplay
from sklearn.metrics import mean_squared_error
from matplotlib.legend_handler import HandlerLine2D
from hyperopt import tpe, STATUS_OK, Trials, hp, fmin, STATUS_OK, space_eval
# Relevant functions
def Kmers_funct(seq, k_low, k_high):
   return [seq[x:x+random.randint(k_low,k_high)].lower() for x in range(len(seq)-k_low + 1)]

def spacings(seq,k_low,k_high):
  words = Kmers_funct(seq, k_low, k_high)
  joined_sentence = ' '.join(words)
  return joined_sentence

def loadsequence(sequence_file, k_low, k_high):
  with open(sequence_file) as fasta_file:
        parser = fastaparser.Reader(fasta_file, parse_method='quick')
        corpus = []
        for seq in parser:
          s = seq.sequence
          corpus.append(spacings(s, k_low, k_high))
  return corpus

def add_labels(sequence_file, k_low, k_high, label):
  file=loadsequence(sequence_file, k_low, k_high)
  file=pd.DataFrame(file)
  file.columns=['kmer']
  file['labels']=label
  return file

def tf_idf(dna_seq, labels, max_features, n_gram_from=1, n_gram_to=1):
  #create count vectorizer and tf vectorizer models
  tf_vec = TfidfTransformer(smooth_idf=False)
  cvec = CountVectorizer(max_features=max_features, ngram_range=(n_gram_from, n_gram_to))
  #get the term frequencies: [n_samples, n_features].
  tf = cvec.fit_transform(dna_seq.values)# dataframe sequences
  #get IDF too. 
  tfidf = tf_vec.fit_transform(tf)
  tfidf=tfidf.toarray()
  np.nan_to_num(tfidf)
  tf_labels=np.array(labels)
  feature=cvec.get_feature_names_out()
  return tfidf, tf_labels, feature

def split_dataset(X, Y, train_ratio, test_ratio, validation_ratio):
    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=1 - train_ratio)
    x_val, x_test, y_val, y_test = train_test_split(x_test, y_test, test_size=test_ratio/(test_ratio + validation_ratio))
    return x_train, y_train, x_test, y_test, x_val, y_val

def train_model(model,x_train, y_train, x_test):
   clf=model(n_estimators = 1000)
   # fit the training data into the model
   clf.fit(x_train, y_train)
   y_pred=clf.predict(x_test)
   y_probas=clf.predict_proba(x_test)
   return clf, y_pred, y_probas

def model_metrics(model, x_test, y_test, y_pred):
  # accuracy prediction
  accuracy = accuracy_score(y_test, y_pred)
  print("Accuracy: %.2f%%" % (accuracy * 100.0))
  # classification report
  print("Classification report:\n")
  print(classification_report(y_test, y_pred))
  # confusion matrix
  conf=confusion_matrix(y_test, y_pred)
  print("Confusion matrix:\n", conf)

def feature_imp(model,feature_names, n_top_features):
  feats=np.array(feature_names)
  importances = model.feature_importances_
  indices = np.argsort(importances)[::-1]
  plt.figure(figsize=(8,10))
  plt.barh(feats[indices][:n_top_features ], importances[indices][:n_top_features ])
  plt.xlabel("XG feature Importance ")

def grid_search(model, param, scoring, x_train, y_train, x_test):
    clf_grid=GridSearchCV(estimator=model, param_grid=param, scoring = scoring , refit = 'recall' , cv = 3, verbose=2, n_jobs = 4)
    # fit the training data
    clf_grid.fit(x_train,y_train)
    # Best hyperparameter values
    print('Best parameter values:')
    print(clf_grid.best_params_)
    # predicted values from the grid search model
    clf_g=clf_grid.best_estimator_
    y_pred=clf_g.predict(x_test)
    y_probas = clf_g.predict_proba(x_test)
    return clf_g, y_pred, y_probas

def random_search(model, param, scoring, x_train, y_train, x_test):
    clf_ran=RandomizedSearchCV(estimator=model, param_distributions = param, scoring = scoring, refit = 'recall', cv = 3, verbose=2, n_jobs = 4)
    # fit the training data
    clf_ran.fit(x_train,y_train)
    # Best hyperparameter values
    print('Best parameter values:')
    print(clf_ran.best_params_)
    # predicted values from the random search model
    clf_r=clf_ran.best_estimator_
    y_pred=clf_r.predict(x_test)
    y_probas = clf_r.predict_proba(x_test)
    return clf_r, y_pred, y_probas

def bay_opt(model, param, scoring, x_train, y_train, x_test):
  # we need to define space from param grid
  # we are using choice-categorical variable distribution type to define space
  def space_(param):
    space = {key : hp.choice(key, param[key]) for key in param}
    return space
  # Set up the k-fold cross-validation
  kfold = StratifiedKFold(n_splits=3, shuffle=True, random_state=0)

  # Objective function
  # detach cross validation from sweep
  def objective(params):
    estimator = model(**params)
    scores = cross_val_score(estimator, x_train, y_train, cv=kfold, scoring = scoring, n_jobs=-1)
    # Extract the best score
    best_score = max(scores)
    # Loss must be minimized
    loss = - best_score
    # Dictionary with information for evaluation
    return {'loss': loss, 'params': params, 'status': STATUS_OK}
  # Trials to track progress
  bayes_trials = Trials()
  # Optimize
  best = fmin(fn = objective, space = space_(param), algo = tpe.suggest, max_evals = 48, trials = bayes_trials)
  # the index of the best parameters (best)
  # the values of the best parameters
  param_b = space_eval(space_(param), best)

  clf_bo = model(**param_b).fit(x_train, y_train)
  y_pred=clf_bo.predict(x_test)
  y_probas = clf_bo.predict_proba(x_test)
  return clf_bo, y_pred, y_probas
   
def token_freq_plot(feature, X):
    visualizer = FreqDistVisualizer(features=feature, orient='v')
    visualizer.fit(X)
    visualizer.show()

def best_sweep(entity, project):
    api = wandb.Api()
    runs = api.runs(entity + "/" + project)
    # download metrics from all runs
    print("Get metrics from all runs")
    summary_list, config_list, name_list = [], [], []
    for run in runs: 
       # .summary contains the output keys/values for metrics like accuracy.
       summary_list.append(run.summary._json_dict)
       # .config contains the hyperparameters.
       #  We remove special values that start with _.
       config_list.append(
           {k: v for k,v in run.config.items()
            if not k.startswith('_')})
       # .name is the human-readable name of the run.
       name_list.append(run.name)
    runs_df = pd.DataFrame({
       "summary": summary_list,
       "config": config_list,
       "name": name_list
       })
    runs_df.to_csv('metrics.csv')
    # identify best model file from the sweep
    metric_opt='f1'
    runs = sorted(runs, key=lambda run: run.summary.get(metric_opt, 0), reverse=True)
    score = runs[0].summary.get(metric_opt, 0)
    print(f"Best sweep {runs[0].name} with {metric_opt}={score}%")

def main():
    sequence_file1='Human_promoter.fa'
    sequence_file2='Human_promoter_synthetic.fa'
    k_low=5
    k_high=5
    label_1=0
    label_2=1
    n_gram_from=2
    n_gram_to=2
    max_features=1000
    train_ratio = 0.70
    validation_ratio = 0.15
    test_ratio = 0.15
    param=100
    model=XGBClassifier
    param = {"colsample_bytree": [ 0.3, 0.5 , 0.8 ],"reg_alpha": [0, 0.5, 1, 5],"reg_lambda": [0, 0.5, 1, 5]}
    pos=add_labels(sequence_file1, k_low, k_high, label_1)
    neg=add_labels(sequence_file2, k_low, k_high, label_2)
    dna=pd.concat([pos,neg]) 
    dna.reset_index(drop=True, inplace=True)
    #print(dna.head())
    tfidf, tf_labels, feature=tf_idf(dna.kmer, dna.labels, max_features, n_gram_from, n_gram_to)
    print("Total data items:",tfidf.shape)
    print("Total data labels",tf_labels.shape)
    token_freq_plot(feature, tfidf)
    # split the dataset into train, test and validation set using sklearn
    # train is now 70% of the entire data set
    # test is now 15% of the initial data set
    # validation is now 15% of the initial data set
    x_train, y_train, x_test, y_test, x_val, y_val=split_dataset(tfidf, tf_labels, train_ratio, test_ratio, validation_ratio) 
    print("Training data:",x_train.shape)
    print("Training data labels:",y_train.shape)
    print("Test data:",x_test.shape)
    print("Test data labels:",y_test.shape)
    print("Validation data:",x_val.shape)
    print("Validation data labels:",y_val.shape)
    print('BASE MODEL')
    #training the model
    xg_base, y_pred, y_probas=train_model(model, x_train, y_train, x_test)
    # model metrics
    model_metrics(xg_base, x_test, y_test, y_pred)
    print("Feature Importance Plot:\n")
    feature_imp(xg_base, feature, 20)
    # wandb plot
    wandb.init(project="test XG", name="XG-base model")
    # Visualize all classifier plots at once
    wandb.sklearn.plot_classifier(xg_base, x_train, x_test, y_train, y_test, y_pred,
                                y_probas, labels=None, model_name='BASE MODEL', feature_names=feature)
    wandb.finish()
    # parameters currently used
    print('Parameters currently in use:')
    pprint(xg_base.get_params())
    # Setting range of parameters
    scoring = ['recall']
    print('Range of parameters used for hyperparameter tuning:')
    pprint(param)
    # Hyperparameter tuning using GridsearchCV
    print("\nGRID SEARCH MODEL")
    # Grid Search model
    xg_grid, y_pred1, y_probas1=grid_search(xg_base, param, scoring, x_train, y_train, x_test)
    # model metrics
    model_metrics(xg_grid, x_test, y_test, y_pred1)
    print("Feature Importance Plot:\n")
    feature_imp(xg_grid, feature, 20)
    # wandb plot
    wandb.init(project="test XG", name="XG-Grid Search model")
    # Visualize all classifier plots at once
    wandb.sklearn.plot_classifier(xg_grid, x_train, x_test, y_train, y_test, y_pred1, y_probas1, 
                                labels=None, model_name='Grid Search Model', feature_names=feature)
    wandb.finish()

    print("\nRANDOM SEARCH MODEL")
    # Random search model
    xg_ran, y_pred2, y_probas2=random_search(xg_base, param, scoring, x_train, y_train, x_test)
    # model metrics
    model_metrics(xg_ran, x_test, y_test, y_pred2)
    print("Feature Importance Plot:\n")
    feature_imp(xg_ran, feature, 20)
    # wandb plot
    # Visualize all classifier plots at once
    wandb.init(project="test XG", name="XG-Random Search model")
    wandb.sklearn.plot_classifier(xg_ran, x_train, x_test, y_train, y_test, y_pred2, y_probas2,
                                labels=None, model_name='Random Search Model', feature_names=feature)
    wandb.finish()

    print('BAYESIAN OPTIMISATION MODEL')
    scoring_xg='recall'
    xg_bayes, y_pred3, y_probas3 = bay_opt(model, param, scoring_xg, x_train, y_train, x_test)
    # model metrics
    model_metrics(xg_bayes, x_test, y_test, y_pred3)
    print("Feature Importance Plot:\n")
    feature_imp(xg_bayes, feature, 20)
    # wandb plot
    # Visualize all classifier plots at once
    wandb.init(project="test XG-eng", name="XG-Bayesian opt. model")
    wandb.sklearn.plot_classifier(xg_bayes, x_train, x_test, y_train, y_test, y_pred3, y_probas3, 
                                labels=None, model_name='Bayesian Optimization Model', feature_names=feature)
    
    # wandb sweeps
    def XGsweep(x_train, y_train, x_test, feature):
          wandb.init(settings=wandb.Settings(console='off', start_method='fork'))
          clf = RandomForestClassifier(n_estimators=100)
          clf.fit(x_train, y_train)
          preds = clf.predict(x_test)
          pred_prob = clf.predict_proba(x_test)
          #features=cv.get_feature_names_out()
          #print(classification_report(y_test, preds))
          # Log any metric with Weights and Biases
          wandb.log({'accuracy_score': accuracy_score(y_test,preds), 
                    'f1':f1_score(y_test,preds), 
                    'precision': precision_score(y_test, preds), 
                    'recall': recall_score(y_test, preds)})
          wandb.sklearn.plot_classifier(clf, x_train, x_test, y_train, y_test, 
                                        preds, pred_prob, labels=None, model_name='Random Forest Model', feature_names=feature)
    sweep_config = {
              'name'  : "random",
              'method': 'random', #grid, random
              'metric': {
                'name': 'f1_score',
                'goal': 'maximize' },
              'parameters': { "colsample_bytree": {"values":[ 0.3, 0.5 , 0.8 ]},
                             "reg_alpha": {"values":[0, 0.5, 1, 5]},
                             "reg_lambda": {"values": [0, 0.5, 1, 5]}
                             }, }
    sweep_id = wandb.sweep(sweep_config, project='test sweep_')
    count=3
    wandb.agent(sweep_id,function=XGsweep, count=count)
    wandb.finish()

    sweep_config1 = {
              'name'  : "grid",
              'method': 'grid', #grid, random
              'metric': {
                'name': 'f1_score',
                'goal': 'maximize' },
              'parameters': { "colsample_bytree": {"values":[ 0.3, 0.5 , 0.8 ]},
                             "reg_alpha": {"values":[0, 0.5, 1, 5]},
                             "reg_lambda": {"values": [0, 0.5, 1, 5]}
                             }, }
    sweep_id1 = wandb.sweep(sweep_config1, project='test sweep_')
    count=3
    wandb.agent(sweep_id1,function=XGsweep, count=count)
    wandb.finish()
         
    sweep_config2 = {
              'name'  : "bayesian",
              'method': 'bayes', #grid, random
              'metric': {
                'name': 'f1_score',
                'goal': 'maximize' },
              'parameters': { "colsample_bytree": {"values":[ 0.3, 0.5 , 0.8 ]},
                             "reg_alpha": {"values":[0, 0.5, 1, 5]},
                             "reg_lambda": {"values": [0, 0.5, 1, 5]}
                             }, }
                             
    sweep_id2 = wandb.sweep(sweep_config2, project='test sweep_')
    count=3
    wandb.agent(sweep_id2,function=XGsweep, count=count)
    wandb.finish()

    # Exporting metrics from a project in to a CSV file
    # set to your entity and project
    # best sweep
    best_sweep('tyagilab', 'test sweep_')

if __name__ == "__main__":
    main()
