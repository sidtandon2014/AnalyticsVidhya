# -*- coding: utf-8 -*-
#from sklearn.metrics import mean_squared_error,r2_score
import pdb
import math
import gc
import numpy as np

def LinearRegressionModel(train,test,splits = 10, degree = 2, ISPOLY = True):
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.model_selection import KFold
    
    train_x = np.array(train[train.columns[train.columns != "Upvotes"]])
    train_y = np.array(train[train.columns[train.columns == "Upvotes"]])
    test_x = np.array(test)
    #pdb.set_trace()
    
    #--------------Implement polynomial model
    if ISPOLY:
        polyModel = PolynomialFeatures(degree=degree)
        train_x = polyModel.fit_transform(train_x)
        test_x = polyModel.transform(test_x)
    
    kf = KFold(n_splits= splits)
    rmse_tmp = 0
    rmse = 0
    
    for train_index, test_index in kf.split(train_x):
        X_train, X_test = train_x[train_index],train_x[test_index]
        Y_train, Y_test = train_y[train_index],train_y[test_index]
    
        model = LinearRegression() 
        model.fit(X_train,Y_train)
        #pdb.set_trace()
        result = model.predict(X_test)
        
        rmse = math.sqrt(np.sum((result - Y_test) **2)/ X_train.shape[0])
        rmse_tmp += rmse
        #rmse = math.sqrt(mean_squared_error(Y_test, result))
        #r2 = r2_score(Y_test, result)
        r2 = model.score(X_test,Y_test)
        
        #print("Mean squared error: %.2f" % rmse)
        print("Mean squared error calcu: %.2f" % rmse)
        print('Variance score: %.2f' % r2)
        
        """
        if rmse < rmse_tmp:
            rmse_tmp = rmse
            model_final = model
            #residuals = result - Y_test
        """
    
    print("CV Error %f" % (rmse_tmp/splits))
    model = LinearRegression()
    model.fit(train_x,train_y)
    
    result = model.predict(test_x)
    resid = model.predict(train_x) - train_y

    return model,result,resid

def LassoModel(train,test,splits = 10, degree = 2, ISPOLY = True):
    from sklearn.linear_model import Lasso,Ridge
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.model_selection import train_test_split
    
    train_x = np.array(train[train.columns[train.columns != "Upvotes"]])
    train_y = np.array(train[train.columns[train.columns == "Upvotes"]])
    test_x = np.array(test)
    #pdb.set_trace()
    
    #--------------Implement polynomial model
    if ISPOLY:
        polyModel = PolynomialFeatures(degree=degree)
        train_x = polyModel.fit_transform(train_x)
        test_x = polyModel.transform(test_x)
    
    rmse_tmp = 0
    rmse = 0
    best_alpha = 0
    best_r2 = 0
    X_train, X_test, Y_train, Y_test = train_test_split(train_x, train_y, test_size=0.33, random_state=42)
    
    for alpha in np.arange(0,1,.001):
        model = Ridge(alpha=alpha, normalize=True)
        model.fit(X_train,Y_train)
        #pdb.set_trace()
        result = model.predict(X_test)
        
        rmse = math.sqrt(np.sum((result.reshape(-1,1) - Y_test) **2)/ X_train.shape[0])
        rmse_tmp += rmse
        r2 = model.score(X_test,Y_test)
        #pdb.set_trace()
        print("Mean squared error calcu: %.2f" % rmse)
        print('Variance score: %f' % r2)
        if r2> best_r2:
            best_r2 = r2
            best_alpha = alpha
        gc.collect()
    
    print("Best Alpha %f" % best_alpha)
    print("CV Error %f" % (rmse_tmp/splits))
    model = Ridge(alpha=best_alpha, normalize=True)
    model.fit(train_x,train_y)
    
    result = model.predict(test_x)
    resid = model.predict(train_x)[:,0] - train_y

    return model,result,resid


def lightGBMModel(train,test,splits = 10, degree = 2, ISPOLY = True):
    import lightgbm as lgb
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.model_selection import KFold
    from sklearn.metrics import r2_score
    
    train_x = np.array(train[train.columns[train.columns != "Upvotes"]])
    train_y = np.array(train[train.columns[train.columns == "Upvotes"]])
    test_x = np.array(test)
    #pdb.set_trace()
    
    #--------------Implement polynomial model
    if ISPOLY:
        polyModel = PolynomialFeatures(degree=degree)
        train_x = polyModel.fit_transform(train_x)
        test_x = polyModel.transform(test_x)
    
    kf = KFold(n_splits= splits)
    rmse_tmp = 0
    rmse = 0
    
    params = {
            'boosting_type': 'gbdt',
            'objective': 'regression',
            'metric': 'rmse',
            'two_round':True
        }
    #pdb.set_trace()
    for train_index, test_index in kf.split(train_x):
        X_train, X_test = train_x[train_index],train_x[test_index]
        Y_train, Y_test = train_y[train_index],train_y[test_index]
    
        # create dataset for lightgbm
        # if you want to re-use data, remember to set free_raw_data=False
        lgb_train = lgb.Dataset(X_train, Y_train[:,0])
        lgb_eval = lgb.Dataset(X_test, Y_test[:,0], reference=lgb_train)
        
        gbm = lgb.train(params,
                lgb_train,
                num_boost_round=100,
                valid_sets=lgb_eval  # eval training data
                )
        
        result = gbm.predict(X_test)
        rmse = math.sqrt(np.sum((result - Y_test) **2)/ X_train.shape[0])
        rmse_tmp += rmse
        
        r2 = r2_score(Y_test,result)
        
        #print("Mean squared error: %.2f" % rmse)
        print("Mean squared error calcu: %.2f" % rmse)
        print('Variance score: %.2f' % r2)
        gc.collect()
        
        
    print("CV Error %f" % (rmse_tmp/splits))
    
    lgb_train = lgb.Dataset(train_x, train_y[:,0])
    gbm = lgb.train(params,
                lgb_train,
                num_boost_round=10
                )
    result = gbm.predict(test_x)
    resid = gbm.predict(train_x) - train_y

    return gbm,result,resid    