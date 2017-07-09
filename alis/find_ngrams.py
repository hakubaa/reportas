import string
import random
import operator
import itertools
from collections import Counter
from functools import reduce
import pickle

import nltk
import pandas as pd
from sklearn import tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, auc
from sklearn.ensemble import RandomForestClassifier


from rparser.nlp import NGram
from rparser.models import Document
from rparser.util import find_ngrams, find_numbers


# 1) Load reports

from alis.data import reports

# 2) Create development sample
#    - for each document select positive (target) & negatvie pages

random.seed(1)

target_statement = "cfs"
neg_rate = 10 # negative pages / positive pages ratio
ngram_doc_min_freq = 0.5 # minimum number of doc with the ngram


doc_pages = dict()
for report in reports:
    pos_pages = report["statements"][target_statement]
    neg_pages = list(
        set(reduce(operator.add, report["statements"].values())) \
        - set(pos_pages)
    )
    neg_temp = set(range(len(report["doc"]))) - set(neg_pages)
    neg_pages.extend(random.sample(
        neg_temp, 
        min(max(neg_rate * len(pos_pages) - len(neg_pages), 0), len(neg_temp))
    ))

    doc_pages[report["doc"]] = (pos_pages, neg_pages)

# 3) Identify ngrams

doc_ngrams = dict()
ngram_docs = dict() # Reverse doc_ngrams 

number_ngram = NGram("fake#number") # fake ngram for counting numbers
ngram_docs[number_ngram] = set()

page_ngram = NGram("fake#page") # fake page for position
ngram_docs[page_ngram] = set()

for doc, (pos, neg) in doc_pages.items():
    temp = doc_ngrams.setdefault(doc, dict())
    for page in itertools.chain(pos, neg):
        # Find ngrams
        ngrams_temp = find_ngrams(doc[page], 2)
        temp[page] = Counter(ngrams_temp)
        for ngram in ngrams_temp:
            ngram_docs.setdefault(ngram, set()).add(doc)
        
        # Find numbers
        temp[page][number_ngram] = len(find_numbers(doc[page]))
        ngram_docs[number_ngram].add(doc)

        # Set page
        temp[page][page_ngram] = page / len(doc)
        ngram_docs[page_ngram].add(doc)

     
# Remove ngrams with small frequencies
ngrams = [ ngram for ngram in ngram_docs 
                 if len(ngram_docs[ngram]) >= len(reports)*ngram_doc_min_freq ]

# 4) Create dataset for model's development

data_rows = list()
for doc, (pos, neg) in doc_pages.items():
    for page in itertools.chain(pos, neg):
        page_ngrams = doc_ngrams[doc][page]
        data_rows.append(
            [doc, page, 1 if page in pos else 0] + 
            [page_ngrams.get(ngram, 0) for ngram in ngrams]
        )

dataset = pd.DataFrame(
    data_rows, 
    columns=["doc", "page", "target"] + list(range(len(ngrams)))
)

## Model Development

X = dataset.loc[:,list(range(len(ngrams)))]
y = dataset["target"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.33, random_state=1
)

# 5) Decision Tree

# clf = tree.DecisionTreeClassifier()
# clf = clf.fit(X_train, y_train)

# clf.score(X_test, y_test)

# yhat_test = clf.predict(X_test)

# fpr, tpr, _ = roc_curve(y_test, yhat_test)
# roc_auc = auc(fpr, tpr)

# 6) Random Forest

clf = RandomForestClassifier(n_estimators=100)
clf = clf.fit(X_train, y_train)

clf.score(X_test, y_test)

# pd.concat([dataset.loc[:,["doc", "page", "target"]], 
#            pd.DataFrame(clf.predict_proba(X))], axis=1)

clf_ngrams_indeces = list(filter(lambda x: x >= 0, reduce(
    operator.add, 
    [estimator.tree_.feature.tolist() for estimator in clf.estimators_]
)))
clf_ngrams = Counter(ngrams[ngram_index] for ngram_index in clf_ngrams_indeces)

# clf.score(X_test.loc[:,list(clf_ngrams_indeces)], y_test)
# clf.score(X_test, y_test)


################################################################################
# Learn model and save

clf = RandomForestClassifier(n_estimators=100)
clf = clf.fit(X, y)

model = {
    "type": type(clf),
    "clf": clf,
    "ngrams": ngrams
}

with open("parser/cls/%s.pkl" % target_statement, "wb") as f:
    pickle.dump(model, f)