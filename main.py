from scrapy.crawler import CrawlerProcess
from src.spiders import BiographySpider, InterestsSpider
from src.extractors import BiographyExtractor
"""
process = CrawlerProcess(settings={
        "LOG_LEVEL": "INFO",
    })
process.crawl(BiographySpider)
process.crawl(InterestsSpider)
process.start()
"""
bio_extractor = BiographyExtractor()
bio_extractor.run()