from scrapy.crawler import CrawlerProcess
from src.spiders import BiographySpider, InterestsSpider
from src.extractors import BiographyExtractor

def main():
    process = CrawlerProcess(settings={
        "LOG_LEVEL": "INFO",
    })
    print('running crawlers')
    process.crawl(BiographySpider)
    #process.crawl(InterestsSpider)
    process.start()
    print('finish')
    print('running extraction')
    bio_extractor = BiographyExtractor()
    bio_extractor.run()
    print('finish')

if __name__ == "__main__":
    main()