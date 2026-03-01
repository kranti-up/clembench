# Import matplotlib
import matplotlib.pyplot as plt

# Labels
metrics = ["Abort", "Loss", "Reconst", "Optimize", "Overall"]

# Data
qwen = [0.01, 0.33, 0.69, 0.96, 0.66]
gpt = [0.00, 0.06, 0.94, 1.00, 0.94]

x = range(len(metrics))
width = 0.35

plt.figure()

# Eye-pleasing modern colors
plt.bar([i - width/2 for i in x], qwen, width=width, label="Qwen-3 30B", color="#5DA5DA")
plt.bar([i + width/2 for i in x], gpt, width=width, label="GPT-5.2-Codex", color="#60BD68")

plt.xticks(x, metrics)
plt.ylim(0, 1)
plt.title("Teaching (Reconstruction) task performance comarison")
plt.legend()

plt.tight_layout()
plt.show()
plt.savefig("reconstruct_comparison.png")
plt.close()