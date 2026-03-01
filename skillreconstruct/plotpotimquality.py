# Import matplotlib
import matplotlib.pyplot as plt

# Updated labels and order
metrics_opt = [
    "Overall success",
    "Has FN?",
    "Has Loop?",
    "Reduced put()",
    "Reduced ByteLen"
]

# Data
qwen_opt = [0.96, 1.00, 0.62, 0.70, 0.23]
gpt_opt = [1.00, 1.00, 1.00, 1.00, 0.43]

x = range(len(metrics_opt))
width = 0.35

# Increase figure width for better spacing
plt.figure(figsize=(10, 5))

# Maintain previously used colors
plt.bar([i - width/2 for i in x], qwen_opt, width=width, label="Qwen-3 30B", color="#4E79A7")
plt.bar([i + width/2 for i in x], gpt_opt, width=width, label="GPT-5.2-Codex", color="#F28E2B")

plt.xticks(x, metrics_opt)
plt.ylim(0, 1)
plt.title("Optimization Quality Statistics")
plt.legend()

plt.tight_layout()
plt.show()
plt.savefig("optimization_quality_comparison.png")
plt.close()