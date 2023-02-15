import scrapy
import re
from scrapy.exceptions import CloseSpider
from covid_19.no_accents import no_accent_vietnamese


class NewCaseSpider(scrapy.Spider):
    name = 'new_case'
    allowed_domains = ['web.archive.org']
    start_urls = ['https://web.archive.org/web/20210907023426/https://ncov.moh.gov.vn/vi/web/guest/dong-thoi-gian']

    def parse(self, response):
        if response.status == 404:
            raise CloseSpider("Reached last page...")

        #Get all detail follow day
        details = response.xpath("//div[@class='timeline-detail']")

        #Pattern to use regex to extract needed data from post
        reg_new_case = "([0-9]+) CA MAC MOI"
        reg_case_city = " ([a-zA-Z ]+ \([0-9]+\))"

        for detail in details:
            time = detail.xpath(".//div/h3/text()").get()
            new_case = detail.xpath(".//div[@class='timeline-content']/p[2]/text()").get()
            case_city = detail.xpath("./div[@class='timeline-content']/p[3]").get()
            #New_case process
            if new_case == None: #Remove record has no new case
                continue
            new_case = new_case.replace(".", "")
            new_case = no_accent_vietnamese(new_case) #Remove accents
            if len(re.findall(reg_new_case, new_case)) == 0: #Remove record has no new case
                continue
            new_case = re.findall(reg_new_case, new_case)[0]

            #Case_city process
            lst_case_city=[]
            if case_city != None: 
                case_city = no_accent_vietnamese(case_city)#Remove accents
                case_city = case_city.replace(".", "")
                case_city = case_city.replace("tai", "tai:")#To using regex more efficient after string "trong nuoc tai TP Ho CHi Minh" I add character ":" to make it "trong nuoc tai: TP Ho CHi Minh"
                lst_case_city = re.findall(reg_case_city, case_city)#Find all pair has format:" city (new_case)""
        
            for ix in range(len(lst_case_city)):
                #Convert format from " city (new_case)" to {"city": city, "new_case": new_case}
                lst_case_city[ix] = {
                    "city": re.findall("([a-zA-Z ]+) ", lst_case_city[ix])[0],#Da Nang
                    "case": int(re.findall("\(([0-9]+)\)*", lst_case_city[ix])[0])#4802
                }

            yield {
                "time": time,
                "new_case": int(new_case),
                "case_city": lst_case_city
            }
        
        link_next = response.xpath("//ul[@class='lfr-pagination-buttons pager']/li[2]/a/@href").get()
        yield scrapy.Request(
            url=link_next,
            callback=self.parse
        )
