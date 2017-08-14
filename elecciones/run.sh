#!/bin/bash
rm /tmp/resultados.json 2>/dev/null
mkdir out 2>/dev/null
scrapy crawl resultados
now=`date +"%m_%d_%YT%H_%M"`
cp /tmp/resultados.json ./out/resultados_$now.json
