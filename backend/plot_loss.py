import matplotlib.pyplot as plt
import numpy as np

# Sample data representing TimeGAN phases
epochs = np.arange(1, 101)
autoencoder_loss = np.exp(-epochs/15) + 0.1
generator_loss = 0.5 + 0.2 * np.sin(epochs/5) * np.exp(-epochs/30)
discriminator_loss = 0.5 - 0.2 * np.sin(epochs/5) * np.exp(-epochs/30)

plt.figure(figsize=(10, 6))
plt.plot(epochs[:30], autoencoder_loss[:30], label='Autoencoder Loss', color='blue', linewidth=2)
plt.plot(epochs[30:], generator_loss[30:], label='Generator Loss', color='green', linewidth=2)
plt.plot(epochs[30:], discriminator_loss[30:], label='Discriminator Loss', color='red', linewidth=2)

plt.axvline(x=30, color='gray', linestyle='--', label='Phase Transition')
plt.title('TimeGAN 3-Phase Training Convergence', fontsize=14, fontname='Times New Roman')
plt.xlabel('Epochs', fontsize=12, fontname='Times New Roman')
plt.ylabel('Loss', fontsize=12, fontname='Times New Roman')
plt.legend(loc='upper right')
plt.grid(True, linestyle=':', alpha=0.7)

# Save as a high-res image
plt.savefig('training_loss.png', dpi=300, bbox_inches='tight')
print("Graph saved as training_loss.png")