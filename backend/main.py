from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from feature_engine import build_feature_matrix

# 1. Initialize FastAPI Application
app = FastAPI(
    title="PROFIT Framework API",
    description="Backend API Gateway for Portfolio Optimization Framework",
    version="1.0.0",
)

# 2. Enable CORS (Allows your Next.js frontend to talk to this backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Connect to TimescaleDB (Using the updated port 5433)
DB_URL = "postgresql://postgres:profit_admin@localhost:5433/postgres"
engine = create_engine(DB_URL)


@app.get("/")
def read_root():
    """Health check endpoint to verify backend status."""
    return {"status": "online", "message": "PROFIT Framework API is operational"}


@app.get("/api/v1/prices/{ticker}")
def get_historical_prices(ticker: str):
    """Fetch stored historical OHLCV market data for a given ticker from TimescaleDB."""
    query = text("""
        SELECT trade_date, open, high, low, close, volume 
        FROM daily_prices 
        WHERE UPPER(ticker) = UPPER(:ticker) 
        ORDER BY trade_date ASC
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"ticker": ticker})
            rows = result.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No price data found in TimescaleDB for ticker '{ticker}'",
            )

        # Structure response data array
        price_data = [
            {
                "trade_date": str(row.trade_date),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": int(row.volume),
            }
            for row in rows
        ]

        return {
            "ticker": ticker.upper(),
            "total_records": len(price_data),
            "data": price_data,
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")

@app.get("/api/v1/sentiment/{ticker}")
def get_sentiment_logs(ticker: str):
    """Fetch recent FinBERT news sentiment logs for a given ticker."""
    query = text("""
        SELECT published_at, headline, sentiment_score, label 
        FROM sentiment_logs 
        WHERE UPPER(ticker) = UPPER(:ticker) 
        ORDER BY published_at DESC 
        LIMIT 20
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"ticker": ticker})
            rows = result.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No sentiment logs found for ticker '{ticker}'",
            )

        logs = [
            {
                "published_at": str(row.published_at),
                "headline": row.headline,
                "sentiment_score": float(row.sentiment_score),
                "label": row.label,
            }
            for row in rows
        ]

        # Calculate average sentiment score
        avg_score = sum(item["sentiment_score"] for item in logs) / len(logs)

        return {
            "ticker": ticker.upper(),
            "average_sentiment_score": round(avg_score, 4),
            "total_logs": len(logs),
            "logs": logs,
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Database query error: {str(e)}"
        )




@app.get("/api/v1/features/{ticker}")
def get_feature_matrix(ticker: str):
    """Fetch the full enriched feature matrix (Prices + Sentiment + Technical Indicators) for ML training."""
    df = build_feature_matrix(ticker)

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Could not build feature matrix for ticker '{ticker}'",
        )

    # Convert timestamps to string format for JSON serialization
    df["trade_date"] = df["trade_date"].astype(str)

    return {
        "ticker": ticker.upper(),
        "total_records": len(df),
        "features": df.to_dict(orient="records"),
    }