import feedparser

url = "https://feeds.reuters.com/reuters/businessNews"

feed = feedparser.parse(url)

print("Feed Title:", feed.feed.get("title"))
print("Entries:", len(feed.entries))

for entry in feed.entries[:5]:
    print(entry.get("title"))