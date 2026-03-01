# Import matplotlib
import matplotlib.pyplot as plt

# Data
num_elements = [2, 3, 4, 5]
reconst_success = [1.00, 0.79, 0.68, 0.56]
opt_success = [1.00, 1.00, 0.94, 0.93]

plt.figure(figsize=(8, 5))

# Eye-pleasing modern colors
plt.plot(num_elements, reconst_success, marker='o', linewidth=2.5, label="Reconstruction Success", color="#4E79A7")
plt.plot(num_elements, opt_success, marker='s', linewidth=2.5, label="Optimization Success", color="#59A14F")

plt.xlabel("Number of Elements / Objects")
plt.ylabel("Success Rate")
plt.ylim(0, 1)
plt.xticks(num_elements)
plt.title("Success Rate vs Number of Elements")
plt.legend()

plt.tight_layout()
plt.show()
plt.savefig("success_vs_num_elements.png")
plt.close()