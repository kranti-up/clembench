# Import matplotlib
import matplotlib.pyplot as plt

# Data
shapes = [2, 3, 4, 5]
total_episodes = [10, 34, 73, 48]

clarifications = [4, 21, 57, 35]
corrections = [1, 2, 5, 2]

# Normalize (compute rates)
clarification_rates = [c/t for c, t in zip(clarifications, total_episodes)]
correction_rates = [c/t for c, t in zip(corrections, total_episodes)]

# Plot
plt.figure()
plt.plot(shapes, clarification_rates, marker='o', linewidth=2, color="#4C72B0", label="Clarification")
plt.plot(shapes, correction_rates, marker='o', linewidth=2, color="#DD8452", label="Correction")

plt.xlabel("Number of elements/object")
plt.ylabel("Normalized Rate")
plt.title("Dialogue quality statistics")
plt.xticks(shapes)
plt.ylim(0, 1)
plt.legend()
plt.grid(alpha=0.3)

plt.show()
plt.savefig("dialogue_quality_stats.png")
plt.close()