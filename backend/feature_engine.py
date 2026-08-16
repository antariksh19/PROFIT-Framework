import pandas as pd
from sqlalchemy import create_engine, text
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

# Database Connection
DB_URL = "postgresql://postgres:profit_admin@localhost:5433/postgres"
engine = create_engine(DB_URL)


def build_feature_matrix(ticker: str) -> pd.DataFrame:
    """Builds an enriched feature matrix combining OHLCV, FinBERT sentiment, and technical indicators."""
    print(f"Building feature matrix for {ticker}...")

    # 1. Fetch Daily Prices
    price_query = text("""
        SELECT trade_date, open, high, low, close, volume
        FROM daily_prices
        WHERE UPPER(ticker) = UPPER(:ticker)
        ORDER BY trade_date ASC
    """)

    # 2. Fetch Daily Sentiment Aggregates
    sentiment_query = text("""
        SELECT DATE(published_at) AS trade_date, AVG(sentiment_score) AS avg_sentiment
        FROM sentiment_logs
        WHERE UPPER(ticker) = UPPER(:ticker)
        GROUP BY DATE(published_at)
        ORDER BY trade_date ASC
    """)

    with engine.connect() as conn:
        prices_df = pd.read_sql_query(
            price_query, conn, params={"ticker": ticker}
        )
        sentiment_df = pd.read_sql_query(
            sentiment_query, conn, params={"ticker": ticker}
        )

    if prices_df.empty:
        print(f"No price data found for {ticker}")
        return pd.DataFrame()

    # Ensure trade_date columns are datetime objects for merging
    prices_df["trade_date"] = pd.to_datetime(prices_df["trade_date"])

    if not sentiment_df.empty:
        sentiment_df["trade_date"] = pd.to_datetime(sentiment_df["trade_date"])
        # Merge prices and sentiment on trade_date
        df = pd.merge(prices_df, sentiment_df, on="trade_date", how="left")
        # Fill days with no news as neutral sentiment (0.0)
        df["avg_sentiment"] = df["avg_sentiment"].fillna(0.0)
    else:
        df = prices_df
        df["avg_sentiment"] = 0.0

    # 3. Calculate Technical Indicators
    # 20-day Simple Moving Average (SMA)
    sma_20 = SMAIndicator(close=df["close"], window=20)
    df["sma_20"] = sma_20.sma_indicator()

    # 14-day Relative Strength Index (RSI)
    rsi_14 = RSIIndicator(close=df["close"], window=14)
    df["rsi_14"] = rsi_14.rsi()

    # Calculate daily percentage returns
    df["daily_return"] = df["close"].pct_change()

    # Drop initial NaN rows created by rolling windows
    df = df.dropna().reset_index(drop=True)

    print(
        f"Feature matrix built successfully for {ticker}: {len(df)} records generated."
    )
    return df


if __name__ == "__main__":
    df_features = build_feature_matrix("AAPL")
    if not df_features.empty:
        print("\nFeature Matrix Sample:")
        print(df_features.head())