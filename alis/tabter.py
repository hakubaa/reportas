import csv
import itertools
import random
import operator

import numpy as np

from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split

from parser.models import FinancialReport


# initial settings
np.set_printoptions(suppress=True) # turn off scientific notation

random.seed(1) 


# load data
dataset = list()

with open("alis/data_tabter.csv", "r") as f:
	reader = csv.reader(f, delimiter=";", lineterminator="\n")
	dataset.extend(itertools.islice(reader, 70000))

# standardize text length
for row in dataset:
	row[-1] = (row[-1] + 120*' ')[:120]

# split text int features
#
#  0 - white space
#  1 - numeric character 0-9
# -1 - alphabetic character

fmapper = {
	" ": 0,
	"1": 1, "2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 1,	"8": 1, "9": 1
}

for row in dataset:
	row[-1] = list(map(lambda x: fmapper.get(x, -1), row[-1]))

## Create training and test sample
data = list(map(operator.itemgetter(-1), dataset))[1:]
target = [ int(x)for x in list(map(operator.itemgetter(2), dataset))[1:] ]

X = list()
for i in range(1, len(data)-1):
	X.append(data[i-1] + data[i] + data[i+1])
y = target[1:(len(data)-1)]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.33, random_state=1
)

clf = MLPClassifier(
	solver='lbfgs', alpha=1e-5, activation='logistic',
	hidden_layer_sizes=(16,), random_state=1, verbose=True,
	max_iter=200
)
clf.fit(X_train, y_train)

clf.score(X_train, y_train)
clf.score(X_test, y_test)

xhat_train = clf.predict(X_train)
xyhat_test = clf.predict(X_test)  

# test on specific report

doc = FinancialReport("reports/mpk_2016_q3.pdf", spec=spec, voc=voc)

doc_rows = list()
for index, text in enumerate(doc):
	rows = list(enumerate(text.split("\n")))
	doc_rows.extend(map(lambda x: list((doc.docpath, index, 0) + x), rows))

data = list()
for row in doc_rows:
	row120 = (row[-1] + 120*' ')[:120]
	data.append(list(map(lambda x: fmapper.get(x, -1), row120)))
target = [ int(x)for x in list(map(operator.itemgetter(2), data_rows)) ]

X = list()
for i in range(1, len(data)-1):
	X.append(data[i-1] + data[i] + data[i+1])
y = target[1:(len(data)-1)]

yhat = clf.predict(X)

for i in range(1, len(doc_rows)-1):
	doc_rows[i].append(yhat[i-1])

list(itertools.starmap(
	lambda x, y: str(y) + ' - ' + x,
	map(operator.itemgetter(4, 5), filter(lambda x: x[1] in (28,), doc_rows))
))