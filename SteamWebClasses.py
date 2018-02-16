import json
from collections import defaultdict
from bs4 import BeautifulSoup
import requests


class AppNotOnSteamError(Exception):
    def __init__(self):
        Exception.__init__(self, "This app is no longer on the Steam store.")


class AppRequiresAgeCheckError(Exception):
    def __init__(self):
        Exception.__init__(self, "This app requires an age check to access on the Steam store.")


class AppNotFoundError(Exception):
    def __init__(self):
        Exception.__init__(self, "This app could not be found.")


class AppAgeCheckFailedError(Exception):
    def __init__(self):
        Exception.__init__(self, "Steam store age check was not successful.")


class AppInitializationFailedError(Exception):
    def __init__(self):
        Exception.__init__(self, "App ID could not be determined, so app could not be initialized.")


class DomNotSetError(Exception):
    def __init(self):
        Exception.__init__(self, "The dom was not set or could not be parsed.")


class SteamAppBase:
    def __init__(self, app_id=None, search_term=None):
        self.app_id = app_id
        self.search_term = search_term

    def get_app_id_from_search_term(self):

        r = requests.get('http://store.steampowered.com/search/?term={}'.format(self.search_term))
        search_dom = BeautifulSoup(r.text, 'lxml')
        app_id = search_dom.find(id='search_result_container').find('a').attrs['href'].split('/')[4]
        if not self.app_id:
            self.app_id = app_id
        return app_id

    def initialize(self):

        if not self.app_id and self.search_term:
            self.get_app_id_from_search_term()
        if not self.app_id:
            raise AppInitializationFailedError


