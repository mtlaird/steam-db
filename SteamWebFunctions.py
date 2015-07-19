from bs4 import BeautifulSoup
import requests


def get_tags(dom):
    tags = dom.find(class_='popular_tags')
    tags_array = tags.text.replace('\t', '').replace('\n', '').replace('+', '').split('\r')
    return tags_array


def get_categories(dom):
    cats_div = dom.find(id='category_block')
    cats_soup = BeautifulSoup(str(cats_div))
    cats = cats_soup.find_all(class_='name')
    cats_array = []
    for c in cats:
        cats_array.append(c.text)
    return cats_array


def get_appname(dom):
    name = dom.find(class_='apphub_AppName')
    return name.text


def get_releasedate(dom):
    res = dom.find_all(class_='release_date')
    date = res[1]
    date = date.text.replace('Release Date: ', '').replace('\t', '').replace('\n', '').replace('\r', '')
    return date


def get_metascore(dom):
    score = dom.find(id='game_area_metascore')
    return score.text.replace('\n', '').replace('\r', '')


def get_review_summary(dom):
    quick_summary = dom.find(class_='game_review_summary')
    aggregate_review_div = dom.find('div',{'itemprop':'aggregateRating'})
    full_summary = aggregate_review_div['data-store-tooltip']
    return [quick_summary.text, full_summary]

def get_html_dom(app_id):
    r = requests.get("http://store.steampowered.com/app/%s/" % app_id)
    dom = BeautifulSoup(r.text)
    return dom


def get_app_info(app_id):
    dom = get_html_dom(app_id)
    appname = get_appname(dom)
    print appname
    releasedate = get_releasedate(dom)
    print releasedate
    metascore = get_metascore(dom)
    print metascore
    review_summary = get_review_summary(dom)
    print review_summary
    categories = get_categories(dom)
    print categories
    user_tags = get_tags(dom)
    print user_tags


def get_owned_games():
    api_key = '67A9B0DDDABA23B76FE8976FC14D0BBC'
    steamid = '76561198024767219'
    url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/'
    params = 'key=%s&steamid=%s&format=json' % (api_key, steamid)
    r = requests.get('%s?%s' % (url, params))
    return r.json()
