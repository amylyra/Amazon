# -*- coding: utf-8 -*-
import scrapy
import useragent
from scrapy.http import Request
from Walgreens.items import WalgreensItem
import requests
import time, re, random, base64, csv
import json
from time import sleep
from scrapy.selector import Selector

class WalgreenspiderSpider(scrapy.Spider):
    name = "walgreenspider"
    allowed_domains = ["walgreens.com"]
    useragent_lists = useragent.user_agent_list
      
    baseUrl = "https://www.walgreens.com"

    headers = {
        'Accept':'application/json, text/plain, */*',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'en-GB,en-US;q=0.8,en;q=0.6',
        'Content-Type':'application/json;charset=UTF-8',
        'User-Agent':useragent_lists[random.randrange(0, len(useragent_lists))],
    }
 
    def start_requests(self):

        prodList = []

        url = "https://customersearch.walgreens.com/productsearch/v1/products/search"
        payload = {"p":1,"s":"24","sort":"Top Sellers","view":"allView","geoTargetEnabled":"false","id":["359434"],"abtest":["showNewCategories"],"requestType":"tier3","deviceType":"desktop"}
        json_data = requests.post(url, headers=self.headers, data=json.dumps(payload)).text

        jsonData = json.loads(json_data)
        totalNumPages = jsonData["summary"]["totalNumPages"]

        for items in jsonData["products"]:
            prodId = items["productInfo"]["prodId"]
            prodList.append(prodId)

        for pagenum in range(2, int(totalNumPages)+1):
            param = {"id":["359434"],"p":pagenum,"s":"24","sort":"Top Sellers","view":"allView","requestType":"tier3","clearAllSelections":"/store/c/productlist/N=359434","deviceType":"desktop","populateChannelAvailMap":"true","reqsPerPage":"24","abtest":["showNewCategories"]}
        
            json_data = requests.post(url, headers=self.headers, data=json.dumps(payload)).text

            jsonData = json.loads(json_data)

            for items in jsonData["products"]:
                prodId = items["productInfo"]["prodId"]
                prodList.append(prodId)   

        for cc, prodid in enumerate(prodList):

            url = "https://www.walgreens.com/svc/products/" + prodid + "/(PriceInfo+Inventory+ProductInfo+ProductDetails)?rnd=1501805117091&app=dotcom&instart_disable_injection=true"

            req = Request(url=url, callback=self.getData, headers=self.headers, dont_filter=True)
            req.meta['prodid'] = prodid

            yield req

    def getData(self, response):
        
        item = WalgreensItem()

        prodid = response.meta['prodid']

        json_data = json.loads(response.body)

        title = json_data["productInfo"]["title"]
        item['Product_name'] = ''.join(title).strip()
 
        skuId = json_data["productInfo"]["skuId"] 
        item['skuId'] = skuId
        
        upc = json_data["inventory"]["upc"]
        item['upc'] = upc
        
        wicId = json_data["inventory"]["wicId"]
        item['wicId'] = wicId
        
        sizeCount = json_data["productInfo"]["sizeCount"] 
        item['sizeCount'] = sizeCount 
        
        item['productId'] = prodid 
        
        productImageUrl = json_data["productInfo"]["productImageUrl"]
        productImageUrl = "https:" + productImageUrl
        item['productImageUrl'] = productImageUrl
        
        brandName = json_data["productInfo"]["brandName"]
        item['brandName'] = brandName
        
        regularPrice = json_data["priceInfo"]["regularPrice"]
        item['regularPrice'] = regularPrice
        
        url = "https://api.bazaarvoice.com/data/batch.json?passkey=tpcm2y0z48bicyt0z3et5n2xf&apiversion=5.5&displaycode=2001-en_us&resource.q0=products&filter.q0=id%3Aeq%3A" + prodid + "&stats.q0=reviews&filteredstats.q0=reviews&filter_reviews.q0=contentlocale%3Aeq%3Aen%2Cen_AU%2Cen_CA%2Cen_GB%2Cen_US&filter_reviewcomments.q0=contentlocale%3Aeq%3Aen%2Cen_AU%2Cen_CA%2Cen_GB%2Cen_US&resource.q1=reviews&filter.q1=isratingsonly%3Aeq%3Afalse&filter.q1=productid%3Aeq%3A" + prodid + "&filter.q1=contentlocale%3Aeq%3Aen%2Cen_AU%2Cen_CA%2Cen_GB%2Cen_US&sort.q1=relevancy%3Aa1&stats.q1=reviews&filteredstats.q1=reviews&include.q1=authors%2Cproducts%2Ccomments&filter_reviews.q1=contentlocale%3Aeq%3Aen%2Cen_AU%2Cen_CA%2Cen_GB%2Cen_US&filter_reviewcomments.q1=contentlocale%3Aeq%3Aen%2Cen_AU%2Cen_CA%2Cen_GB%2Cen_US&filter_comments.q1=contentlocale%3Aeq%3Aen%2Cen_AU%2Cen_CA%2Cen_GB%2Cen_US&limit.q1=8&offset.q1=0&limit_comments.q1=3&callback=BV._internal.dataHandler0"
        contentJson = requests.get(url=url).text

        sub_data = re.search("BV._internal\.dataHandler0\((.*)\)", contentJson, re.M|re.S).group(1)
        
        jsonData = json.loads(sub_data)
        
        category = jsonData["BatchedResults"]["q0"]["Results"][0]["Attributes"]["MerchantCategory"]["Values"][0]["Value"]
        item["category"] = category

        ProductPageUrl = jsonData["BatchedResults"]["q0"]["Results"][0]["ProductPageUrl"]
        item["ProductPageUrl"] = ProductPageUrl

        revitem ={}
        RecommendedCount = jsonData["BatchedResults"]["q0"]["Results"][0]["FilteredReviewStatistics"]["RecommendedCount"]
        revitem['RecommendedCount'] = RecommendedCount

        reviewCount = jsonData["BatchedResults"]["q0"]["Results"][0]["FilteredReviewStatistics"]["TotalReviewCount"]
        revitem['reviewCount'] = reviewCount
        
        overallRating = jsonData["BatchedResults"]["q0"]["Results"][0]["FilteredReviewStatistics"]["AverageOverallRating"]
        revitem['overallRating'] = overallRating
        
        RatingDistribution = jsonData["BatchedResults"]["q0"]["Results"][0]["FilteredReviewStatistics"]["RatingDistribution"]
        revitem["RatingDistribution"] = RatingDistribution

        item["Review"] = revitem

        TotalResults = jsonData["BatchedResults"]["q1"]["TotalResults"]
        
        reviewList = []
        for element in jsonData["BatchedResults"]["q1"]["Results"]:
            sitem ={}
            sitem["rating"] = element["Rating"]
            sitem["ReviewText"] = element["ReviewText"]
            sitem["SubmissionTime"] = element["SubmissionTime"]
            sitem["UserLocation"] = element["UserLocation"]
            sitem["Title"] = element["Title"]
            sitem["UserNickname"] = element["UserNickname"]

            flag = element["IsRecommended"]

            if flag == True:
                sitem["IsRecommended"] = "Yes, I recommend this product."
            elif flag == False:
                sitem["IsRecommended"] = "No, I do not recommend this product."
            reviewList.append(sitem)

        for count in range(0, int(TotalResults)):
            offset = 8 + count*30
            url = "https://api.bazaarvoice.com/data/batch.json?passkey=tpcm2y0z48bicyt0z3et5n2xf&apiversion=5.5&displaycode=2001-en_us&resource.q0=reviews&filter.q0=isratingsonly%3Aeq%3Afalse&filter.q0=productid%3Aeq%3A" + prodid + "&filter.q0=contentlocale%3Aeq%3Aen%2Cen_AU%2Cen_CA%2Cen_GB%2Cen_US&sort.q0=relevancy%3Aa1&stats.q0=reviews&filteredstats.q0=reviews&include.q0=authors%2Cproducts%2Ccomments&filter_reviews.q0=contentlocale%3Aeq%3Aen%2Cen_AU%2Cen_CA%2Cen_GB%2Cen_US&filter_reviewcomments.q0=contentlocale%3Aeq%3Aen%2Cen_AU%2Cen_CA%2Cen_GB%2Cen_US&filter_comments.q0=contentlocale%3Aeq%3Aen%2Cen_AU%2Cen_CA%2Cen_GB%2Cen_US&limit.q0=30&offset.q0=" + str(offset) + "&limit_comments.q0=3&callback=BV._internal.dataHandler0"    
            contentJson = requests.get(url=url).text
            try:
                sub_data = re.search("BV._internal\.dataHandler0\((.*)\)", contentJson, re.M|re.S).group(1)
            except:
                sub_data = contentJson
                
            if sub_data:

                jsonData = json.loads(sub_data)

                for element in jsonData["BatchedResults"]["q0"]["Results"]:
                    sitem ={}
                    sitem["rating"] = element["Rating"]
                    sitem["ReviewText"] = element["ReviewText"]
                    sitem["SubmissionTime"] = element["SubmissionTime"]
                    sitem["UserLocation"] = element["UserLocation"]
                    sitem["Title"] = element["Title"]
                    sitem["UserNickname"] = element["UserNickname"]

                    flag = element["IsRecommended"]
                    if flag == True:
                        sitem["IsRecommended"] = "Yes, I recommend this product."
                    elif flag == False:
                        sitem["IsRecommended"] = "No, I do not recommend this product."
                    reviewList.append(sitem)

            if offset>int(TotalResults):
                break

        item["ReviewText"] = reviewList
# ---------------------------------------------------------        
        ingredientsUrl = "https://www.walgreens.com/store/store/ingredient.jsp?id=" + prodid
        ingredientsText = requests.get(url=ingredientsUrl).text

        ingredientsText = Selector(text=ingredientsText).xpath('//p/text()').extract()
        item['ingredients'] = ingredientsText
# ---------------------------------------------------------
        warningsUrl = "https://www.walgreens.com/store/store/prodWarnings.jsp?id=" + prodid + "&instart_disable_injection=true"
        warningsText = requests.get(url=warningsUrl).text

        warningsText = Selector(text=warningsText).xpath('//p/text()').extract()
        item['warnings'] = warningsText
# ---------------------------------------------------------
        descripUrl = "https://www.walgreens.com/store/store/prodDesc.jsp?id=" + str(prodid) + "&callFrom=dotcom&instart_disable_injection=true"
        descriptionText = requests.get(url=descripUrl).text
        descriptionText2 = ''.join(Selector(text=descriptionText).xpath('//body//text()').extract()).strip()
        result = re.sub('if.*?};','', descriptionText2, flags=re.M|re.S).replace("\n", " ")
        description = result
        item['description'] = ''.join(description).strip()

        yield item



