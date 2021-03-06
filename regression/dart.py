#coding=utf-8

import xgboost as xgb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from config import *
import argparse
parser = argparse.ArgumentParser(description='manual to this script')
# 0为训练全部数据并测试线上结果，1为最小规模训练及测试线下结果，2为线下训练数据集及测试线下测试集
parser.add_argument('--offline_test', type=int, default=2)
args = parser.parse_args()
OFFLINE_BUTTON = args.offline_test

#loading feature file and merge
if OFFLINE_BUTTON == 1:
    origin_train = pd.read_csv('../data/feature/pure_train_feat.csv')
elif OFFLINE_BUTTON == 2:
	origin_train = pd.read_csv('../data/feature/offline_train_feat.csv')
else:
    origin_train = pd.read_csv('../data/feature/all_train_feat.csv')

train_param_feature = list(origin_train.columns)
train_param_feature.remove('id')
train_param_feature.remove('血糖')

print("all",origin_train.shape)
train = origin_train[origin_train['血糖']<=19]
print('<=19',train.shape)

if OFFLINE_BUTTON == 1:
    origin_test = pd.read_csv('../data/feature/pure_test_feat.csv')
elif OFFLINE_BUTTON == 2:
    origin_test = pd.read_csv('../data/feature/offline_test_feat.csv')
	# origin_test = pd.read_csv('../data/feature/all_test_feat.csv')
else:
    origin_test = pd.read_csv('../data/feature/all_test_feat.csv')

#drop nan columns
origin_test['血糖'] = -999
train_test = pd.concat([train,origin_test],axis=0)
train_test.dropna(axis='columns',how='all',inplace=True)
# delete specify params and the remaining params without sugar
train_test.drop(del_params,axis=1,inplace=True)
train = train_test[train_test['血糖']!=-999]
test = train_test[train_test['血糖']==-999]

train_y = train['血糖']
train_x = train.drop(['血糖','id'],axis=1)
test_id = test['id']
test_x = test.drop(['id','血糖'],axis=1)

# #'p1_p2' is a new feature
train_x['acid_soda'] = train_x['嗜酸细胞%'] - train_x['嗜碱细胞%']
test_x['acid_soda'] = test_x['嗜酸细胞%'] - test_x['嗜碱细胞%']
predictors = train_x.columns

#training xgboost
dtrain = xgb.DMatrix(train_x,label=train_y)
dtest = xgb.DMatrix(test_x)

params={'booster':'dart',
    'eval_metric': 'rmse',
    "objective":"reg:linear",
    'max_depth':8,
    'lambda':200,
	'subsample':0.75,
	'colsample_bytree':0.75,
	'eta': 0.02,
	'sample_type':'uniform',
	'normalize':'forest',
	'rate_drop':0.15,
	'skip_drop':0.85,
	'seed':1024,
	'nthread':8
}

#通过cv找最佳的nround
cv_log = xgb.cv(params,dtrain,num_boost_round=25000,nfold=10,early_stopping_rounds=50,seed=1023)#num_boost_round=25000
bst_rmse= cv_log['test-rmse-mean'].min()
cv_log['nb'] = cv_log.index
cv_log.index = cv_log['test-rmse-mean']
bst_nb = cv_log.nb.to_dict()[bst_rmse]

watchlist  = [(dtrain,'train')]
model = xgb.train(params,dtrain,num_boost_round=bst_nb+50,evals=watchlist)
# 保存dart模型
model.save_model('../model/regression/xgb_reg.model')
#predict test set
test_y = model.predict(dtest)
test_result = pd.DataFrame(test_id,columns=["id"])
test_result["score_all"] = test_y
test_result.to_csv("dart_preds.csv",index=None,encoding='utf-8')

print(bst_nb,bst_rmse)
#Plot feature importance
myfont = FontProperties(fname="simhei.ttf")
fig,ax = plt.subplots(figsize=(12,18))
xgb.plot_importance(model,height=0.8,ax=ax)
ax.set_yticklabels(predictors,rotation='horizontal',fontproperties=myfont)
# plt.show()


if OFFLINE_BUTTON == 1:
	origin_test1 = pd.read_csv('../data/feature/pure_test_feat.csv')
	exact_value = origin_test1['血糖']
	mse = np.mean(np.square(test_y - exact_value))/2.0
	print('dart MSE:'+str(mse))
if OFFLINE_BUTTON == 2:
	origin_test1 = pd.read_csv('../data/feature/offline_test_feat.csv')
	# origin_test1 = pd.read_csv('../data/feature/all_test_feat.csv')
	exact_value = origin_test1['血糖']
	mse = np.mean(np.square(test_y - exact_value)) / 2.0
	print('dart MSE:' + str(mse))
