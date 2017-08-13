# -*- coding: utf-8 -*-
import scrapy
import useragent
import proxylist
import config
from scrapy.http import Request
from Amazonscraper.items import AmazonscraperItem
import requests
import time, re, random, base64, csv
import json
from time import sleep
from scrapy.selector import Selector

class SkinCareBodyCleansersSpider(scrapy.Spider):
    name = "Skin_Care_Body_Cleansers"
    allowed_domains = ["amazon.com"]

    proxy_lists = proxylist.proxys
    useragent_lists = useragent.user_agent_list

    baseUrl = "https://www.amazon.com"

    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'en-GB,en-US;q=0.8,en;q=0.6',
        'Cache-Control':'max-age=0',
        'Connection':'keep-alive',
        'Host':'www.amazon.com',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':useragent_lists[random.randrange(0, len(useragent_lists))],   
    }

    def set_proxies(self, url, callback, headers=None):

        req = Request(url=url, callback=callback, dont_filter=True, headers= headers)
        proxy_url = self.proxy_lists[random.randrange(0,len(self.proxy_lists))]
        user_pass=base64.encodestring(b'username:password').strip().decode('utf-8')
        req.meta['proxy'] = "http://" + proxy_url
        req.headers['Proxy-Authorization'] = 'Basic ' + user_pass
        user_agent = self.useragent_lists[random.randrange(0, len(self.useragent_lists))]
        req.headers['User-Agent'] = user_agent

        return req

    def start_requests(self):
        print "====== Start ======"
        
        # Beauty & Personal Care : Skin Care : Body : Cleansers
        url = "https://www.amazon.com/s/ref=lp_11060711_nr_n_2?fst=as%3Aoff&rh=n%3A3760911%2Cn%3A%2111055981%2Cn%3A11060451%2Cn%3A11060711%2Cn%3A11061091&bbn=11060711&ie=UTF8&qid=1502339219&rnid=11060711"
        
        req = self.set_proxies(url, self.getData, headers=self.headers)
        yield req

    def getData(self, response):
        print "===== Get Data ====="

        itemPaths = response.xpath('//ul[contains(@class, "s-result-list")]/li[contains(@id, "result")]')
        for cc, element in enumerate(itemPaths):
            print "----------------------------"
            itemUrl = element.xpath('.//a[@class="a-link-normal s-access-detail-page  s-color-twister-title-link a-text-normal"]/@href').extract_first()
            # print itemUrl
            if "/gp/slredirect/" in itemUrl:
                continue
            req = self.set_proxies(itemUrl, self.getDetail, headers=self.headers)
            req.meta['page_url'] = itemUrl
            yield req

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
            req.meta['page_url'] = itemUrl

            yield req            

    def getDetail(self, response):
        # print "====== Get Detail ======"

        item = AmazonscraperItem()

        page_url = response.meta['page_url']
        item['Page_url'] = page_url

        asin = ''.join(response.xpath('//input[@id="ASIN"]/@value').extract()).strip()
        item['ASIN'] = asin

        brand = ''.join(response.xpath('//div[@id="brandBarLogoWrapper"]//img/@alt').extract()).strip()
        if brand == "":
            brand = ''.join(response.xpath('//div[@id="mbc"]/@data-brand').extract()).strip()        
        item['Brand_Name'] = brand

        product_name = ''.join(response.xpath('//h1[@id="title"]//text()').extract()).strip()
        item['Product_Name'] = product_name
        # print product_name

        catetxt = response.xpath('//span[@class="zg_hrsr_ladder"][1]//text()').extract()
        # print catetxt
        # return
        try:
            del catetxt[0]
        except:
            pass
        cate = ''.join(catetxt).strip()
        item['Category'] = cate
        # print category

        rankSummary = {}
        rankingText1 = ''.join(response.xpath('//li[@id="SalesRank"]/text()').extract()).strip()
        # print rankingText
        # print "----------------"
        rank1 = rankingText1.replace("#", "").replace(" ()", "")
        rankSummary['category rank'] = rank1

        rankList = []
        paths = response.xpath('//ul[@class="zg_hrsr"]/li')
        for ele in paths:

            category = ''.join(ele.xpath('.//span[@class="zg_hrsr_ladder"]//text()').extract()).strip()
            rankingText2 = ''.join(ele.xpath('.//span[@class="zg_hrsr_rank"]/text()').extract()).strip()
            rankingText2 = rankingText2.replace("#", "")
            rank2 = rankingText2 + " " + category
            rankList.append(rank2)

        rankSummary['sub category rank'] = rankList 
        # print ranking
        item['Ranking'] = rankSummary

        price = ''.join(response.xpath('//span[@id="priceblock_ourprice"]/text()').extract()).strip()
        item['Price'] = price
        # print price

        Description = ""
        sentence = response.xpath('//div[@id="visual-rich-product-description"]//div[contains(@class, "a-section a-text-left visualRpdColumnSmall")]')
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
            Description = ''.join(response.xpath('//div[@id="productDescription"]//p/text()').extract()).strip()
            item['Description'] = Description

        importantInfo = ''.join(response.xpath('//div[@class="bucket"]/div[@class="content"]/text()').extract()).strip()
        if importantInfo:
            item['Important_Info'] = importantInfo

        rating = ''.join(response.xpath('//div[@id="reviewSummary"]//span[@class="a-icon-alt"]/text()').extract()).strip()
        item['Rating'] = rating
        # print rating

        reviews = ''.join(response.xpath('//div[@id="reviewSummary"]//span[@data-hook="total-review-count"]/text()').extract()).strip()
        item['Reviews'] = reviews
        # print reviews

        reviewSummary = {}

        star5 = ''.join(response.xpath('//a[@class="a-size-base a-link-normal 5star histogram-review-count"]/text()').extract()).strip()
        reviewSummary["5 star"] = star5
        # print star5

        star4 = ''.join(response.xpath('//a[@class="a-size-base a-link-normal 4star histogram-review-count"]/text()').extract()).strip()
        reviewSummary["4 star"] = star4
        # print star4

        star3 = ''.join(response.xpath('//a[@class="a-size-base a-link-normal 3star histogram-review-count"]/text()').extract()).strip()
        reviewSummary["3 star"] = star3
        # print star3

        star2 = ''.join(response.xpath('//a[@class="a-size-base a-link-normal 2star histogram-review-count"]/text()').extract()).strip()
        reviewSummary["2 star"] = star2
        # print star2

        star1 = ''.join(response.xpath('//a[@class="a-size-base a-link-normal 1star histogram-review-count"]/text()').extract()).strip()
        reviewSummary["1 star"] = star1
        # print star1

        item['ReviewSummary'] = reviewSummary
        
        reviewList = []

        customReviewUrl = ''.join(response.xpath('//a[@id="dp-summary-see-all-reviews"]/@href').extract()).strip()
        # customReviewUrl = customReviewUrl.split("/")[0]
        if customReviewUrl:

            try:
                customReviewUrl = re.sub('(ref=.*)','',customReviewUrl)
            except:
                pass
            url = self.baseUrl + customReviewUrl + "ref=cm_cr_arp_d_show_all?ie=UTF8&reviewerType=all_reviews&pageNumber=1"
            # url = "https://www.amazon.com/Mario-Badescu-Facial-Spray-Rosewater/product-reviews/B002LC9OES/ref=cm_cr_dp_d_show_all_top?ie=UTF8&reviewerType=avp_only_reviews"
            
            s = requests.Session()        
            while True:        
                s.cookies.clear()                
                agent = config.rotateAgent()        
                # print "++++++++++++++++++++"        
                # print agent        
                # print "++++++++++++++++++++"        
                proxy = config.rotateProxy()        
                proxies = {'http':'http://{}@{}'.format(config.proxy_auth, proxy), 'https':'http://{}@{}'.format(config.proxy_auth, proxy)}
                res = s.request('GET', url, headers = self.headers, proxies = proxies)                
                # print res.status_code
                if res.status_code == 200:
                    break
                else:
                    time.sleep(3)

            r = res.text
            htmlText = Selector(text=r)
            
            # total_review_count = ''.join(htmlText.xpath('//li[@data-reftag="cm_cr_arp_d_paging_btm"][last()]/a/text()').extract()).strip()        
            total_review = reviews.replace(",", "")
            total_review_count = int(total_review)/10
            total_review_mod = int(total_review)%10
            if total_review_mod != 0:
                total_review_count = total_review_count + 1
            if total_review_count<0:
                total_review_count = 1

            reviewitems = htmlText.xpath('//div[@id="cm_cr-review_list"]/div[@class="a-section review"]')

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
            if total_review_count>1:

                for page_count in range(2, total_review_count+1):

                    url = self.baseUrl + customReviewUrl + "ref=cm_cr_arp_d_show_all?ie=UTF8&reviewerType=all_reviews&pageNumber=" + str(page_count)
                           
                    while True:        
                        s.cookies.clear()                
                        agent = config.rotateAgent()        
                        # print "++++++++++++++++++++"        
                        # print agent        
                        # print "++++++++++++++++++++"        
                        proxy = config.rotateProxy()        
                        proxies = {'http':'http://{}@{}'.format(config.proxy_auth, proxy), 'https':'http://{}@{}'.format(config.proxy_auth, proxy)}
                        res = s.request('GET', url, headers = self.headers, proxies = proxies)                
                        # print res.status_code
                        if res.status_code == 200:
                            break
                        else:
                            time.sleep(3)

                    r = res.text
                    htmlText = Selector(text=r)
                    reviewitems = htmlText.xpath('//div[@id="cm_cr-review_list"]/div[@class="a-section review"]')
                    
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