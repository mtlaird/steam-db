import SteamWebClasses as swc
import argparse


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('user_id')
    parser.add_argument('-s', '--sort-type')
    parser.add_argument('-p', '--max-price')
    parser.add_argument('-d', '--min-discount')
    parser.add_argument('-l', '--historical-low', action='store_true')

    args = parser.parse_args()

    wishlist = swc.SteamWishList(user_id=args.user_id)

    max_price = int(args.max_price) if args.max_price else None
    min_discount = int(args.min_discount) if args.min_discount else None

    if not args.historical_low:
        wishlist.print_discounted_games(sort_type=args.sort_type, max_price=max_price, min_discount=min_discount)
    else:
        wlg = wishlist.get_discounted_games(sort_type=args.sort_type, max_price=max_price, min_discount=min_discount)
        for game in wlg:
            sdb = swc.SteamAppInfo(app_id=game['id'], domtype='steamdb')
            sdb.initialize()
            hlp = sdb.get_steamdb_historical_low_price()
            if float(hlp['price'].strip('$')) >= float(game['discount_price'].strip('$')):
                wishlist.print_game(game)


if __name__ == '__main__':
    main()
