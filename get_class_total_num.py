import requests
from bs4 import BeautifulSoup as bs
s = requests.Session()
content = s.get('http://govinfo.nlc.cn/index_4602.html?classid=363&title=%E8%B4%A2%E6%94%BF%E3%80%81%E9%87%91%E8%9E%8D%E3%80%81%E5%AE%A1%E8%AE%A1').content.decode('utf-8')
soup = bs(content, 'lxml')
total_tags = soup.find_all('td', attrs={'class': 'ty_link'})
span_tags = [i.span for i in total_tags]
for span in span_tags:
    print(span['id'].split('_')[1])