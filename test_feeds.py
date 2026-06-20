import feedparser
import sys

feeds = {
    "Investing.com": "https://www.investing.com/rss/news_25.rss",
    "Benzinga": "https://www.benzinga.com/feed",
    "Barron's": "https://feeds.barrons.com/v1/rss/search?query=barrons_section%3A%22Markets%22",
    "Google News Business": "https://news.google.com/news/rss/headlines/section/topic/BUSINESS",
    "Financial Times": "https://www.ft.com/markets?format=rss",
    "TheStreet": "https://www.thestreet.com/.rss/full/",
    "CNBC Business (Test)": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147",
    "WSJ Markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
}

for name, url in feeds.items():
    print(f"\n--- Testing {name} ---")
    try:
        f = feedparser.parse(url)
        print("Bozo:", getattr(f, 'bozo', 1))
        print("Status:", getattr(f, 'status', 'N/A'))
        print("Entries:", len(f.entries))
        if f.entries:
            print("Title 1:", getattr(f.entries[0], 'title', 'No Title'))
            print("Link 1:", getattr(f.entries[0], 'link', 'No Link'))
    except Exception as e:
        print("Error:", e)
