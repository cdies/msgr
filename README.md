<h1>Парсер для www.msgr.ru (МосСоцГарантия)</h1>
<p>&nbsp;</p>
<p>Описание:</p>
<p>https://habr.com/ru/post/487370/</p>
<p>&nbsp;</p>
<p>Зависимости:</p>
<p>Anaconda python 3, scrapy, yfinance, openpyxl, requests, numpy, pandas, tqdm</p>
<p>&nbsp;</p>
<p>1 Запуск парсера: <b>python3 msgr_parser.py</b></p>
<p>2 Формирование отчёта и координат для Yandex карт: <b>python3 report.py</b></p>
<p>&nbsp;</p>
<p>Для работы report.py необходимо ваш yandex api ключ записать в файл yandex.key.txt (https://yandex.ru/blog/mapsapi/novye-pravila-dostupa-k-api-kart)</p>
<p>&nbsp;</p>
<p>Координаты после выполнения report.py находятся в файле yandex.map.csv, их нужно загрузить на https://yandex.ru/map-constructor/</p>
<p>&nbsp;</p>
<p>Гистограммы находятся в файле statistics.ipynb</p>
<p>&nbsp;</p>


