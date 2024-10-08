# -*- coding: utf-8 -*-
"""Another copy of starter_bank.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1BE9FkTEybwAg9HsdCVoHyHCmu7fP-WxP
"""

import pandas as pd

campaign = pd.read_csv('https://raw.githubusercontent.com/byui-cse/cse450-course/master/data/bank.csv')

# drop missing values
# campaign.replace('unknown', pd.NA, inplace=True)
# campaign.dropna(axis=0, inplace=True)

campaign['contacted_before'] = campaign['pdays'].apply(lambda x: 0 if x == 999 else 1)

# campaign['contacted_before'].value_counts()
# campaign.value_counts()

campaign.info()

from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import plot_tree
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import RandomOverSampler

ro = RandomOverSampler(random_state=42)

# make certain columns categorical
campaign['job_cat'] = campaign['job'].astype('category')
campaign['marital_cat'] = campaign['marital'].astype('category')
campaign['education_cat'] = campaign['education'].astype('category')
campaign['default_cat'] = campaign['default'].astype('category')
campaign['housing_cat'] = campaign['housing'].astype('category')
campaign['loan_cat'] = campaign['loan'].astype('category')
campaign['contact_cat'] = campaign['contact'].astype('category')
campaign['month_cat'] = campaign['month'].astype('category')
campaign['day_of_week_cat'] = campaign['day_of_week'].astype('category')
campaign['poutcome_cat'] = campaign['poutcome'].astype('category')
campaign['contacted_before_cat'] = campaign['contacted_before'].astype('category')

# split feature and target data
features = ['age', 'job_cat', 'marital_cat', 'education_cat', 'default_cat', 'housing_cat', 'loan_cat', 'contact_cat', 'month_cat', 'day_of_week_cat', 'previous', 'poutcome_cat', 'emp.var.rate', 'cons.price.idx', 'cons.conf.idx', 'euribor3m', 'nr.employed', 'contacted_before_cat']
X_first = pd.get_dummies(campaign[features])

# columns_to_remove = [col for col in X_first.columns if 'unknown' in col]
# X_first.drop(columns=columns_to_remove, inplace=True)

y_first = campaign['y']
X, y = ro.fit_resample(X_first, y_first)

# split training and test data
X_train, X_other, y_train, y_other = train_test_split(X, y, test_size=0.20, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_other, y_other, test_size=0.50, random_state=42)

# create tree
clf = RandomForestClassifier(max_depth=8, criterion='entropy', max_leaf_nodes=25, max_features=0.60, class_weight={'yes':53, 'no':47}) # {'yes':87, 'no':13}

# train tree
clf.fit(X_train, y_train)

X.info()

from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
y_pred = clf.predict(X_val)

# test tree
accuracy_score(y_val, y_pred)

precision_score(y_val, y_pred, pos_label='yes')

recall_score(y_val, y_pred, pos_label='yes')

f1_score(y_val, y_pred, pos_label='yes')

y_pred = clf.predict(X_test)

# test tree
print(accuracy_score(y_test, y_pred))
print(precision_score(y_test, y_pred, pos_label='yes'))
print(recall_score(y_test, y_pred, pos_label='yes'))
print(f1_score(y_test, y_pred, pos_label='yes'))

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

# Compute confusion matrix
cm = confusion_matrix(y_test, y_pred)