class SteamAppInfo(SteamAppBase):
    def __init__(self, app_id=None, search_term=None, domtype='both'):
        SteamAppBase.__init__(self, app_id, search_term)
        self.steam_dom = None
        self.steamdb_dom = None
        self.domtype = domtype
        self.app_info = None

    @staticmethod
    def clean_array(a):
        new_array = []
        if not a:
            return new_array
        for e in a:
            if e != '':
                new_array.append(e.strip())
        return new_array

    def get_basic_steamstore_app_dom(self):
        r = requests.get("http://store.steampowered.com/app/{}/".format(self.app_id))
        if 'app' not in r.url:
            raise AppNotOnSteamError
        elif 'agecheck' in r.url:
            raise AppRequiresAgeCheckError
        self.steam_dom = BeautifulSoup(r.text, "html.parser")

    def get_agecheck_steamstore_app_dom(self):
        s = requests.session()
        s.get("http://store.steampowered.com/agecheck/app/{}/".format(self.app_id))
        form_data = {'snr': '1_agecheck_agecheck__age-gate', 'ageDay': '1', 'ageMonth': 'April', 'ageYear': '1980'}
        rpost = s.post("http://store.steampowered.com/agecheck/app/{}/".format(self.app_id), data=form_data)
        if rpost.url == "http://store.steampowered.com/app/{}/".format(self.app_id):
            self.steam_dom = BeautifulSoup(rpost.text, "html.parser")
        else:
            raise AppAgeCheckFailedError

    def get_steamdb_app_dom(self):
        r = requests.get("https://steamdb.info/app/{}/info/".format(self.app_id))
        if r.status_code == 404:
            raise AppNotFoundError
        self.steamdb_dom = BeautifulSoup(r.text, "lxml")

    def get_tags(self):
        tags = self.steam_dom.find(class_='popular_tags')
        tags_array = tags.text.replace('\t', '').replace('\n', '').replace('+', '').split('\r')
        return self.clean_array(tags_array)

    def get_categories(self):
        cats_div = self.steam_dom.find(id='category_block')
        cats_soup = BeautifulSoup(str(cats_div), 'lxml')
        cats = cats_soup.find_all(class_='name')
        cats_array = []
        for c in cats:
            cats_array.append(c.text)
        return cats_array

    def get_appname(self):
        if self.domtype == 'basic':
            name = self.steam_dom.find(class_='apphub_AppName')
        elif self.domtype == 'steamdb':
            name = self.steamdb_dom.find(attrs={'itemprop': 'name'})
        else:
            return None
        return name.text

    def get_releasedate(self):
        rdate = self.steam_dom.find(class_='release_date')
        date = rdate.text.replace('Release Date: ', '').replace('\t', '').replace('\n', '').replace('\r', '')
        return date

    def get_metascore(self):
        score = self.steam_dom.find(id='game_area_metascore')
        try:
            score_text = score.text
        except AttributeError:
            return None

        return [int(s) for s in score_text.split() if s.isdigit()][0]

    def get_review_summary(self):
        quick_summary = self.steam_dom.find(class_='game_review_summary')
        review_divs = self.steam_dom.find_all(class_='user_reviews_summary_row')
        recent_summary, full_summary = None, None
        for rd in review_divs:
            if not full_summary or not recent_summary:
                if 'in the last 30 days' in rd['data-store-tooltip']:
                    recent_summary = rd['data-store-tooltip']
                else:
                    full_summary = rd['data-store-tooltip']
        return [quick_summary.text, full_summary, recent_summary]

    def get_details(self):

        details_block = self.steam_dom.find(class_="details_block")
        dbt = details_block.text.replace('\r', '').replace('\t', '')
        sdbt = dbt.replace('\n', ',').replace(':', ',').split(',')
        genres, developer, publisher = [], [], []
        for e in sdbt:
            if e == 'Genre':
                try:
                    genres = sdbt[sdbt.index('Genre') + 1:sdbt.index('Developer')]
                except ValueError:
                    pass
            if e == 'Developer':
                try:
                    developer = sdbt[sdbt.index('Developer') + 1:sdbt.index('Publisher')]
                except ValueError:
                    pass
            if e == 'Publisher':
                try:
                    publisher = sdbt[sdbt.index('Publisher') + 1:sdbt.index('Release Date')]
                except ValueError:
                    pass

        return self.clean_array(genres), self.clean_array(developer), self.clean_array(publisher)

    def get_steamdb_details(self):

        try:
            developer = self.steamdb_dom.find(attrs={"itemprop": "author"}).text.split(",")
        except AttributeError:
            developer = None
        try:
            publisher = self.steamdb_dom.find(attrs={"itemprop": "publisher"}).text.split(",")
        except AttributeError:
            publisher = None

        return self.clean_array(developer), self.clean_array(publisher)

    def get_steamdb_historical_low_price(self):

        hist_low_details = {}
        hist_low_td = self.steamdb_dom.find('td', attrs={'data-cc': 'us'}).parent.find_all('td')[-1]
        hist_low_details['date'] = hist_low_td.attrs['title']
        hist_low_details['price'] = hist_low_td.text.split()[0]
        hist_low_details['discount'] = hist_low_td.text.split()[-1]

        return hist_low_details

    def get_game_description_snippet(self):
        gds = self.steam_dom.find(class_="game_description_snippet")
        try:
            return gds.text.strip()
        except AttributeError:
            return None

    def get_app_info_from_dom(self):
        if not self.steam_dom and not self.steamdb_dom:
            raise DomNotSetError
        if self.steam_dom:
            genres, developer, publisher = self.get_details()
            self.app_info = {'app_name': self.get_appname(), 'release_date': self.get_releasedate(),
                             'metascore': self.get_metascore(), 'review_summary': self.get_review_summary(),
                             'categories': self.get_categories(), 'user_tags': self.get_tags(),
                             'genres': genres, 'developer': developer,
                             'publisher': publisher, 'game_desc': self.get_game_description_snippet()}
        if self.steamdb_dom:
            developer, publisher = self.get_steamdb_details()
            historical_low_price = self.get_steamdb_historical_low_price()
            if not self.app_info:
                self.app_info = {'app_name': self.get_appname(), 'developer': developer, 'publisher': publisher,
                                 'release_date': None, 'metascore': None, 'review_summary': None, 'categories': None,
                                 'user_tags': None, 'genres': None, 'game_desc': None}
            self.app_info['historical_low_price'] = historical_low_price

    def print_app_info(self):
        if not self.app_info:
            return False
        print self.app_info['app_name']
        print self.app_info['developer']
        print self.app_info['publisher']
        if self.domtype == 'basic':
            print self.app_info['release_date']
            print self.app_info['metascore']
            print self.app_info['review_summary']
            print self.app_info['categories']
            print self.app_info['user_tags']
            print self.app_info['genres']
            print self.app_info['game_desc']

    def get_app_dom(self):
        if not self.domtype:
            self.domtype = 'both'
        if self.domtype != 'steamdb' and not self.steam_dom:
            try:
                self.get_basic_steamstore_app_dom()
            except AppNotOnSteamError:
                self.domtype = 'steamdb'
                try:
                    self.get_steamdb_app_dom()
                except AppNotFoundError:
                    self.domtype = None
            except AppRequiresAgeCheckError:
                try:
                    self.get_agecheck_steamstore_app_dom()
                except AppAgeCheckFailedError:
                    self.domtype = None
        if self.domtype != 'basic' and not self.steamdb_dom:
            self.get_steamdb_app_dom()

    def initialize(self):

        if not self.app_id and self.search_term:
            self.get_app_id_from_search_term()
        if not self.app_id:
            raise AppInitializationFailedError

        self.get_app_dom()
        self.get_app_info_from_dom()


