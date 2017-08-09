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

class LuxurybeautyskincareSpider(scrapy.Spider):
    name = "LuxuryBeautySkinCare"
    allowed_domains = ["amazon.com"]

    proxy_lists = proxylist.proxys
    useragent_lists = useragent.user_agent_list
    page_count = 0
    baseUrl = "https://www.amazon.com"

    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'en-GB,en-US;q=0.8,en;q=0.6',
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

        # Luxury Beauty : Skin Care
        url = "https://www.amazon.com/Skin-Body-Face-Luxury-Beauty-Products/b/ref=lxbeauty_skincare_leftnav?ie=UTF8&node=7175562011&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=merchandised-search-leftnav&pf_rd_r=GJNADTC54DRZBJDBAR7X&pf_rd_r=GJNADTC54DRZBJDBAR7X&pf_rd_t=101&pf_rd_p=b6e90c6b-ae6e-45cd-9c68-2fb43609cf4a&pf_rd_p=b6e90c6b-ae6e-45cd-9c68-2fb43609cf4a&pf_rd_i=7175545011"
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

        nextUrl = response.xpath('//a[@title="Next Page"]/@href').extract_first()

        if nextUrl:
            nextPage = self.baseUrl + nextUrl

            req = self.set_proxies(nextPage, self.getData, headers=self.headers)
            req.meta['page_url'] = itemUrl

            yield req            

    def getDetail(self, response):
        print "====== Get Detail ======"

        item = AmazonscraperItem()

        page_url = response.meta['page_url']
        item['Page_url'] = page_url

        asin = ''.join(response.xpath('//input[@id="ASIN"]/@value').extract()).strip()
        item['ASIN'] = asin

        brand = ''.join(response.xpath('//div[@id="brandBarLogoWrapper"]//img/@alt').extract()).strip()
        item['Brand_Name'] = brand

        product_name = ''.join(response.xpath('//h1[@id="title"]//text()').extract()).strip()
        item['Product_Name'] = product_name
        # print product_name

        catetxt = response.xpath('//span[@class="zg_hrsr_ladder"][1]//text()').extract()
        try:
            del catetxt[0]
        except:
            pass
        cate = ''.join(catetxt).strip()
        item['Category'] = cate
        # print category

        rankSummary = {}
        rankingText1 = ''.join(response.xpath('//li[@id="SalesRank"]/text()').extract()).strip()

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

        sentence = response.xpath('//div[@id="visual-rich-product-description"]//div[contains(@class, "a-column a-span4")]')
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

        if customReviewUrl:

            try:
                customReviewUrl = re.sub('(ref=.*)','',customReviewUrl)
            except:
                pass
            url = self.baseUrl + customReviewUrl + "ref=cm_cr_arp_d_show_all?ie=UTF8&reviewerType=all_reviews&pageNumber=1"
            
            s = requests.Session()        
            while True:        
                s.cookies.clear()                
                agent = config.rotateAgent()        
                proxy = config.rotateProxy()        
                proxies = {'http':'http://{}@{}'.format(config.proxy_auth, proxy), 'https':'http://{}@{}'.format(config.proxy_auth, proxy)}
                res = s.request('GET', url, headers = self.headers, proxies = proxies)                

                if res.status_code == 200:
                    break
                else:
                    time.sleep(3)

            r = res.text
            htmlText = Selector(text=r)
            
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

