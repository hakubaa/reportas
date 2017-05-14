import operator
import csv

from alis.data import reports


dataset = list()
for report in map(operator.itemgetter("doc"), reports):
	for index, text in enumerate(report):
		rows = list(enumerate(text.split("\n")))
		dataset.extend(map(lambda x: (report.docpath, index, 0) + x, rows))


with open("alis/data_tabter2.csv", "w") as out:
	csv_out = csv.writer(out, delimiter=";", lineterminator="\n")
	csv_out.writerow(["report", "page", "target", "row", "text"])
	for row in dataset:
		csv_out.writerow(row)