class SteamAppGlobalAchievements(SteamAppBase):
    def __init__(self, app_id=None, search_term=None):
        SteamAppBase.__init__(self, app_id, search_term)
        self.dom = None
        self.achievements = []

    def get_achievements_dom(self):
        r = requests.get("http://steamcommunity.com/stats/{}/achievements/".format(self.app_id))
        self.dom = BeautifulSoup(r.text, "html.parser")

    def get_achievements_from_dom(self):
        if not self.dom:
            raise DomNotSetError
        achievetextdivs = self.dom.find_all(class_="achieveTxtHolder")
        for d in achievetextdivs:
            a = {'Primary Text': d.find(class_="achieveTxt").find('h3').text}
            stext = d.find(class_="achieveTxt").find('h5').text
            if stext:
                a['Secondary Text'] = stext
            a['Percent'] = d.find(class_="achievePercent").text
            self.achievements.append(a)

    def initialize(self):

        if not self.app_id and self.search_term:
            self.get_app_id_from_search_term()
        if not self.app_id:
            raise AppInitializationFailedError

        self.get_achievements_dom()
        self.get_achievements_from_dom()


class SteamAppUserAchievements(SteamAppBase):
    def __init__(self, user_id, app_id=None, search_term=None):
        SteamAppBase.__init__(self, app_id, search_term)
        self.user_id = user_id
        self.dom = None
        self.unlocked_achievements = []
        self.locked_achievements = []

    def get_user_achievements_dom(self):
        r = requests.get("http://steamcommunity.com/profiles/{}/stats/{}/achievements/".format(self.user_id,
                                                                                               self.app_id))
        self.dom = BeautifulSoup(r.text, "html.parser")

    def get_user_achievments_from_dom(self):
        if not self.dom:
            raise DomNotSetError
        achievetextdivs = self.dom.find_all(class_="achieveTxt")
        for d in achievetextdivs:
            a = {'Primary Text': d.find('h3').text}
            stext = d.find('h5').text
            if stext:
                a['Secondary Text'] = stext
            a['Unlock Time'] = d.find(class_="achieveUnlockTime")
            if not a['Unlock Time']:
                a.pop('Unlock Time')
                self.locked_achievements.append(a)
            else:
                a['Unlock Time'] = a['Unlock Time'].text.strip().replace('Unlocked ', '')
                self.unlocked_achievements.append(a)

    def initialize(self):

        if not self.app_id and self.search_term:
            self.get_app_id_from_search_term()
        if not self.app_id:
            raise AppInitializationFailedError

        self.get_user_achievements_dom()
        self.get_user_achievments_from_dom()


