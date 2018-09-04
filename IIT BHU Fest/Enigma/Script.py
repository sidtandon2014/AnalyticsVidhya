import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.special import boxcox,inv_boxcox
#from scipy import stats
import Models
import imp
%matplotlib auto
sns.set(color_codes=True)

def readData():
    train = pd.read_csv("./Data/train.csv")
    test = pd.read_csv("./Data/test.csv")
    test.loc[:,"Upvotes"] = -1
    dataset = pd.concat([train,test],axis = 0)
    #dataset.drop(["Username"],axis = 1,inplace = True)
    return dataset

def generateAggregates(data):
    data_group_tag = data.groupby("Tag").agg({"Reputation":["mean","max","std","var"]
                                        ,"Answers":["mean","max","std","var"]
                                        ,"Views":["mean","max","std","var"]
    })
    data_group_tag_username = data.groupby(["Tag","Username"]).agg({"Reputation":["mean","max","min","std"]
                                        ,"Answers":["mean","max","min","std"]
                                        ,"Views":["mean","max","min","std"]
    })
    pdb.set_trace()
    data_group_tag.columns = ["_".join(x) + "_TAG" for x in data_group_tag.columns.ravel()]
    print(data_group_tag.head())
    data = data.merge(data_group_tag,how = "inner",on = "Tag")
    
    data_group_tag_username.columns = ["_".join(x) + "_TAG_UN" for x in data_group_tag_username.columns.ravel()]
    data = data.merge(data_group_tag_username,how = "inner",on = ["Tag","Username"])
    return data
    
def convertCategoricalVaribalesToOneHotEncoding(data):
    cat_vars = []
    #pdb.set_trace()
    origColumns = data.columns;
    for column in origColumns:        
        if data[column].dtype.kind in "O":
            cat_vars.append(column)               
            dummyCol = column + "_"                
            cat_list = pd.get_dummies(data[column], prefix=dummyCol)
            data=pd.concat([data,cat_list], axis = 1)
    
    data.drop(cat_vars,axis = 1,inplace = True)
    return data
 
def transformExplanatoryVariables(data):
    data["Reputation"] = np.log(data["Reputation"] + 1)
    data["Answers"] = np.log(data["Answers"] + 1)
    data["Views"] = np.log(data["Views"] + 1)
    #data["Views_Ratio"] = data["Views"] * data["Reputation"]
    return data

def convertCategoricalVaribalesToNumEncoding(data):
    data["Tag"] = data["Tag"].astype("category").cat.codes
    return data


dataset = readData()
#dataset["Views_Rep_Intr"] = dataset["Views"] * dataset["Reputation"]
dataset = transformExplanatoryVariables(dataset)
#dataset = generateAggregates(dataset)
dataset = convertCategoricalVaribalesToNumEncoding(dataset)
dataset.isnull().sum()
#dataset.fillna(0, inplace = True)
"""
-------Univariate Analysis
1. Total Rows: 330045
2. Unique Tags: 10
3. No NULL or empty values 
4. No very high corerlation between independent variables

"""
train = dataset[dataset["Upvotes"] != -1]
test = dataset[dataset["Upvotes"] == -1]

"""
1. Convert target to normal distribution
2. Drop unused variables
"""
train["Upvotes"] = np.log(train["Upvotes"] + 1)

test_Ids = test["ID"]
train.drop(["Username","ID"],axis = 1, inplace = True)
test.drop(["Username","ID","Upvotes"],axis = 1, inplace = True)

"""
Visualize 
1. Boxplot for tag and reputation: Similar variance
2. Boxplot for tag and Answers: Similar variance
3. Boxplot for tag and Answers: Similar variance
4. Reponse vs explanatory variables
    Reputation, Answers, Views vs upvotes: not linear. Used log transformation
"""
train.groupby("Tag").count()
sns.regplot(x = 1/(train["Views"]+1),y = train["Upvotes"])
plt.scatter(x = train["View"],y = train["Upvotes"])
plt.scatter(x = train["Reputation"],y = np.log(train["Upvotes"] + 1))
plt.scatter(x = np.log(train["Reputation"]+1),y = train["Upvotes"])
plt.scatter(x = np.log(train["Reputation"]+1),y = np.log(train["Upvotes"] + 1))


plt.scatter(x = 1/(train["Views"] + 1),y = train["Upvotes"])
plt.scatter(x = np.log(train["Views"]) ** 1.5 ,y = (np.log(train["Upvotes"] + 1)))

sns.pairplot(train)
sns.boxplot(x = "Tag",y = "Views",data = train)
stats.boxcox(train["Upvotes"])
sns.distplot(stats.boxcox(train["Upvotes"] + 1)[0])  
sns.distplot(np.log(train["Upvotes"] + 1)) 


"""
.1 Build Models
"""
imp.reload(Models)

model,results,resid = Models.lightGBMModel(train,test,degree = 2,ISPOLY= True)

results = (np.exp(results) - 1).round().astype(int)
results = pd.DataFrame({"ID":test_Ids,"Upvotes":results[:,0]})
results.to_csv("./Results.csv",sep = ",",index = False)


"""
Model plots
1. Residuals vs explanatory vairbale
2. Residual vs y_pred
3. y on y_pred
4. 
"""
plt.scatter(x = train["Views"], y = resid )
plt.scatter(x = model.predict(np.array(train[train.columns[train.columns != "Upvotes"]])), y = resid )
