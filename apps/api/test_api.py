import requests
names = ["JPMorgan", "JP Morgan", "JPMorgan Chase", "JPMorgan Chase & Co.", "JPMC"]
for n in names:
    r = requests.get(f"http://localhost:8000/api/v1/intelligence/{n}")
    if r.status_code == 200:
        data = r.json()
        print(f"Searched: {n} -> Resolved: {data['company_name']}, Articles: {data['overview']['total_articles']}")
    else:
        print(f"Searched: {n} -> Error: {r.status_code}")
