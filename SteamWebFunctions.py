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
    rdate = dom.find(class_='release_date')
    date = rdate.text.replace('Release Date: ', '').replace('\t', '').replace('\n', '').replace('\r', '')
    return date


def get_metascore(dom):
    score = dom.find(id='game_area_metascore')
    try:
        return score.text.replace('\n', '').replace('\r', '')
    except AttributeError:
        return None


# This will need to be fixed to accommodate recent reviews
def get_review_summary(dom):
    quick_summary = dom.find(class_='game_review_summary')
    aggregate_review_div = dom.find('div', {'itemprop':'aggregateRating'})
    full_summary = aggregate_review_div['data-store-tooltip']
    return [quick_summary.text, full_summary]


def get_details(dom):

    def clean_array(a):
        new_array = []
        for e in a:
            if e != '':
                new_array.append(e.strip())
        return new_array
    details_block = dom.find(class_="details_block")
    dbt = details_block.text.replace('\r', '').replace('\t', '')
    sdbt = dbt.replace('\n', ',').replace(':', ',').split(',')
    genres, developer, publisher = [], [], []
    for e in sdbt:
        if e == 'Genre':
            genres = sdbt[sdbt.index('Genre')+1:sdbt.index('Developer')]
        if e == 'Developer':
            developer = sdbt[sdbt.index('Developer')+1:sdbt.index('Publisher')]
        if e == 'Publisher':
            publisher = sdbt[sdbt.index('Publisher')+1:sdbt.index('Release Date')]

    return clean_array(genres), clean_array(developer), clean_array(publisher)


def get_game_description_snippet(dom):
    gds = dom.find(class_="game_description_snippet")
    try:
        return gds.text.strip()
    except AttributeError:
        return None


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
    genres, developer, publisher = get_details(dom)
    print genres
    print developer
    print publisher
    game_desc = get_game_description_snippet(dom)
    print game_desc


def get_owned_games():
    with open('steamApiKey') as f_api:
        api_key = f_api.read()
    with open('steamID') as f_id:
        steamid = f_id.read()
    url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/'
    params = 'key=%s&steamid=%s&format=json' % (api_key, steamid)
    r = requests.get('%s?%s' % (url, params))
    return r.json()
