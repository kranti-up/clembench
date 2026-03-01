# Import matplotlib
import matplotlib.pyplot as plt

# Data
models = ["Qwen3-Coder", "GPT5.2-Codex"]
success = [0.66, 0.94]
token_cost = [1.32, 10.30]

plt.figure(figsize=(7, 5))

# Scatter plot
plt.scatter(token_cost, success)

# Annotate points
for i, model in enumerate(models):
    plt.annotate(model, (token_cost[i], success[i]), xytext=(5,5), textcoords='offset points')

plt.xlabel("Token Cost ($)")
plt.ylabel("Success Rate")
plt.ylim(0, 1)
plt.title("Success vs Token Cost")

plt.tight_layout()
plt.show()
plt.savefig("success_vs_token_cost.png")
plt.close()