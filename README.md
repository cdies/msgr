<h1>Парсер для www.msgr.ru (МосСоцГарантия)</h1>
<p>&nbsp;</p>
<p>Описание:</p>
<p>https://habr.com/ru/post/487370/</p>
<p>&nbsp;</p>
<p>Зависимости:</p>
<p>Anaconda python 3, scrapy, yfinance, openpyxl, requests, numpy, pandas, tqdm</p>
<p>&nbsp;</p>
<p>1. Запуск парсера: <b>python3 msgr_parser.py</b></p>
<p>2. Формирование отчёта и координат для Yandex карт: <b>python3 report.py</b></p>
<p>&nbsp;</p>

***

<p>Если нужна карта:</p>
<p>1. Необходимо ваш yandex api ключ записать в файл <b>yandex.key.txt</b> (https://yandex.ru/blog/mapsapi/novye-pravila-dostupa-k-api-kart)</p>
<p>2. Раскомментировать соответствующий код в <b>report.py</b> в самом конце, где вызывается функция <code>make_yandex_map(auctions, past_auctions)</code></p>
<p>3. Координаты после выполнения <b>report.py</b> находятся в файле <b>yandex.map.csv</b>, их нужно загрузить на https://yandex.ru/map-constructor/</p>

<p>&nbsp;</p>

***

<p>Гистограммы находятся в файле <b>statistics.ipynb</b></p>
<p>&nbsp;</p>


<br/><br/>
---
[![](https://habrastorage.org/webt/gz/gc/i6/gzgci6pivvdnk-gmj-kepml5q9y.gif)](https://yoomoney.ru/to/4100117863420642)
