import urllib.request
import json
import urllib.parse

companies = ['Tesla', 'Nvidia', 'Apple', 'Microsoft', 'Google', 'Alphabet', 'Amazon']

for c in companies:
    try:
        url = f'http://localhost:8000/api/v1/intelligence/{urllib.parse.quote(c)}'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"{c}: OK, {len(data.get('news_feed', []))} articles, total articles: {data.get('overview', {}).get('total_articles')}")
            
            # Check duplicates
            urls = []
            ids = []
            for art in data.get('news_feed', []):
                if art.get('article_url'):
                    urls.append(art.get('article_url'))
                ids.append(art.get('id'))
            
            if len(urls) != len(set(urls)):
                print(f"  -> Found URL duplicates in {c}! Unique URLs: {len(set(urls))} vs Total URLs: {len(urls)}")
            if len(ids) != len(set(ids)):
                print(f"  -> Found ID duplicates in {c}! Unique IDs: {len(set(ids))} vs Total IDs: {len(ids)}")
    except Exception as e:
        print(f"{c}: FAILED - {e}")
