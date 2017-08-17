# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import Spider
from scrapy.http import Request
from elecciones.items import EleccionesItem
import logging, re

def num(s):
    try:
        return int(s)
    except ValueError:
        return 0

class ResultadosSpider(Spider):
    name = 'resultados'
    allowed_domains = ['resultados.gob.ar']
    start_urls = ['http://resultados.gob.ar/99/resu/content/telegramas/IPRO.htm']

    def parse(self, response):
        provincias = response.xpath('//div[@class="ulmes"]/ul/li/a')

        reqs = []

        for item in provincias:
            href = item.xpath('@href').extract()[0]
            nameparts = item.xpath('text()').extract()[0].split('-')
            num = nameparts[0].strip()
            name = nameparts[1].strip()

            logging.info("%s: %s" % (name, href))

            req = Request(url='http://resultados.gob.ar/99/resu/content/telegramas/%s' % href, callback=self.parse_provincia)
            req.meta['provincia_num'] = num
            req.meta['provincia_name'] = name
            reqs.append(req)


        return reqs

    def parse_provincia(self, response):

        secciones = response.xpath('//div[@class="ulmes"]/ul/li/a')

        reqs = []

        for item in secciones:
            href = item.xpath('@href').extract()[0]
            nameparts = item.xpath('text()').extract()[0].split('-')
            num = nameparts[0].strip()
            name = nameparts[1].strip()

            logging.info("%s: %s" % (name, href))

            req = Request(url='http://resultados.gob.ar/99/resu/content/telegramas/%s' % href, callback=self.parse_seccion)
            req.meta['provincia_num'] = response.meta['provincia_num']
            req.meta['provincia_name'] = response.meta['provincia_name']
            req.meta['seccion_num'] = num
            req.meta['seccion_name'] = name
            reqs.append(req)


        return reqs

    def parse_seccion(self, response):
        circuitos = response.xpath('//div[@class="ulmes"]/ul/li/a')

        reqs = []

        for sec in circuitos:
            href = sec.xpath('@href').extract()[0]
            nameparts = sec.xpath('text()').extract()[0].split('-')
            num = nameparts[0].strip()

            logging.info("%s: %s" % (num, href))

            req = Request(url='http://resultados.gob.ar/99/resu/content/telegramas/%s' % href, callback=self.parse_circuito)
            req.meta['provincia_num'] = response.meta['provincia_num']
            req.meta['provincia_name'] = response.meta['provincia_name']
            req.meta['seccion_num'] = response.meta['seccion_num']
            req.meta['seccion_name'] = response.meta['seccion_name']
            req.meta['circuito'] = num
            reqs.append(req)


        return reqs


    def parse_circuito(self, response):
        mesas = response.xpath('//div[@class="ulmes"]/ul/li/a')

        reqs = []

        for sec in mesas:
            href = sec.xpath('@href').extract()[0]
            nameparts = sec.xpath('text()').extract()[0].split('-')
            num = nameparts[0].strip()

            logging.info("%s: %s" % (num, href))

            req = Request(url='http://resultados.gob.ar/99/resu/content/telegramas/%s' % href, callback=self.parse_mesa)
            req.meta['provincia_num'] = response.meta['provincia_num']
            req.meta['provincia_name'] = response.meta['provincia_name']
            req.meta['seccion_num'] = response.meta['seccion_num']
            req.meta['seccion_name'] = response.meta['seccion_name']
            req.meta['circuito'] = response.meta['circuito']
            req.meta['mesa'] = num
            reqs.append(req)


        return reqs


    def parse_mesa(self, response):
        try:
            estado = response.xpath("//td[preceding-sibling::th = 'Estado']/text()").extract()[0]
        except IndexError:
            return None

        #Tipos de voto (Senadores, diputados, etc)
        types = [re.sub(' ', '_', x.lower()) for x in response.xpath("//div[@class='pt1']/table/thead/tr/th/text()").extract()]

        #Votos especiales (Nulos, impugnados, etc)
        especiales = response.xpath("//div[@class='pt1']/table/tbody/tr/td")
        ev = []
        for e in especiales:
            ev.append(num(e.xpath('text()').extract()[0].strip()))


        objNulos = {}
        objBlanco = {}
        objRecurridos = {}
        i=0
        for t in types:
            objNulos[t] = ev[i]
            i+=1
        for t in types:
            objBlanco[t] = ev[i]
            i+=1
        for t in types:
            objRecurridos[t] = ev[i]
            i+=1

        impugnados = response.xpath("//div[@class='pt2']/table/td/text()").extract()[0].strip()

        votosEspeciales  = {'blanco':objBlanco, 'nulo':objNulos, 'recurridos':objRecurridos, 'impugnados': num(impugnados)}

        votos = response.xpath("//table[@id='TVOTOS']/tbody/tr")
        votosArr = []
        for v in votos:
            if len(v.xpath('th')) > 0:
                typeV = v.xpath('th/@class').extract()[0]
                name = v.xpath('th/text()').extract()[0]
                values = [num(x) for x in v.xpath('td/text()').extract()]

                votosArr.append([typeV, name] + values)

        votosFinal = []


        currPartido = ''
        for v in votosArr:
            if v[0] == 'alaizquierda':
                currPartido = v[1]
            else:
                obj = {
                'partido': currPartido,
                'lista': v[1]
                }

                i = 2
                for ty in types:
                    obj[ty] = v[i]
                    i+=1

                votosFinal.append(obj)

        #try:
        #    urlbase=response.url.rsplit('/',1)[0]
        #    pdf=response.xpath("//iframe[@id='caja_pdf']/@src").extract()[0]
        #    yield Request(
        #        url='%s/%s' % (urlbase, pdf),
        #        callback=self.save_pdf
        #    )
        #except Exception:
        #    print('Failed to download pdf')

        res = EleccionesItem()
        res['url'] = response.url
        res['estado'] = estado,
        res['provincia_num'] = response.meta['provincia_num']
        res['provincia_name'] = response.meta['provincia_name']
        res['seccion_num'] = response.meta['seccion_num']
        res['seccion_name'] = response.meta['seccion_name']
        res['circuito'] = response.meta['circuito']
        res['mesa'] = response.meta['mesa']
        res['especiales'] = votosEspeciales
        res['votos'] = votosFinal

        return res


    def save_pdf(self, response):
        path = response.url.split('/')[-1]
        self.logger.info('Saving PDF %s', path)
        with open('pdf/%s' % path, 'wb') as f:
            f.write(response.body)
