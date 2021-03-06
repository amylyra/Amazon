# -*- coding: utf-8 -*-
import scrapy
import config
from scrapy.http import Request
from Amazonscraper.items import AmazonscraperItem
import requests
import time, re, random, base64, csv
import json
from time import sleep
from scrapy.selector import Selector
import datetime

class MakeupBrushesToolsFaceSpider(scrapy.Spider):
    name = "Makeup_Brushes_Tools_Face"
    allowed_domains = ["amazon.com"]

    proxy_lists = config.proxies
    useragent_lists = config.agents
    total = 0
    baseUrl = "https://www.amazon.com"

    headers = {
        'User-Agent': useragent_lists[random.randrange(0, len(useragent_lists))],
    }

    def set_proxies(self, url, callback, headers=None):

        req = Request(url=url, callback=callback, dont_filter=True, headers= headers)
        proxy_url = self.proxy_lists[random.randrange(0,len(self.proxy_lists))]
        user_pass=base64.encodestring(config.proxy_auth).strip().decode('utf-8')
        req.meta['proxy'] = "http://" + proxy_url
        req.headers['Proxy-Authorization'] = 'Basic ' + user_pass
        user_agent = self.useragent_lists[random.randrange(0, len(self.useragent_lists))]
        req.headers['User-Agent'] = user_agent

        return req
    def start_requests(self):

        self.clearLog()
        self.makeLog("Start")

        url = "https://www.amazon.com/s/ref=sr_nr_n_0?fst=as%3Aoff&rh=n%3A3760911%2Cn%3A%2111055981%2Cn%3A11058281%2Cn%3A11058691%2Cn%3A11058701&bbn=11058691&ie=UTF8&qid=1502833838&rnid=11058691"
        req = self.set_proxies(url, self.getData, headers=self.headers)
        yield req

    def getData(self, response):
        print "===== Get Data ====="
      
        try:
            if "To discuss automated access to Amazon data please contact" in response.body:
                print "========= > None data"
                req = self.set_proxies(response.url, self.getData, headers=self.headers)
                sleep(2)
                yield req

            itemPaths = response.xpath('//ul[contains(@class, "s-result-list")]/li[contains(@id, "result")]')
            for cc, element in enumerate(itemPaths):
                print "----------------------------"
                itemUrl = element.xpath('.//a[@class="a-link-normal s-access-detail-page  s-color-twister-title-link a-text-normal"]/@href').extract_first()
                # print itemUrl
                if "/gp/slredirect/" in itemUrl:
                    continue

                item = AmazonscraperItem()
                s = requests.Session()
                error_count = 0
                asin = ""
                reviewList = []
                reviewSummary = {}

                customReviewUrl = ""
                while True:
                    s.cookies.clear()

                    agent = config.rotateAgent()
                    proxy = config.rotateProxy()        
                    print proxy

                    proxies = {'http':'http://{}@{}'.format(config.proxy_auth, proxy), 'https':'http://{}@{}'.format(config.proxy_auth, proxy)}
                    try:
                        res = s.request('GET', itemUrl, headers = self.headers, proxies = proxies)   
                        # print itemUrl
                    except:
                        error_count = error_count + 1
                        continue

                    if error_count==10:
                        break
                    # print res.status_code
                    elif res.status_code == 200:
                        if "To discuss automated access to Amazon data please contact" in res.content:
                            print "==========> No none ========="
                            # sleep(2)
                            continue                            
                        else:
                            r = res.text
                            htmlBody = Selector(text=r)
                            asin = ''.join(htmlBody.xpath('//input[@id="ASIN"]/@value').extract()).strip()
                            if asin != "":                                                 
                                break                
                            else:
                                print "***** Asin None *****"
                                # print htmlBody
                                error_count = error_count + 1
                                if error_count==10:
                                    break
                                continue
                if error_count==10:
                    continue

                catetxt = htmlBody.xpath('//ul[@class="a-unordered-list a-horizontal a-size-small"]//text()').extract()
                cate = re.sub(" +", " ", re.sub("\s", " ", ''.join(catetxt)).strip())
                
                if "Beauty" and "Personal" not in cate:
                    continue 

                item['Category'] = cate
                # print category 

                item['Page_url'] = itemUrl
                item['ASIN'] = asin

                brand = ''.join(htmlBody.xpath('//div[@id="brandBarLogoWrapper"]//img/@alt').extract()).strip()
                if brand == "":
                    brand = ''.join(htmlBody.xpath('//div[@id="mbc"]/@data-brand').extract()).strip()        
                item['Brand_Name'] = brand

                product_name = ''.join(htmlBody.xpath('//h1[@id="title"]//text()').extract()).strip()
                item['Product_Name'] = product_name
                # print product_name

                rankSummary = {}
                rankingText1 = ''.join(htmlBody.xpath('//li[@id="SalesRank"]/text()').extract()).strip()
                # print rankingText
                # print "----------------"
                rank1 = rankingText1.replace("#", "").replace(" ()", "")
                rankSummary['category rank'] = rank1

                rankList = []
                paths = htmlBody.xpath('//ul[@class="zg_hrsr"]/li')
                for ele in paths:

                    category = ''.join(ele.xpath('.//span[@class="zg_hrsr_ladder"]//text()').extract()).strip()
                    rankingText2 = ''.join(ele.xpath('.//span[@class="zg_hrsr_rank"]/text()').extract()).strip()
                    rankingText2 = rankingText2.replace("#", "")
                    rank2 = rankingText2 + " " + category
                    rankList.append(rank2)

                rankSummary['sub category rank'] = rankList 
                # print ranking
                item['Ranking'] = rankSummary

                price = ''.join(htmlBody.xpath('//span[contains(@id, "priceblock_")]/text()').extract()).strip()
                item['Price'] = price
                # print price

                Description = ""
                sentence = htmlBody.xpath('//div[@id="visual-rich-product-description"]//div[contains(@class, "a-section a-text-left visualRpdColumnSmall")]')
                # print len(sentence)
                for element in sentence:
                    # print "----------------"
                    text = ''.join(element.xpath('.//h4/text()').extract()).strip()

                    if "Description" in text:
                        Description = ''.join(element.xpath('.//span[@class="a-size-small a-color-base visualRpdText"]/text()').extract()).strip()
                        item['Description'] = Description
                        # print Description

                    elif "Benefits" in text:
                        Benefits = ''.join(element.xpath('.//span[@class="a-size-small a-color-base visualRpdText"]/text()').extract()).strip()
                        item['Benefits'] = Benefits
                        # print Benefits

                    elif "Suggested" in text:
                        Suggested_Use = ''.join(element.xpath('.//span[@class="a-size-small a-color-base visualRpdText"]/text()').extract()).strip()
                        item['Suggested_Use'] = Suggested_Use
                        # print Suggested_Use

                if Description=="":
                    Description = ''.join(htmlBody.xpath('//div[@id="productDescription"]//p/text()').extract()).strip()
                    item['Description'] = Description

                importantInfo = ''.join(htmlBody.xpath('//div[@class="bucket"]/div[@class="content"]/text()').extract()).strip()
                if importantInfo:
                    item['Important_Info'] = importantInfo

                rating = ''.join(htmlBody.xpath('//div[@id="reviewSummary"]//span[@class="a-icon-alt"]/text()').extract()).strip()
                item['Rating'] = rating
                # print rating

                reviews = ''.join(htmlBody.xpath('//div[@id="reviewSummary"]//span[@data-hook="total-review-count"]/text()').extract()).strip()
                item['Reviews'] = reviews
                # print reviews

                star5 = ''.join(htmlBody.xpath('//a[@class="a-size-base a-link-normal 5star histogram-review-count"]/text()').extract()).strip()
                reviewSummary["5 star"] = star5
                # print star5

                star4 = ''.join(htmlBody.xpath('//a[@class="a-size-base a-link-normal 4star histogram-review-count"]/text()').extract()).strip()
                reviewSummary["4 star"] = star4
                # print star4

                star3 = ''.join(htmlBody.xpath('//a[@class="a-size-base a-link-normal 3star histogram-review-count"]/text()').extract()).strip()
                reviewSummary["3 star"] = star3
                # print star3

                star2 = ''.join(htmlBody.xpath('//a[@class="a-size-base a-link-normal 2star histogram-review-count"]/text()').extract()).strip()
                reviewSummary["2 star"] = star2
                # print star2

                star1 = ''.join(htmlBody.xpath('//a[@class="a-size-base a-link-normal 1star histogram-review-count"]/text()').extract()).strip()
                reviewSummary["1 star"] = star1
                # print star1

                item['ReviewSummary'] = reviewSummary                 


                print "*****************************************"
                print "Reviews=", reviews
                print "*****************************************"

                reviews = reviews.encode('utf-8')

                if reviews != "":
                       
                    customReviewUrl = ''.join(htmlBody.xpath('//a[@id="dp-summary-see-all-reviews"]/@href').extract()).strip()
                    try:
                        customReviewUrl = re.sub('(ref=.*)','',customReviewUrl)

                    except:
                        pass
                    reviewUrl = self.baseUrl + customReviewUrl + "ref=cm_cr_arp_d_show_all?ie=UTF8&reviewerType=all_reviews&pageNumber=1"
                    # print reviewUrl

                    s = requests.Session()
                    error_count1 = 0
                    while True:        
                        s.cookies.clear()                
                        agent = config.rotateAgent()        
   
                        proxy = config.rotateProxy()  
                        print proxy      
                        proxies = {'http':'http://{}@{}'.format(config.proxy_auth, proxy), 'https':'http://{}@{}'.format(config.proxy_auth, proxy)}
                        try:
                            res = s.request('GET', reviewUrl, headers = self.headers, proxies = proxies)    
                        except:
                            error_count1 = error_count1 + 1
                            continue

                        if error_count1==10:
                            break

                        # print res.status_code
                        elif res.status_code == 200:
                            if "To discuss automated access to Amazon data please contact" in res.content:
                                print "==========> No none ========="

                                # sleep(2)
                                continue                            
                            else:
                                r = res.text
                                htmlText = Selector(text=r) 
                                reviewitems = htmlText.xpath('//div[@id="cm_cr-review_list"]/div[@class="a-section review"]')
                                if len(reviewitems)==0:
                                    print "****** Review Items None ******"
                                    error_count = error_count + 1
                                    if error_count==10:
                                        break                                    
                                    continue                                                                        
                                else:
                                    break 
                    
                    total_review = reviews.replace(",", "")
                    total_review_count = int(total_review)/10
                    total_review_mod = int(total_review)%10
                    if total_review_mod != 0:
                        total_review_count = total_review_count + 1
                    if total_review_count<0:
                        total_review_count = 1


                    # print "*****************************************"
                    # print "Review Count ==== >> " ,len(reviewitems)
                    # print "*****************************************"

                    for element in reviewitems:
                        sitem = {}

                        # print "-----------------------"
                        review_rating = ''.join(element.xpath('.//i[@data-hook="review-star-rating"]/span/text()').extract()).strip()
                        sitem["review_rating"] = review_rating
                        # print review_rating

                        review_title = ''.join(element.xpath('.//a[@data-hook="review-title"]/text()').extract()).strip()
                        sitem["review_title"] = review_title
                        # print review_title

                        is_verified_purchase = ''.join(element.xpath('.//span[@data-hook="avp-badge"]/text()').extract()).strip()
                        sitem["is_verified_purchase"] = is_verified_purchase
                        # print is_verified_purchase

                        reviewer_name = ''.join(element.xpath('.//a[@data-hook="review-author"]/text()').extract()).strip()
                        sitem["reviewer_name"] = reviewer_name
                        # print reviewer_name

                        review_date = ''.join(element.xpath('.//span[@data-hook="review-date"]/text()').extract()).strip()
                        review_date = review_date.replace("on ", "")
                        sitem["review_date"] = review_date
                        # print review_date

                        review_text = ''.join(element.xpath('.//span[@data-hook="review-body"]/text()').extract()).strip()
                        sitem["review_text"] = review_text
                        # print review_text

                        people_found_usefull = ''.join(element.xpath('.//span[@data-hook="helpful-vote-statement"]/text()').extract()).strip()
                        sitem["people_found_usefull"] = people_found_usefull
                        # print people_found_usefull

                        reviewList.append(sitem)
                    # print total_review_count

                    # print "*****************************************"
                    # print "Total Review = ", total_review_count
                    # print "*****************************************"
                    if total_review_count>1:

                        for page_count in range(2, total_review_count+1):

                            reviewUrl = self.baseUrl + customReviewUrl + "ref=cm_cr_arp_d_paging_btm_next_" + str(page_count) + "?ie=UTF8&reviewerType=all_reviews&pageNumber=" + str(page_count)
                                                                         
                            error_count2 = 0
                            s = requests.Session()
                            while True:        
                                s.cookies.clear()                
                                agent = config.rotateAgent()        
                                # print "++++++++++++++++++++"        
                                # print agent        
                                # print "++++++++++++++++++++"        
                                proxy = config.rotateProxy()        
                                proxies = {'http':'http://{}@{}'.format(config.proxy_auth, proxy), 'https':'http://{}@{}'.format(config.proxy_auth, proxy)}
                                try:
                                    res = s.request('GET', reviewUrl, headers = self.headers, proxies = proxies)    
                                except:
                                    error_count2 = error_count2 + 1
                                    continue

                                if error_count2==10:
                                    break   

                                elif res.status_code == 200:
                                    if "To discuss automated access to Amazon data please contact" in res.content:
                                        print "==========> No none ========="

                                        # sleep(2)
                                        continue                            
                                    else:
                                        r = res.text
                                        htmlText = Selector(text=r) 
                                        reviewitems = htmlText.xpath('//div[@id="cm_cr-review_list"]/div[@class="a-section review"]')
                                        if len(reviewitems)==0:
                                            print "****** Review Items None ******"
                                            error_count = error_count + 1
                                            if error_count==10:
                                                break                                            
                                            continue                                                                        
                                        else:
                                            break  

                            # print "*****************************************"
                            # print "Review Count 2 ==== >> " ,len(reviewitems)
                            # print "*****************************************"                                

                            for element in reviewitems:
                                sitem ={}

                                # print "-----------------------"
                                review_rating = ''.join(element.xpath('.//i[@data-hook="review-star-rating"]/span/text()').extract()).strip()
                                sitem["review_rating"] = review_rating
                                # print review_rating

                                review_title = ''.join(element.xpath('.//a[@data-hook="review-title"]/text()').extract()).strip()
                                sitem["review_title"] = review_title
                                # print review_title

                                is_verified_purchase = ''.join(element.xpath('.//span[@data-hook="avp-badge"]/text()').extract()).strip()
                                sitem["is_verified_purchase"] = is_verified_purchase
                                # print is_verified_purchase

                                reviewer_name = ''.join(element.xpath('.//a[@data-hook="review-author"]/text()').extract()).strip()
                                sitem["reviewer_name"] = reviewer_name
                                # print reviewer_name

                                review_date = ''.join(element.xpath('.//span[@data-hook="review-date"]/text()').extract()).strip()
                                review_date = review_date.replace("on ", "")
                                sitem["review_date"] = review_date
                                # print review_date

                                review_text = ''.join(element.xpath('.//span[@data-hook="review-body"]/text()').extract()).strip()
                                sitem["review_text"] = review_text
                                # print review_text

                                people_found_usefull = ''.join(element.xpath('.//span[@data-hook="helpful-vote-statement"]/text()').extract()).strip()
                                sitem["people_found_usefull"] = people_found_usefull
                                # print people_found_usefull
                                
                                reviewList.append(sitem) 

                    item["Consumer_Reviews"] = reviewList
                    # print customReviewUrl
                yield item
                # print item
                reviewList = []
                reviewSummary = {}
                self.total = self.total + 1
                print "*****************************************"
                print "Total ===== > " + str(self.total)
                print "page_url ===== > " + itemUrl
                print "*****************************************"

                # return
            # test
            # self.page_count = self.page_count + 1
            # if self.page_count==6:
            #     return

            nextUrl = response.xpath('//a[@title="Next Page"]/@href').extract_first()

            if nextUrl:
                nextPage = self.baseUrl + nextUrl
                # print "------------------"
                # print nextPage
                req = self.set_proxies(nextPage, self.getData, headers=self.headers)
                self.makeLog(nextPage)
                yield req
               
        except Exception as e:
            print "******************Except**************"
            print e
            self.makeLog(itemUrl)

    def makeLog(self, txt):

        standartdate = datetime.datetime.now()
        date = standartdate.strftime('%Y-%m-%d %H:%M:%S')
        fout = open("log.txt", "a")
        fout.write(str(date) + " -> " + txt + "\n")
        fout.close()

    def clearLog(self):
        fout = open("log.txt", "w")
        fout.close()