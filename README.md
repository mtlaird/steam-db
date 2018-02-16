This script is not really done, but it has some functionality right now, at least.

It requires the requests, BeautifulSoup, and lxml modules. Eventually, I'd like to have an installer that creates a virtualenv and installs the necessary modules. At the moment, I have a partially completed windows version.

Whether you have your own virtualenv or are just using system python, you can run the script like this:

`python wishlist_analyzer.py`

But that won't do anything, by itself. You need to provide a steam user id, which can be either the username or all-digit ID you will see on either the `https://store.steampowered.com/wishlist/id/<username>/` or `http://steamcommunity.com/profiles/<id>/wishlist/` URLs.

Once you give it a username, it will scrape your Steam wishlist and print out a summary of the games on your wishlist that are currently on sale. From there, you have a few extra options.

If you pass the `--sort-type` / `-s` option, you can specify whether the output will be sorted by the game's `title`, the discounted `price`, the amount of the `discount`, or the `percent` of the discount.

You can also provide `--max-price` / `-p` and/or `--min-discount` / `-d` options, which will only print games that meet those criteria.

Finally, if you specify `--historical-low` / `-l` when running the script, it will perform additional web requests to scrape the SteamDB.info page for the corresponding app, and will only print it out if the current sale price matches the historical low price for the game.

Steam just updated their wishlist page format, so I have done very little testing with this script in its current version. So keep an eye on that!