# Plot confusion matrix
sns.set(font_scale=1.2)  # Adjust font size
plt.figure(figsize=(6, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', annot_kws={"size": 14},
            xticklabels=['Negative', 'Positive'], yticklabels=['Negative', 'Positive'])
plt.title('Confusion Matrix')
plt.xlabel('Predicted label')
plt.ylabel('True label')
plt.savefig('confusion_matrix.png', format='png', bbox_inches='tight')
plt.show()

targets_file = "https://raw.githubusercontent.com/byui-cse/cse450-course/master/data/bank_holdout_test_mini_answers.csv"
targets = pd.read_csv(targets_file)
targets.head()

hold_mini = pd.read_csv('https://raw.githubusercontent.com/byui-cse/cse450-course/master/data/bank_holdout_test_mini.csv')
hold_mini.info()

# hold_mini.replace('unknown', pd.NA, inplace=True)
# hold_mini.dropna(axis=0, inplace=True)
def feature_engineering(hold_mini):
  hold_mini['contacted_before'] = hold_mini['pdays'].apply(lambda x: 0 if x == 999 else 1)

  hold_mini['job_cat'] = hold_mini['job'].astype('category')
  hold_mini['marital_cat'] = hold_mini['marital'].astype('category')
  hold_mini['education_cat'] = hold_mini['education'].astype('category')
  hold_mini['default_cat'] = hold_mini['default'].astype('category')
  hold_mini['housing_cat'] = hold_mini['housing'].astype('category')
  hold_mini['loan_cat'] = hold_mini['loan'].astype('category')
  hold_mini['contact_cat'] = hold_mini['contact'].astype('category')
  hold_mini['month_cat'] = hold_mini['month'].astype('category')
  hold_mini['day_of_week_cat'] = hold_mini['day_of_week'].astype('category')
  hold_mini['poutcome_cat'] = hold_mini['poutcome'].astype('category')
  hold_mini['contacted_before_cat'] = hold_mini['contacted_before'].astype('category')

  # split feature and target data
  hold_features = ['age', 'job_cat', 'marital_cat', 'education_cat', 'default_cat', 'housing_cat', 'loan_cat', 'contact_cat', 'month_cat', 'day_of_week_cat', 'previous', 'poutcome_cat', 'emp.var.rate', 'cons.price.idx', 'cons.conf.idx', 'euribor3m', 'nr.employed', 'contacted_before_cat']
  hold_mini_X = pd.get_dummies(hold_mini[hold_features])

  # since mini holdout has no yes values for default

  # hold_mini_X.info()
  return hold_mini_X

hold_mini_X = feature_engineering(hold_mini)
hold_mini_X.insert(33, 'default_cat_yes', 0)

hold_pred = clf.predict(hold_mini_X)
hold_pred = (hold_pred == 'yes').astype(int)

print(hold_pred)

accuracy_score(targets, hold_pred)

precision_score(targets, hold_pred)

recall_score(targets, hold_pred)

f1_score(targets, hold_pred)

hold_out = pd.read_csv('https://raw.githubusercontent.com/byui-cse/cse450-course/master/data/bank_holdout_test.csv')
hold_out = feature_engineering(hold_out)
hold_out.insert(33, 'default_cat_yes', 0)

hold_out_pred = clf.predict(hold_out)
hold_out_pred = (hold_out_pred == 'yes').astype(int)

hold_out_pred_series = pd.Series(hold_out_pred)

pred_value_counts = hold_out_pred_series.value_counts()
# print(hold_out_pred_series.columns)
# print(hold_out_pred_series)
count_0 = pred_value_counts.get(0, 'no zeroes')  # Get the count for 0, default to 0 if not found
count_1 = pred_value_counts.get(1, 'no ones')

print(f'{count_0=}')
print(f'{count_1=}')

print(f'{hold_out_pred_series=}')

hold_out_pred_series.to_csv('team1-module2-predictions.csv', index=False, header=['predictions'])



import plotly.express as px
# Access feature importances
feature_importances = clf.feature_importances_

# Create a DataFrame to display feature importances
feature_importance_df = pd.DataFrame({'Feature': X_train.columns, 'Importance': feature_importances})
feature_importance_df.sort_values(by='Importance', ascending=False, inplace=True)

# Print the DataFrame
# print(feature_importance_df.to_string())

barImp = px.bar(feature_importance_df, x='Feature', y='Importance', title='Feature Importance')
barImp.show()

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(20, 20))
plot_tree(clf, fontsize=10, feature_names=X.columns)
plt.show()



