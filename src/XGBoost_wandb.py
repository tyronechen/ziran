# XGBoost model 
## Imported and downloaded the necessary modules for running XGBoost
import xgboost
import wandb
import numpy 
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.metrics import mean_squared_error

# initialize wandb run
wandb.init(project="xgboost")

# load data
f_pos = open('Positive.w2v','r') # opened the word embeddings(positive data)file trained on natural sequences from dna2vec saved on desktop 
f_neg = open('Negative.w2v','r') # opened the word embeddings file trained on synthetic sequences(negative data)from dna2vec saved on desktop 
fcontent_pos = f_pos.read() # read content on positive data
fcontent_neg = f_neg.read() # read content on negative data
lis_pos = [x.split() for x in fcontent_pos.split('\n')[1:-1]] # took content from positive data in form of list of sequence embeddings separated by line from second line to last line # excluded first line here because it is not desired output from dna2vec-it is just the matrix dimension of resulting embeddings 
lis1_pos = [[float(x) for x in y[1:]] for y in lis_pos] # converted the list elements to float(numerical values) from strting(default datatype when read from file)- here we had left out k-mer such as AAA since that is of no need- we only need embeddings(vector)-that is why we had included from elements first value i.e y[1:]
lis_neg  = [x.split() for x in fcontent_neg.split('\n')[1:-1]] # # took content from negative data
lis1_neg = [[float(x) for x in y[1:]] for y in lis_neg] # converted the list elements to float(numerical values) from strting(default datatype when read from file)- here we had left out k-mer such as AAA since that is of no need- we only need embeddings(vector)-that is why we had included from elements first value i.e y[1:]
l_pos = [x+[1] for x in lis1_pos] # labelled natural sequence embeddings as 1
l_neg = [x+[0] for x in lis1_neg] # labelled synthetic sequence embeddings as 0
l_whole = l_pos+l_neg # merged both list containing positive sequence embeddings and negative
dataset = numpy.array([numpy.array(x) for x in l_whole]) # converted the dataset into arrays for XGBoost implememtation

# split data into X and Y
X = dataset[:,0:-1] # X is sequence embeddings which needs to be classified
Y = dataset[:,-1] # Y is label of sequence embeddings
# split data into train and test sets
seed = 7 # random state is defined for making training less bias prone
test_size = 0.33 # test dataset is 1/3 of dataset
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=test_size, random_state=seed) # splitted dataset into training and testing data

xg_reg = xgboost.XGBRegressor(objective ='reg:linear', 
    colsample_bytree = 0.3, 
    learning_rate = 0.1,
    max_depth = 5, 
    alpha = 10, 
    n_estimators = 10)

xg_reg.fit(X_train,y_train,callbacks=[wandb.xgboost.wandb_callback()])

preds = xg_reg.predict(X_test)

rmse = numpy.sqrt(mean_squared_error(y_test, preds))
print("RMSE: %f" % (rmse))
wandb.log({"RMSE": rmse})