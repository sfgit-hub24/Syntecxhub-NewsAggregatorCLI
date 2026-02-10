import requests
import json
import csv
import argparse
import os
import logging
from dotenv import load_dotenv
from openpyxl import Workbook
from tabulate import tabulate
# --------------------------------------------------------
# Load API key
# --------------------------------------------------------
load_dotenv()
api_key = os.getenv("NEWS_API_KEY")

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "news_data.json")
# --------------------------------------------------------
# Logging configuration
# --------------------------------------------------------
logging.basicConfig(
    filename="news.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------------------------------------------------------
# Fetch news from NewsAPI
# --------------------------------------------------------
def fetch_news(keyword=None):
    logging.info(f"Fetching news with keyword: {keyword}")

    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "us",
        "apiKey": api_key
    }

    if keyword:
        params["q"] = keyword

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return []

    articles = []
    for item in data.get("articles", []):
        articles.append({
            "title": item["title"],
            "source": item["source"]["name"],
            "date": item["publishedAt"][:10],
            "url": item["url"]
        })

    return articles
# ---------------------------------------------------------
# Save to JSON
# ---------------------------------------------------------
def save_json(news):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(news, f, indent=4)

    logging.info("News data saved to JSON")

# ---------------------------------------------------------
# Remove duplicate titles
# ---------------------------------------------------------
def remove_duplicates(news):
    seen = set()
    unique = []

    for item in news:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)

    logging.info(f"Removed duplicates. Remaining: {len(unique)}")
    return unique
# --------------------------------------------------------
# Filters
# ---------------------------------------------------------
def filter_news(news, source=None, date=None):
    filtered = []

    for item in news:
        if source and source.lower() not in item["source"].lower():
            continue
        if date and date != item["date"]:
            continue
        filtered.append(item)

    logging.info(f"Filtered news count: {len(filtered)}")
    return filtered
# --------------------------------------------------------
# Export CSV
# --------------------------------------------------------
def export_csv(news):
    if not news:
        logging.warning("CSV export skipped: No data")
        print("No data to export.")
        return

    with open("news.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=news[0].keys())
        writer.writeheader()
        writer.writerows(news)

    logging.info("Exported news to CSV")
    print("Saved to news.csv")
# --------------------------------------------------------
# Export Excel
# --------------------------------------------------------
def export_excel(news):
    if not news:
        logging.warning("Excel export skipped: No data")
        print("No data to export.")
        return

    wb = Workbook()
    ws = wb.active
    ws.append(list(news[0].keys()))

    for item in news:
        ws.append(list(item.values()))

    wb.save("news.xlsx")

    logging.info("Exported news to Excel")
    print("Saved to news.xlsx")
# --------------------------------------------------------
# Display
# --------------------------------------------------------
def display(news):
    if not news:
        print("No news found.")
        return

    table = []
    for i, item in enumerate(news, 1):
        table.append([i, item["title"], item["source"], item["date"]])

    print(tabulate(
        table,
        headers=["No", "Title", "Source", "Date"],
        tablefmt="grid"
    ))
# --------------------------------------------------------
# CLI
# --------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="News Aggregator CLI")
    parser.add_argument("--keyword")
    parser.add_argument("--source")
    parser.add_argument("--date")
    parser.add_argument("--export", choices=["csv", "excel"])
    args = parser.parse_args()

    logging.info("Program started")

    news = fetch_news(args.keyword)
    logging.info(f"{len(news)} articles fetched")

    news = remove_duplicates(news)
    news = filter_news(news, args.source, args.date)

    display(news)
    save_json(news)

    if args.export == "csv":
        export_csv(news)
    elif args.export == "excel":
        export_excel(news)

    logging.info("Program finished")
# --------------------------------------------------------
if __name__ == "__main__":
    main()
