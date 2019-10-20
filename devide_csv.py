import csv
with open('./article.csv', 'r') as f:
    count = 0
    error_count = 0
    filecount  = 0
    reader = csv.reader(f)
    f = open('./article_%s' % filecount, 'a', errors='ignore')
    writer = csv.writer(f)
    while True:
        try:
            row = next(reader)
        except StopIteration:
            break
        except:
            error_count+= 1
        writer.writerow(row)
        count += 1
        if count == 1000000:
            filecount += 1
            f.close()
            f = open('./article_%s' % filecount, 'a', errors='ignore')
            writer = csv.writer(f)
            count = 0

print(error_count)

