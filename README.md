Scraper de las elecciones 2017, sobre los resultados en http://resultados.gob.ar

Para correrlo, hay que instalar un entorno de python3 en virtualenv:
(Instrucciones validas en Linux)

```
git clone git@github.com:sicarul/resultados_elecciones2017_scraper.git
cd resultados_elecciones2017_scraper
virtualenv -p python3 .
. bin/activate
pip install -r requirements.txt
cd elecciones
./run.sh
```

Asi, va a generar en elecciones/out/, un archivo con los resultados scrapeados en esa corrida.
