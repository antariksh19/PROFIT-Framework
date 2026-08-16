import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text

# 1. Database Connection String
DB_URL = "postgresql://postgres:profit_admin@localhost:5433/postgres"
engine = create_engine(DB_URL)

def setup_database():
    print("Setting up database schema...")
    with engine.connect() as conn:
        # Create the standard table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS daily_prices (
                ticker VARCHAR(10) NOT NULL,
                trade_date DATE NOT NULL,
                open DECIMAL(12, 4),
                high DECIMAL(12, 4),
                low DECIMAL(12, 4),
                close DECIMAL(12, 4),
                volume BIGINT,
                UNIQUE (ticker, trade_date)
            );
        """))
        
        # Convert to TimescaleDB Hypertable (if it isn't already)
        try:
            conn.execute(text("SELECT create_hypertable('daily_prices', 'trade_date');"))
            print("Hypertable created successfully.")
        except Exception as e:
            # It will throw an error if the hypertable already exists, which is fine
            print("Hypertable already exists or configuration skipped.")
            
        conn.commit()

def fetch_and_store_data(ticker_symbol, start_date, end_date):
    print(f"Fetching data for {ticker_symbol}...")
    
    # 2. Download data using yfinance
    data = yf.download(ticker_symbol, start=start_date, end=end_date)
    
    if data.empty:
        print("No data found!")
        return

    # 3. Clean up the DataFrame to match our SQL schema
    data = data.reset_index()
    # Handle multi-level columns if yfinance returns them
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
        
    data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    data.columns = ['trade_date', 'open', 'high', 'low', 'close', 'volume']
    data['ticker'] = ticker_symbol

    # 4. Push to TimescaleDB
    data.to_sql('daily_prices', engine, if_exists='append', index=False)
    print(f"Successfully stored {len(data)} rows for {ticker_symbol}.")

if __name__ == "__main__":
    setup_database()
    # Test the pipeline with Apple data from the last few years
    fetch_and_store_data("AAPL", "2020-01-01", "2024-01-01")