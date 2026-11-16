import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from sklearn.preprocessing import MinMaxScaler
from feature_engine import build_feature_matrix


class TimeSeriesDataset(Dataset):
    """
    Sliding window dataset for training TimeGAN on multi-feature market data.
    """
    def __init__(self, ticker: str = "AAPL", seq_len: int = 24):
        self.seq_len = seq_len
        self.scaler = MinMaxScaler(feature_range=(0, 1))

        # 1. Fetch feature matrix from feature engine
        df = build_feature_matrix(ticker)

        # 2. Filter out non-numeric/metadata columns like trade_date or id
        excluded_cols = {"id", "ticker", "trade_date", "created_at"}
        candidate_cols = [
            c for c in df.columns 
            if c not in excluded_cols and pd.api.types.is_numeric_dtype(df[c])
        ]

        # Ensure standard baseline features are prioritized in order
        priority_cols = ["open", "high", "low", "close", "volume", "sma_20", "rsi_14"]
        feature_cols = [c for c in priority_cols if c in candidate_cols]
        # Append any additional numeric features present in df
        for c in candidate_cols:
            if c not in feature_cols:
                feature_cols.append(c)

        self.feature_names = feature_cols

        # Drop rows where rolling indicators haven't warmed up yet
        clean_df = df[feature_cols].dropna().reset_index(drop=True)
        raw_data = clean_df.values

        # 3. Fit-transform MinMax scaler to [0, 1]
        self.scaled_data = self.scaler.fit_transform(raw_data)

        # 4. Generate sliding windows
        self.sequences = self._create_sequences(self.scaled_data, seq_len)

    def _create_sequences(self, data: np.ndarray, seq_len: int) -> np.ndarray:
        sequences = []
        for i in range(len(data) - seq_len + 1):
            sequences.append(data[i : i + seq_len])
        return np.array(sequences, dtype=np.float32)

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> torch.Tensor:
        return torch.tensor(self.sequences[idx], dtype=torch.float32)


if __name__ == "__main__":
    dataset = TimeSeriesDataset(ticker="AAPL", seq_len=24)
    print("Dataset successfully created!")
    print(f"Total sequences generated: {len(dataset)}")
    print(f"Single sequence shape (seq_len, num_features): {dataset[0].shape}")
    print(f"Feature columns used ({len(dataset.feature_names)}): {dataset.feature_names}")