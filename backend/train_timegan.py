import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from timegan_dataset import TimeSeriesDataset
from timegan_models import RNNEmbedder, RNNRecovery, RNNGenerator, RNNDiscriminator


def train_timegan(
    ticker: str = "AAPL",
    seq_len: int = 24,
    hidden_dim: int = 24,
    num_layers: int = 3,
    batch_size: int = 64,
    epochs_autoencoder: int = 50,
    epochs_supervised: int = 50,
    epochs_joint: int = 100,
    lr: float = 0.001,
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training TimeGAN on device: {device}")

    # 1. Dataset & DataLoader
    dataset = TimeSeriesDataset(ticker=ticker, seq_len=seq_len)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=True)

    input_dim = len(dataset.feature_names)
    z_dim = input_dim

    # 2. Initialize Models
    embedder = RNNEmbedder(input_dim, hidden_dim, num_layers).to(device)
    recovery = RNNRecovery(hidden_dim, input_dim, num_layers).to(device)
    generator = RNNGenerator(z_dim, hidden_dim, num_layers).to(device)
    discriminator = RNNDiscriminator(hidden_dim, num_layers).to(device)

    # 3. Optimizers
    opt_e = torch.optim.Adam(embedder.parameters(), lr=lr)
    opt_r = torch.optim.Adam(recovery.parameters(), lr=lr)
    opt_g = torch.optim.Adam(generator.parameters(), lr=lr)
    opt_d = torch.optim.Adam(discriminator.parameters(), lr=lr)

    # 4. Loss Functions
    mse_loss = nn.MSELoss()
    bce_loss = nn.BCEWithLogitsLoss()

    # ==========================================
    # PHASE 1: Autoencoder Training (Embedder + Recovery)
    # ==========================================
    print("\n--- Phase 1: Autoencoder Training ---")
    for epoch in range(1, epochs_autoencoder + 1):
        total_loss = 0.0
        for x in dataloader:
            x = x.to(device)
            opt_e.zero_grad()
            opt_r.zero_grad()

            h = embedder(x)
            x_tilde = recovery(h)

            loss_er = mse_loss(x_tilde, x)
            loss_er.backward()

            opt_e.step()
            opt_r.step()
            total_loss += loss_er.item()

        if epoch % 10 == 0 or epoch == epochs_autoencoder:
            print(f"Autoencoder Epoch [{epoch}/{epochs_autoencoder}] | Loss: {total_loss / len(dataloader):.6f}")

    # ==========================================
    # PHASE 2: Supervised Training (Generator temporal dynamics)
    # ==========================================
    print("\n--- Phase 2: Supervised Training ---")
    for epoch in range(1, epochs_supervised + 1):
        total_loss = 0.0
        for x in dataloader:
            x = x.to(device)
            opt_g.zero_grad()

            with torch.no_grad():
                h = embedder(x)

            # Generate latent sequences from random noise
            z = torch.rand(batch_size, seq_len, z_dim).to(device)
            h_hat = generator(z)

            # Supervised loss: step-ahead prediction
            loss_s = mse_loss(h[:, 1:, :], h_hat[:, :-1, :])
            loss_s.backward()

            opt_g.step()
            total_loss += loss_s.item()

        if epoch % 10 == 0 or epoch == epochs_supervised:
            print(f"Supervised Epoch [{epoch}/{epochs_supervised}] | Loss: {total_loss / len(dataloader):.6f}")

    # ==========================================
    # PHASE 3: Joint Adversarial Training
    # ==========================================
    print("\n--- Phase 3: Joint Adversarial Training ---")
    for epoch in range(1, epochs_joint + 1):
        d_total_loss = 0.0
        g_total_loss = 0.0

        for x in dataloader:
            x = x.to(device)
            z = torch.rand(batch_size, seq_len, z_dim).to(device)

            # --- Train Discriminator ---
            opt_d.zero_grad()

            with torch.no_grad():
                h_real = embedder(x)
                h_fake = generator(z)

            d_real = discriminator(h_real)
            d_fake = discriminator(h_fake)

            loss_d_real = bce_loss(d_real, torch.ones_like(d_real))
            loss_d_fake = bce_loss(d_fake, torch.zeros_like(d_fake))
            loss_d = loss_d_real + loss_d_fake

            loss_d.backward()
            opt_d.step()
            d_total_loss += loss_d.item()

            # --- Train Generator & Recovery & Embedder ---
            opt_g.zero_grad()
            opt_e.zero_grad()
            opt_r.zero_grad()

            h_real = embedder(x)
            x_tilde = recovery(h_real)
            h_fake = generator(z)
            d_fake = discriminator(h_fake)

            loss_reconstruct = mse_loss(x_tilde, x)
            loss_unsupervised = bce_loss(d_fake, torch.ones_like(d_fake))
            loss_supervised = mse_loss(h_real[:, 1:, :], h_fake[:, :-1, :])

            # Combined generator loss
            loss_g_total = (
                loss_unsupervised
                + 100 * torch.sqrt(loss_supervised)
                + 10 * loss_reconstruct
            )

            loss_g_total.backward()
            opt_g.step()
            opt_e.step()
            opt_r.step()

            g_total_loss += loss_g_total.item()

        if epoch % 20 == 0 or epoch == epochs_joint:
            print(
                f"Joint Epoch [{epoch}/{epochs_joint}] | "
                f"D Loss: {d_total_loss / len(dataloader):.4f} | "
                f"G Loss: {g_total_loss / len(dataloader):.4f}"
            )

    # 5. Save Model Checkpoints
    os.makedirs("models", exist_ok=True)
    torch.save(generator.state_dict(), "models/timegan_generator.pt")
    torch.save(recovery.state_dict(), "models/timegan_recovery.pt")
    torch.save(embedder.state_dict(), "models/timegan_embedder.pt")
    print("\nTraining complete! Model checkpoints saved to backend/models/")


if __name__ == "__main__":
    train_timegan()