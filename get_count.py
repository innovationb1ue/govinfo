import time
import csv
count = 0
csv.field_size_limit(500 * 1024 * 1024)
with open('./articles_govinfo_0_12.csv', encoding='utf-8', errors='ignore', mode='r') as f:
    reader = csv.reader(f)
    for i in reader:
        print(i)
print(count)
time.sleep(10000)