class SteamWishList:
    def __init__(self, user_id, initialize=True):

        self.user_id = user_id
        self.dom = None
        self.wishlistgames = []
        self.apps = None
        self.appinfo = None
        if initialize:
            self.initialize()

    def get_wishlist_dom(self):
        r = requests.get('http://steamcommunity.com/profiles/{}/wishlist/'.format(self.user_id))
        self.dom = BeautifulSoup(r.text, "html.parser")

    # Old dom parsing method, now obsolete
    # def parse_dom(self):
    #
    #     for wlr in self.dom.find_all('div', class_='wishlistRow'):
    #         wlrdef = {'title': wlr.find('h4').text,
    #                   'added_on': wlr.find('div', class_='wishlist_added_on').text.strip().strip('Added on '),
    #                   'url': wlr.find('a', class_='storepage_btn_alt')['href'],
    #                   'id': wlr.find('a', class_='storepage_btn_alt')['href'].split('/')[-1]}
    #         try:
    #             wlrdef['full_price'] = wlr.find('div', class_='price').text.strip()
    #             wlrdef['discount_price'] = None
    #             wlrdef['discount_percent'] = None
    #             wlrdef['discounted'] = False
    #         except AttributeError:
    #             try:
    #                 wlrdef['full_price'] = wlr.find('div', class_='discount_original_price').text.strip()
    #                 wlrdef['discount_price'] = wlr.find('div', class_='discount_final_price').text.strip()
    #                 wlrdef['discount_percent'] = wlr.find('div', class_='discount_pct').text.strip()
    #                 wlrdef['discounted'] = True
    #             except AttributeError:
    #                 wlrdef['errors'] = 'Could not determine price.'
    #         self.wishlistgames.append(wlrdef)

    def parse_dom(self):

        varstr = None
        scripts = self.dom.find_all('script')

        for script in scripts:
            if 'var g_rgWishlistData =' not in script.text:
                continue
            varstr = script.text
        if not varstr:
            return
        apps = json.loads(varstr[varstr.index('['):varstr.index(';')])
        self.apps = apps
        varstr = varstr[varstr.index(';') + 1:]
        appinfo = json.loads(varstr[varstr.index('{'):varstr.index('};') + 1])
        self.appinfo = appinfo
        # return
        for app in apps:

            app_id = str(app['appid'])
            wlgame = {'id': app_id}

            if wlgame['id'] not in appinfo:
                continue
            wlgame['title'] = appinfo[wlgame['id']]['name']
            wlgame['added_on'] = app['added']
            wlgame['url'] = 'http://store.steampowered.com/app/{}/'.format(wlgame['id'])
            try:
                if appinfo[wlgame['id']]['subs'][0]['discount_pct'] == 0:
                    wlgame['discounted'] = False
                    wlgame['discount_price'] = None
                    wlgame['discount_percent'] = None
                    wlgame['full_price'] = appinfo[wlgame['id']]['subs'][0]['price']
                else:
                    parsed_discount_block = BeautifulSoup(appinfo[wlgame['id']]['subs'][0]['discount_block'],
                                                          "html.parser")
                    wlgame['discounted'] = True
                    wlgame['discount_price'] = '${:,.2f}'.format(appinfo[wlgame['id']]['subs'][0]['price'] / 100.0)
                    wlgame['discount_percent'] = '-%' + str(appinfo[wlgame['id']]['subs'][0]['discount_pct'])
                    wlgame['full_price'] = parsed_discount_block.find('div', class_='discount_original_price').text
            except IndexError:
                wlgame['errors'] = 'Could not determine price.'
            self.wishlistgames.append(wlgame)

    def initialize(self):

        self.get_wishlist_dom()
        self.parse_dom()

    @staticmethod
    def print_game(game):

        try:
            print '{} ({}) Full price: {} Discount: {} Sale price: {}'.format(game['title'], game['url'],
                                                                              game['full_price'],
                                                                              game['discount_percent'],
                                                                              game['discount_price'])
        except UnicodeEncodeError:
            title = game['title'].encode('ascii', 'ignore')
            print '{} ({}) Full price: {} Discount: {} Sale price: {}'.format(title, game['url'], game['full_price'],
                                                                              game['discount_percent'],
                                                                              game['discount_price'])

    @staticmethod
    def get_discount_price_float(g):
        return float(g['discount_price'].lstrip('$'))

    @staticmethod
    def get_discount_percent_int(g):
        return int(g['discount_percent'].strip('-%'))

    @staticmethod
    def get_full_price_float(g):
        return float(g['full_price'].lstrip('$'))

    def print_discounted_games(self, sort_type=None, max_price=None, min_discount=None):

        dg = self.get_discounted_games(sort_type, max_price, min_discount)

        for game in dg:
            self.print_game(game)

    def get_discounted_games(self, sort_type=None, max_price=None, min_discount=None):

        dg = []

        for game in self.wishlistgames:
            if 'discounted' in game and game['discounted']:
                if max_price and (self.get_discount_price_float(game) > max_price):
                    pass
                elif min_discount and (self.get_discount_percent_int(game) < min_discount):
                    pass
                else:
                    dg.append(game)

        if sort_type == 'percent':
            dg.sort(key=lambda x: self.get_discount_percent_int(x), reverse=True)
        elif sort_type == 'price':
            dg.sort(key=lambda x: self.get_discount_price_float(x))
        elif sort_type == 'discount':
            dg.sort(key=lambda x: (self.get_full_price_float(x) - self.get_discount_price_float(x)), reverse=True)
        elif sort_type == 'title':
            dg.sort(key=lambda x: x['title'])

        return dg

    def get_discounted_games_count_by_percent(self):

        discount_games = self.get_discounted_games()
        discount_percents = defaultdict(int)

        for game in discount_games:
            discount_percents[game['discount_percent']] += 1

        return discount_percents

    def get_discounted_games_count_by_price(self):

        discount_games = self.get_discounted_games()
        discount_prices = defaultdict(int)

        for game in discount_games:
            discount_prices[game['discount_price']] += 1

        return discount_prices

    def get_appids_removed_from_steam(self):

        appid_set = set(str(self.apps[x]['appid']) for x in range(0, len(self.apps)))
        appinfo_set = set(self.appinfo.keys())

        return appid_set - appinfo_set


