import csv
import time
with open('./articles_govinfo_0.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    while True:
        i = next(reader)
        print(i)
        time.sleep(0.5)