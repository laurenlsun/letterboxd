from flask import Flask, redirect, render_template, request, url_for, session, flash, get_flashed_messages
import os
from bs4 import BeautifulSoup as bs
import urllib.request
import ssl
from markupsafe import Markup


app = Flask(__name__)

# TODO: optimize with comprehensions

@app.route("/")
def home():
    """
    Default landing page.
    :return: redirects to num_users, sending options 2-5 for number of users to compare
    num_users
    """
    return render_template("num_users.html", options=list(range(2,6)))

@app.route("/enter_users", methods=["POST"])
def enter_users():
    """
    takes input from form action="/enter_users" in num_users.html
    :return: render enter_users.html page for user with correct number of text boxes
    """
    if request.method == "POST":
        '''
        Must be accessed by submitting a number of users
        Retrieve num_users from dropdown in num_users.html, make an iterable of that length,
        send to enter_users.html's for loop
        '''
        session['num_users'] = int(request.form['num_users'])
        return render_template("enter_users.html", num=list(range(session['num_users'])))
    else:
        # redirect to entering number first
        return render_template("num_users.html", options=list(range(2,6)))


@app.route("/watchlist", methods=["POST", "GET"])
def watchlist():
    """
    retrieves usernames from form action="/watchlist" in enter_users.html
    scrapes watchlists for each user
    finds overlap from all watchlists
    :return: send overlap to display
    """
    print()
    if request.method == "POST":  # if accessed by submitting a form
        usernames = [request.form['username' + str(i)] for i in range(session['num_users'])]
        if "" in usernames:  # if blank entry
            flash("Please fill all " + str(session['num_users']) + " blanks.")
            return render_template("enter_users.html", num=list(range(session['num_users'])))
        else:
            watchlists = [get_watchlist(username) for username in usernames]  # list of lists of tuples
            overlap = get_overlap(watchlists) # a list of tuples
            # overlap = convert_markup(overlap)
            return render_template("watchlist.html", films=overlap)  # send to watchlist comparison page
    else:  # not accessed by posting
        # render home
        return render_template("num_users.html", options=list(range(2,6)))


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
    """
    :param user: username
    :return: list of tuple (url-film-name, Full Film Name)
    """
    web_url = 'https://letterboxd.com/' + user + '/watchlist/'
    soup = get_soup(web_url)
    pages = watchlist_count(soup) // 28 + 1
    watchlist = []
    for i in range(pages):
        url_with_page = web_url + 'page/' + str(i) + '/'
        soup = get_soup(url_with_page)
        films = soup.find_all('li', class_='poster-container')
        watchlist.extend([(film.div.attrs['data-film-slug'], film.img.attrs['alt']) for film in films])
    return watchlist


def get_overlap(watchlists):
    """
    finds films that are in all watchlists
    :param watchlists: is a list of lists of tuples
    :return: overlap, a list
    """
    overlap = []
    print(watchlists[0])
    for filmtuple in watchlists[0]:  # take films in first watchlist
        in_all = 0  # dummy var assume the film is in all the other lists
        for watchlist in watchlists:
            if filmtuple not in watchlist:
                in_all += 1  # increments if one of the lists is missing this film
        if in_all == 0:  # no increments = film is in all lists
            if filmtuple not in overlap:
                overlap.append(filmtuple)
                print(filmtuple)
    return overlap


def convert_markup(list):
    return [Markup('<strong>' + item + '</strong>') for item in list]


def watchlist_count(soup):
    tag = soup.find('div', class_='cols-2 js-watchlist-content')
    attributes = tag.attrs
    return int(attributes['data-num-entries'])

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)
