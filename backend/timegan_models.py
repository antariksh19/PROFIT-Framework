import torch
import torch.nn as nn

class RNNEmbedder(nn.Module):
    """Maps feature space (e.g., 9 dims) to latent space."""
    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int = 3):
        super().__init__()
        self.rnn = nn.GRU(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, hidden_dim)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.rnn(x)
        out = self.fc(out)
        return self.sigmoid(out)

class RNNRecovery(nn.Module):
    """Maps latent space back to original feature space."""
    def __init__(self, hidden_dim: int, output_dim: int, num_layers: int = 3):
        super().__init__()
        self.rnn = nn.GRU(hidden_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.sigmoid = nn.Sigmoid() # Maps output back to [0, 1] for MinMax scaled data

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        out, _ = self.rnn(h)
        out = self.fc(out)
        return self.sigmoid(out)

class RNNGenerator(nn.Module):
    """Generates synthetic latent dynamics from random noise."""
    def __init__(self, z_dim: int, hidden_dim: int, num_layers: int = 3):
        super().__init__()
        self.rnn = nn.GRU(z_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, hidden_dim)
        self.sigmoid = nn.Sigmoid()

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        out, _ = self.rnn(z)
        out = self.fc(out)
        return self.sigmoid(out)

class RNNDiscriminator(nn.Module):
    """Classifies latent sequences as real (from Embedder) or fake (from Generator)."""
    def __init__(self, hidden_dim: int, num_layers: int = 3):
        super().__init__()
        self.rnn = nn.GRU(hidden_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        out, _ = self.rnn(h)
        out = self.fc(out)
        # Returning raw logits (no sigmoid) for stability with BCEWithLogitsLoss
        return out 


if __name__ == "__main__":
    # Smoke test to verify tensor dimensions
    batch_size = 32
    seq_len = 24
    input_dim = 9  # Based on our dataset output
    hidden_dim = 24
    z_dim = 9
    
    embedder = RNNEmbedder(input_dim, hidden_dim)
    recovery = RNNRecovery(hidden_dim, input_dim)
    generator = RNNGenerator(z_dim, hidden_dim)
    discriminator = RNNDiscriminator(hidden_dim)
    
    # Mock data tensors
    x = torch.rand(batch_size, seq_len, input_dim)
    z = torch.rand(batch_size, seq_len, z_dim)
    
    # Forward passes
    h = embedder(x)
    x_tilde = recovery(h)
    h_hat = generator(z)
    y_real = discriminator(h)
    
    print("PyTorch TimeGAN Networks Initialized Successfully!")
    print(f"X (Input) shape:           {x.shape}")
    print(f"H (Latent) shape:          {h.shape}")
    print(f"X_tilde (Recovered) shape: {x_tilde.shape}")
    print(f"H_hat (Generated) shape:   {h_hat.shape}")
    print(f"Y_real (Logits) shape:     {y_real.shape}")