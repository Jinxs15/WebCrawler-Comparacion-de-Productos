import scrapy
from scrapy.crawler import CrawlerProcess
import pandas as pd

class ProductSpider(scrapy.Spider):
    name = 'product_spider'
    parsed_data = []

    def start_requests(self):

        product_name = input("Ingrese el nombre del producto: ")

        mercado_libre_url = f'https://listado.mercadolibre.com.mx/{product_name.replace(" ", "-")}'
        amazon_url = f'https://www.amazon.com.mx/s?k={product_name.replace(" ", "+")}'
        soriana_url = f'https://www.soriana.com/buscar?q={product_name.replace(" ", "+")}'
        walmart_url = f'https://www.walmart.com.mx/search?q={product_name.replace(" ", "+")}'
        aurrera_url = f'https://www.bodegaaurrera.com.mx/search?q=switch{product_name.replace(" ", "+")}'

        # Hacemos solicitudes a las URLs
        yield scrapy.Request(url=mercado_libre_url, callback=self.parse_mercado_libre, meta={'product_name': product_name})
        yield scrapy.Request(url=amazon_url, callback=self.parse_amazon, meta={'product_name': product_name}, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})
        yield scrapy.Request(url=soriana_url, callback=self.parse_soriana, meta={'product_name': product_name})
        yield scrapy.Request(url=walmart_url, callback=self.parse_walmart, meta={'product_name': product_name}, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})
        yield scrapy.Request(url=aurrera_url, callback=self.parse_aurrera, meta={'product_name': product_name}, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})
    def parse_mercado_libre(self, response):
        product_name = response.meta['product_name']
        items = []

        products = response.css('.ui-search-layout__item')
        for product in products:
            name = product.css('.ui-search-item__title::text').get()
            price = product.css('.andes-money-amount__fraction::text').get()
            link = product.css('.ui-search-link::attr(href)').get()

            if name and price and link:
                items.append({
                    'Recurso': 'MercadoLibre',
                    'Nombre': name.strip(),
                    'Precio': price.strip(),
                    'Link': link,
                })
            if len(items) == 10:
                break

        self.parsed_data.extend(items)

    def parse_amazon(self, response):
        product_name = response.meta['product_name']
        items = []

        # Extraemos la información de Amazon
        for index, product in enumerate(response.css('.s-result-item')):
            name = product.css('.a-size-base-plus::text').get() or product.css('.a-text-normal::text').get()
            price = product.css('.a-price > .a-offscreen::text').get()
            link = product.css('.a-link-normal::attr(href)').get()

            if name and price and link:
                items.append({
                    'Recurso': 'Amazon',
                    'Nombre': name.strip(),
                    'Precio': price.strip(),
                    'Link': 'https://www.amazon.com.mx'+ link,
                })

            if len(items) == 10:
                break

        self.parsed_data.extend(items)

    def parse_soriana(self, response):
        product_name = response.meta['product_name']
        items = []

        products = response.css('div.product-tile')  # Ajusta el selector a la clase que contiene cada producto

        for product in products:
            name = product.css('a.font-primary--medium::text').get()  # Selector para el nombre del producto
            price = product.css('span.cart-price span::text').get()
            link = product.css('a.font-primary--medium::attr(href)').get()  # Selector para el enlace del producto

            if name and price and link:
                items.append({
                    'Recurso': 'soriana',
                    'Nombre': name.strip(),
                    'Precio': price.strip(),
                    'Link': response.urljoin(link),  # Para obtener el enlace completo
                })

            # Limitamos a 10 productos
            if len(items) == 10:
                break

        self.parsed_data.extend(items)

    def parse_walmart(self, response):
        items = []

        products = response.xpath('//a[@link-identifier and @class="absolute w-100 h-100 z-1 hide-sibling-opacity"]')

        for product in products:
            name = product.xpath('.//span[@class="w_q67L"]/text()').get()
            price = product.xpath('following::div[@aria-hidden="true"]/text()').get()
            link = product.xpath('./@href').get()

            if name and price and link:
                items.append({
                    'Recurso': 'Walmart',
                    'Nombre': name.strip(),
                    'Precio': price.strip(),
                    'Link': response.urljoin(link),  # Para obtener el enlace completo
                })

            if len(items) == 10:
                break

        self.parsed_data.extend(items)

    def parse_aurrera(self, response):
        items = []

        products = response.xpath('//a[@link-identifier and @class="absolute w-100 h-100 z-1 hide-sibling-opacity"]')

        for product in products:
            name = product.xpath('.//span[@class="w_q67L"]/text()').get()
            price = product.xpath('following::div[@class="mr1 mr2-xl b black lh-copy f5 f4-l" and @aria-hidden="true"]/text()').get()
            link = product.xpath('./@href').get()

            if name and price and link:
                items.append({
                    'Recurso': 'Aurrera',
                    'Nombre': name.strip(),
                    'Precio': price.strip(),
                    'Link': response.urljoin(link),
                })

            if len(items) == 10:
                break

        self.parsed_data.extend(items)

process = CrawlerProcess(settings={
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
    'DOWNLOAD_DELAY': 2,
    'DOWNLOADER_MIDDLEWARES': {
        'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 1,
    },
})


process.crawl(ProductSpider)
process.start()

data = pd.DataFrame(ProductSpider.parsed_data)

data.to_excel('productos_comparados.xlsx', index=False)