class SteamBrowseByTag:

    def __init__(self, tagname, initialize=True):
        self.tagname = tagname
        self.url = 'http://store.steampowered.com/tags/en/{}/'.format(self.tagname)
        self.dom = None
        self.games = {'New Releases': [],
                      'Top Sellers': [],
                      'Popular': [],
                      'Coming Soon': []}
        if initialize:
            self.initialize()

    def get_tag_browse_dom(self):
        r = requests.get(self.url)
        self.dom = BeautifulSoup(r.text, "html.parser")

    def parse_dom(self):

        def parse_browse_row(browse_row):

            row_details = {'url': browse_row.attrs['href'],
                           'title': browse_row.find('div', class_='tab_item_name').text,
                           'app_id': browse_row.attrs['href'].split('/')[4]}
            try:
                row_details['price'] = browse_row.find('div', class_='discount_final_price').text
            except AttributeError:
                row_details['price'] = None
            try:
                row_details['discount_pct'] = browse_row.find('div', class_='discount_pct').text
            except AttributeError:
                row_details['discount_pct'] = None
            try:
                row_details['original_price'] = browse_row.find('div', class_='discount_original_price').text
            except AttributeError:
                row_details['original_price'] = None

            return row_details

        new_releases_rows = self.dom.find('div', id='NewReleasesRows')
        for row in new_releases_rows.find_all('a'):
            self.games['New Releases'].append(parse_browse_row(row))

        top_sellers_rows = self.dom.find('div', id='TopSellersRows')
        for row in top_sellers_rows.find_all('a'):
            self.games['Top Sellers'].append(parse_browse_row(row))

        popular_rows = self.dom.find('div', id='ConcurrentUsersRows')
        for row in popular_rows.find_all('a'):
            self.games['Popular'].append(parse_browse_row(row))

        coming_soon_rows = self.dom.find('div', id='ComingSoonRows')
        for row in coming_soon_rows:
            try:
                self.games['Coming Soon'].append(parse_browse_row(row))
            except AttributeError:
                pass

    def initialize(self):

        self.get_tag_browse_dom()
        self.parse_dom()
