import proxy
from bs4 import BeautifulSoup as bs
from multiprocessing import Pool
import os
import re
import csv
import time
import xlrd
import math



class govinfo:
    def __init__(self):
        self.s = proxy.MyRequests()
        self.catalog2=0
        self.Headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}

    # start crawling
    def start(self):
        sheet = xlrd.open_workbook('./govinfo.xlsx').sheet_by_index(0)
        startrow = 3
        endrow = 8 # MAX = 22
        indexes = sheet.col_values(2)[startrow-1:endrow]
        indexes = [int(i) for i in indexes]
        pages = sheet.col_values(3)[startrow-1:endrow]
        pages = [math.floor(page) for page in pages if page != '']
        for page, index in zip(pages, indexes):
            self.catalog2 = index
            self.multi_crawl_catalog(1, page, worker=16, timeout=12)
            self.multi_crawl_article(worker=16)

    # subprocess generator for list page
    def multi_crawl_catalog(self, startpage, endpage,  worker=4, timeout=8):
        p = Pool(worker)
        flag = (endpage-startpage+1) // worker
        # check wasted pages
        if os.path.exists('./wasted_%s.txt'%self.catalog2):
            with open('./wasted_%s.txt'%self.catalog2, 'r') as f:
                wastedPage = f.read().split('\n')
        else:
            wastedPage = []
        for i in range(worker):
            taskPages = [str(i) for i in range(startpage + i * flag, startpage + (i+1) * flag + 1) if str(i) not in wastedPage]
            p.apply_async(self.crawl_catalog, args=(taskPages,
                                                    self.catalog2,
                                                    timeout
                                                    )
                          )
        p.close()
        p.join()

    # crawl whole list page main function
    def crawl_catalog(self, pageindexlist, catalog2, timeout=8):
        for pageindex in pageindexlist:
            try:
                print('Getting %s'%pageindex)
                content = self.get_menu_page(pageindex, catalog2=catalog2, timeout=timeout)
                if content:
                    soup = bs(content, 'lxml')
                    tds = soup.find_all('a', attrs={'target':'_blank'})
                    urls = [i['href'] for i in tds[1:]]
                    with open('./urls_%s.txt'%self.catalog2, 'a') as f:
                        for url in urls:
                            f.write(url)
                            f.write('\n')
                    with open('./wasted_%s.txt'%self.catalog2, 'a') as f:
                        f.write(str(pageindex))
                        f.write('\n')
            except Exception as e:
                print(e)
                with open('./error_page.txt', 'a') as f:
                    f.write(pageindex)
                    f.write('\n')
                with open('./Exception.txt', 'a') as f:
                    f.write(str(e))
                    f.write('\n')

                continue

    # get specific list page (component function)
    def get_menu_page(self, page=1, catalog2=363, timeout=2):
        url = 'http://govinfo.nlc.cn/search/pagezgb.jsp?catalog2=%s&tcfl=&page=%s'%(catalog2, page)
        resp = self.s.get(url, timeout=timeout, retry=True, retryMax=5)
        if resp:
            content = resp.content.decode('utf-8')
            return content
        else:
            return ''

    def multi_crawl_article(self, worker=4):
        p = Pool(worker)
        with open('./urls_%s.txt'%self.catalog2, 'r') as f:
            urlList = f.read().split('\n')
        if os.path.exists('./wasted_urls_%s.txt'%self.catalog2):
            with open('./wasted_urls_%s.txt'%self.catalog2, 'r') as f:
                wasted = f.read().split('\n')
        else:
            wasted = set()
        urlList = list(set(urlList).symmetric_difference(set(wasted)))
        print('total=', len(urlList))
        flag = len(urlList) // worker
        print('worker = ', worker)
        for i in range(worker):
            task = urlList[i*flag: (i+1)*flag]
            print(len(task))
            p.apply_async(self.crawl_article, args=(task,))
        p.close()
        p.join()

    # subprocess function crawl article (components function)
    def crawl_article(self, urlList):
        for url in urlList:
            try:
                title, body = self.get_article_info(url, timeout=8)
                # check whether the article info is correct or not
                if [title, body] == [1, 1]:
                    with open('./wasted_urls_%s.txt' % self.catalog2, 'a', encoding='utf-8', errors='ignore') as f:
                        f.write(url)
                        f.write('\n')
                    continue
                with open('./articles_govinfo_%s.csv'%self.catalog2, 'a', encoding='utf-8',errors='ignore', newline='') as f:
                    print(title)
                    writer = csv.writer(f)
                    writer.writerow([title, body])
                with open('./wasted_urls_%s.txt'%self.catalog2, 'a', encoding='utf-8', errors='ignore') as f:
                    f.write(url)
                    f.write('\n')
            except Exception as e:
                print(e)
                with open('./Exception.txt', 'a') as f:
                    f.write(str(e))
                    f.write('\n')


    # get specific page details(component function)
    def get_article_info(self, url:str, timeout=4):
        try:
            resp = self.s.get(url, timeout=timeout, retry=True, retryMax=5)
        except Exception as e:
            print(e)
            with open('Exception.txt', 'a') as f:
                f.write(str(e))
                f.write('\n')
            return ['', '']
        try:
            if resp:
                content = resp.content.decode('utf-8')
                soup = bs(content, 'lxml')
                title_tag = soup.find('td', attrs={'class':'dbiaoti'})
                if title_tag:
                    title = title_tag.text
                else:
                    title = ''
                # method 1
                infoTags = re.findall('OpenWindow.document.write\("(.*?)"\)', content)
                if infoTags:
                    body = infoTags[2]
                    return[title, body]

                # method 2
                article_tag = soup.find('td', attrs={'class':'zw_link'})
                if article_tag:
                    if article_tag.img:
                        img_tag_list = article_tag.find_all('img')
                        for img_tag in img_tag_list:
                            postfix = img_tag['src']
                            bimg = self.s.get(url.replace(url.split('/')[-1], postfix)).content
                            with open('./Imgs/%s.png' % time.time(), 'wb') as f:
                                f.write(bimg)
                    article1 = article_tag.text
                    if article1:
                        return [title, article1]

                # method 3
                article = soup.find('td', attrs={'class':'bg_link'})
                if article:
                    if article.img:
                        with open('./ImgUrls.txt', 'a') as f:
                            f.write(url)
                            f.write('\n')
                        img_tag_list = article.find_all('img')
                        for img_tag in img_tag_list:
                            postfix = img_tag['src']
                            bimg = self.s.get(url.replace(url.split('/')[-1], postfix)).content
                            with open('./Imgs/%s.png' % time.time(), 'wb') as f:
                                f.write(bimg)
                    article1 = article.text
                    if article1:
                        return [title, article1]

                # return False condition
                else:
                    with open('./fail.txt','a' ) as f:
                        f.write(url)
                        f.write('\n')
                    return [1, 1]
            else:
                return [1, 1]
        except Exception as e:
            print(e)
            with open('Exception.txt', 'a') as f:
                f.write(str(e))
                f.write('\n')
            return ['', '']







if __name__ == '__main__':
    e = govinfo()
    e.start()
