import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import torch
from sqlalchemy import create_engine, text
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# 1. Database Connection
DB_URL = "postgresql://postgres:profit_admin@localhost:5433/postgres"
engine = create_engine(DB_URL)

# 2. Load FinBERT Model & Tokenizer
MODEL_NAME = "ProsusAI/finbert"
print("Loading FinBERT model into memory...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)


def setup_sentiment_table():
    """Ensure the sentiment_logs table exists in TimescaleDB."""
    with engine.connect() as conn:
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS sentiment_logs (
                log_id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                published_at TIMESTAMP NOT NULL,
                headline TEXT NOT NULL,
                sentiment_score DECIMAL(5, 4) NOT NULL,
                label VARCHAR(20) NOT NULL
            );
        """)
        )
        conn.commit()


def fetch_news_headlines(ticker: str, count: int = 10):
    """Scrape recent news headlines using Google News RSS feed for a given ticker."""
    print(f"Scraping news headlines for {ticker}...")
    url = f"https://news.google.com/rss/search?q={ticker}+stock+when:7d&hl=en-US&gl=US&ceid=US:en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch news feed.")
        return []

    root = ET.fromstring(response.content)
    articles = []

    for item in root.findall(".//item")[:count]:
        headline = item.find("title").text
        pub_date_str = item.find("pubDate").text
        # Clean headline text if HTML tags exist
        headline_clean = BeautifulSoup(headline, "html.parser").get_text()

        # Parse RSS date format: e.g. 'Mon, 12 Feb 2024 14:30:00 GMT'
        try:
            pub_date = datetime.strptime(
                pub_date_str[:-4], "%a, %d %b %Y %H:%M:%S"
            )
        except Exception:
            pub_date = datetime.utcnow()

        articles.append({"headline": headline_clean, "published_at": pub_date})

    return articles


def analyze_sentiment(headlines: list[str]):
    """Run FinBERT model inference on a batch of headlines."""
    inputs = tokenizer(
        headlines, padding=True, truncation=True, return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

    # FinBERT labels order: [Positive, Negative, Neutral]
    results = []
    for pred in predictions:
        pos, neg, neu = pred[0].item(), pred[1].item(), pred[2].item()

        # Compute continuous score: Positive (+1) to Negative (-1)
        score = pos - neg

        if pos > neg and pos > neu:
            label = "positive"
        elif neg > pos and neg > neu:
            label = "negative"
        else:
            label = "neutral"

        results.append({"score": round(score, 4), "label": label})

    return results


def process_and_store_sentiment(ticker: str):
    """Pipeline function to scrape news, analyze sentiment, and write to database."""
    setup_sentiment_table()

    articles = fetch_news_headlines(ticker, count=10)
    if not articles:
        print("No articles retrieved.")
        return

    headlines = [a["headline"] for a in articles]
    sentiment_results = analyze_sentiment(headlines)

    # Insert into TimescaleDB
    with engine.connect() as conn:
        for article, sentiment in zip(articles, sentiment_results):
            conn.execute(
                text("""
                INSERT INTO sentiment_logs (ticker, published_at, headline, sentiment_score, label)
                VALUES (:ticker, :published_at, :headline, :score, :label)
            """),
                {
                    "ticker": ticker.upper(),
                    "published_at": article["published_at"],
                    "headline": article["headline"],
                    "score": sentiment["score"],
                    "label": sentiment["label"],
                },
            )
        conn.commit()

    print(
        f"Successfully processed and stored {len(articles)} sentiment records for {ticker}."
    )


if __name__ == "__main__":
    process_and_store_sentiment("AAPL")