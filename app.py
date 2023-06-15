from flask import Flask, redirect, render_template, request, url_for
import os
from bs4 import BeautifulSoup as bs
import urllib.request
import ssl
from markupsafe import Markup
app = Flask(__name__)

@app.route("/")
def home():
    return redirect(url_for("watchlist"))


@app.route("/watchlist", methods=["POST", "GET"])
def watchlist():
    if request.method == "POST":  # if accessed by submitting a form
        watchlist1 = get_watchlist(request.form["username1"])
        watchlist2 = get_watchlist(request.form["username2"])
        overlap = get_overlap(watchlist1, watchlist2)
        # overlap = convert_markup(overlap)
        return render_template("watchlist.html", list=overlap)  # send to watchlist comparison page
    else:  # not accessed by posting
        # render home
        return render_template("enter_users.html")


def store_webpage(url, ctx, fn):
    req = urllib.request.Request(
        url,
        data=None,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/58.0.3029.110 Safari/537.36.'
        }
    )
    page = urllib.request.urlopen(req, context=ctx)
    soup = bs(page.read(), 'html.parser')
    f = open(fn, 'w', encoding='utf-8')
    print(soup, file=f)
    f.close()


def load_webpage(url, ctx):
    page = urllib.request.urlopen(url, context=ctx)
    return bs(page.read(), 'html.parser')


def get_soup(web_url):
    # This function returns the soup from url
    # Ignore SSL certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    file_name = 'sites/letterboxd.html'
    store_webpage(web_url, ctx, file_name)
    file_url = 'file:///' + os.path.abspath(file_name)
    soup = load_webpage(file_url, ctx)

    return soup

def get_watchlist (user):
    web_url = 'https://letterboxd.com/' + user + '/watchlist/'
    soup = get_soup(web_url)
    pages = watchlist_count(soup) // 28 + 1
    print("pages:", pages)
    watchlist = []
    for i in range(pages):
        url_with_page = web_url + 'page/' + str(i) + '/'
        soup = get_soup(url_with_page)
        films = soup.find_all('li', class_='poster-container')
        for film in films:
            tag = film.div
            print(tag)
            attributes = tag.attrs
            watchlist.append(attributes['data-film-slug'])









    return watchlist


def get_overlap(list1, list2):
    return [film for film in list1 if (film in list2)]


def convert_markup(list):
    return [Markup('<strong>' + item + '</strong>') for item in list]


def watchlist_count(soup):
    tag = soup.find('div', class_='cols-2 js-watchlist-content')
    attributes = tag.attrs
    return int(attributes['data-num-entries'])

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)