import feedparser
import json
import datetime
import requests
from flask import Flask
from flask import render_template
from flask import request
from flask import make_response

app = Flask(__name__)

DEFAULTS = {'publication': 'bbc',
            'city': 'London,UK',
            'currency_from': 'GBP',
            'currency_to': 'USD'}

RSS_FEEDS = {'bbc': 'http://feeds.bbci.co.uk/news/rss.xml',
             'cnn': 'http://rss.cnn.com/rss/edition.rss',
             'fox': 'http://feeds.foxnews.com/foxnews/latest',
             'iol': 'http://www.iol.co.za/cmlink/1.640'}

URLS = {'weather': 'http://api.openweathermap.org/data/2.5/weather',
        'exchange': 'https://openexchangerates.org/api/latest.json'}

API_KEYS = {'weather': '41ca473e753cff7224bf1e764d858784',
            'exchange': '2ce8941af50648cf9452c3e630163920'}

@app.route('/', methods=['GET', 'POST'])
def home():
    publication = get_value_with_fallback('publication')
    articles = get_news(publication)
    city = get_value_with_fallback('city')
    weather = get_weather(city)
    currency_from = get_value_with_fallback('currency_from')
    currency_to = get_value_with_fallback('currency_to')
    rate, currencies = get_rate(currency_from, currency_to)
    response = make_response(render_template("home.html",
                                             articles=articles,
                                             weather=weather,
                                             currency_from=currency_from,
                                             currency_to=currency_to,
                                             rate=rate,
                                             currencies=sorted(currencies)))
    expires = datetime.datetime.now() + datetime.timedelta(days=365)
    response.set_cookie("publication", publication, expires=expires)
    response.set_cookie("city", city, expires=expires)
    response.set_cookie("currency_from", currency_from, expires=expires)
    response.set_cookie("currency_to", currency_to, expires=expires)
    return response

def get_value_with_fallback(key):
    if request.args.get(key):
        return request.args.get(key)
    elif request.form.get(key):
        return request.form.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)
    return DEFAULTS[key]

def get_news(query):
    if not query or query.lower() not in RSS_FEEDS:
        publication = DEFAULTS["publication"]
    else:
        publication = query.lower()
    feed = feedparser.parse(RSS_FEEDS[publication])
    return feed['entries']

def get_weather(query):
    payload = { "q": query, "units": "metric", "appid": API_KEYS['weather'] }
    response = requests.get(URLS['weather'], params=payload)
    parsed = json.loads(response.content)
    weather = None
    if parsed.get("weather"):
        weather = {"description": parsed["weather"][0]["description"],
                   "temperature": parsed["main"]["temp"],
                   "city": parsed["name"],
                   "country": parsed["sys"]["country"]
                   }
    return weather

def get_rate(frm, to):
    payload = { 'app_id': API_KEYS['exchange'] }
    all_currency = requests.get(URLS['exchange'], params=payload)

    parsed = json.loads(all_currency.content).get('rates')
    frm_rate = parsed.get(frm.upper())
    to_rate = parsed.get(to.upper())
    return to_rate/frm_rate, parsed.keys()

if __name__ == '__main__':
    app.run()
