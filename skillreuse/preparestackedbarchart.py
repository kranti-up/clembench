import matplotlib.pyplot as plt
import numpy as np
import json



def readfile(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def plot_multiple_subplots(base_dir, data, filename):
    fig, axes = plt.subplots(2, 2, figsize=(14,11), sharex=True)
    fig.subplots_adjust(
        hspace=0.45,   # vertical space between rows
        wspace=0.25    # horizontal space between columns
    )

    model_colors = {
        "Qwen Skills": "#4C72B0",
        "Codex Skills": "#DD8452"
    }

    model_colors = {
        "Qwen Skills": {"success": "#4C72B0", "used_available": "#4C72B0", "used_hallucinated": "#DD8452",},
        "Codex Skills": {"success": "#DD8452", "used_available": "#4C72B0", "used_hallucinated": "#DD8452",}
    }


    markers = {
        "Qwen Skills": "o",
        "Codex Skills": "s"
    }

    def plot_success(ax, data, linestyle="-", linewidth=2):
        skill_types = list(data.keys())
        models = list(data[skill_types[0]].keys())
        x = np.arange(len(models))

        qskills_sa_success = np.array([data[skill_types[0]][model][0] for model in models])
        qskills_sna_success = np.array([data[skill_types[0]][model][1] for model in models])
        gskills_sa_success = np.array([data[skill_types[1]][model][0] for model in models])
        gskills_sna_success = np.array([data[skill_types[1]][model][1] for model in models])

        jitter = 0.01
        ax.plot(x, qskills_sa_success - jitter, marker='o', linestyle='-', label="Qwen Skills - Used", color="#4C72B0")
        ax.plot(x, qskills_sna_success, marker='o', linestyle='--', label="Qwen Skills - Not Used (Reconstruct fallback)", color="#4C72B0")
        ax.plot(x, gskills_sa_success + jitter, marker='o', linestyle='-', label="Codex Skills - Used", color="#DD8452")
        ax.plot(x, gskills_sna_success, marker='o', linestyle='--', label="Codex Skills - Not Used (Reconstruct fallback)", color="#DD8452")

        #ax.set_title("Success Rate when Skills are Used vs Not Used", fontsize=12)
        #ax.set_xlabel("Model Configuration", fontsize=12)
        ax.set_xlabel("(a) Impact of skill usage on success rate", fontsize=12)
        ax.set_xticks(x, models)
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Success Rate", fontsize=12)
        ax.tick_params(axis='both', labelsize=12) 
        ax.legend()           
        ax.grid(axis="y", linewidth=0.5, alpha=0.4)  

    plot_success(axes[0][0], data["success_data"], linestyle=":", linewidth=2) 
    #axes[0][0].text(0.5, -0.14,
    #         "(a) Impact of skill usage on success rate",
    #         transform=axes[0][0].transAxes, ha="center", va="top", fontsize=11)


    def plot_skill_usage(ax, data, linestyle="-", linewidth=2):
        #This would be a scatter plot with different markers for Qwen vs Codex skills and used by each model configuration. On x-axis nothing, but on y-axis the percentage of test instances where skills were used whenever they are available.
        models = list(next(iter(data.values())).keys())
        x = np.arange(len(models))

        markers = ["o", "s", "^", "D"]

        for i, (group, values) in enumerate(data.items()):
            y = [values[m] for m in models]
            ax.plot(
                x,
                y,
                marker=markers[i % len(markers)],
                linewidth=2,
                markersize=7,
                label=group
            )

        ax.set_xticks(x)
        ax.set_xticklabels(models)
        ax.set_ylim(0,100.05)

        #ax.set_xlabel("Model Configuration", fontsize=12)
        ax.set_xlabel("(b) Retrieval of skills when available", fontsize=12)
        ax.set_ylabel("Percentage of Test Instances", fontsize=12)

        ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
        ax.legend(frameon=False)


    plot_skill_usage(axes[0][1], data["skillsused"], linestyle=":", linewidth=2)
    #axes[0][1].text(0.45, -0.14,
    #         "(b) Retrieval of skills when available",
    #         transform=axes[0][1].transAxes, ha="center", va="top", fontsize=11)

    def plot_actual_hallucinated_skills(ax, data, used_skills, linestyle="-", linewidth=2):
        #This would be a stacked bar-chart combining the available vs hallucinated skills for success test cases for Qwen or Codex skills. X-axis would be the model configurations, Y-axis would be the fraction of episodes, and the bars would be color coded based on available vs hallucinated skills.

        models = list(data.keys())
        x = np.arange(len(models))
        used_available = np.array([data[model][0] for model in models])
        used_hallucinated = np.array([data[model][1] for model in models])
        width = 0.4
        bars1 = ax.bar(x, used_available, width=width, color=model_colors[used_skills]["used_available"], label="Used Skills - Available")
        bars2 = ax.bar(x, used_hallucinated, width=width, bottom=used_available, color=model_colors[used_skills]["used_hallucinated"], alpha=0.6, label="Used Skills - Hallucinated")
        # Annotate bars
        """
        for i in range(len(x)):
            if used_available[i] > 0:
                ax.text(
                    x[i],
                    used_available[i] / 2,
                    "Exists",
                    ha="center",
                    va="center",
                    fontsize=10,
                    color="white"
                )

            if used_hallucinated[i] > 0:
                ax.text(
                    x[i],
                    used_available[i] + used_hallucinated[i] / 2,
                    "Hall",
                    ha="center",
                    va="center",
                    fontsize=10
                )
        """

        #ax.set_title(f"{used_skills} - Available vs Hallucinated", fontsize=12)
        ax.set_xlabel(f"Model Configuration ({used_skills})", fontsize=12)
        ax.set_xticks(x, models)
        ax.set_ylim(0, 100.05)
        ax.set_ylabel("Percentage of Test Instances", fontsize=12)
        ax.tick_params(axis='both', labelsize=12)
        #ax.legend()
        #ax.legend(loc="upper centre", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)
        ax.grid(axis="y", linewidth=0.5, alpha=0.4)

    plot_actual_hallucinated_skills(axes[1][0], data["skillactuals"]["Qwen Skills"], "Qwen Skills", linestyle=":", linewidth=2)
    plot_actual_hallucinated_skills(axes[1][1], data["skillactuals"]["Codex Skills"], "Codex Skills", linestyle=":", linewidth=2)
    fig.text(  0.49, -0.01, "(c), (d): Where Qwen/Codex skills were actually available vs cobot hallucinated",
    ha="center", fontsize=12 )
    plt.subplots_adjust(bottom=0.15)

    # hide top row x labels
    for ax in axes[0]:
        ax.tick_params(labelbottom=False)


    models = list(data["skillactuals"]["Qwen Skills"].keys())
    x = np.arange(len(models))

    # set shared x ticks
    axes[1,0].set_xticks(x)
    axes[1,0].set_xticklabels(models)
    axes[1,1].set_xticks(x)
    axes[1,1].set_xticklabels(models)
    axes[1,1].tick_params(labelleft=False)


    plt.tight_layout(rect=[0,0,1,0.9])
    plt.savefig(base_dir + "/" + filename, dpi=300, bbox_inches='tight')
    plt.savefig(base_dir + "/" + filename.replace(".png", ".pdf"), dpi=300, bbox_inches='tight')
    plt.close()     



def plot_success_rate(base_dir, data, filename):

    skill_types = list(data.keys())
    models = list(data[skill_types[0]].keys())

    x = np.arange(len(models))

    # Data
    qskills_sa_success = np.array([data[skill_types[0]][model]["used_success"] for model in models])
    qskills_sna_success = np.array([data[skill_types[0]][model]["not_used_success"] for model in models])
    gskills_sa_success = np.array([data[skill_types[1]][model]["used_success"] for model in models])
    gskills_sna_success = np.array([data[skill_types[1]][model]["not_used_success"] for model in models])

    # Small jitter so overlapping lines are visible
    jitter = 0.01
    plt.figure()
    plt.plot(x, qskills_sa_success - jitter, marker='o', linestyle='-', label="Qwen Skills - Used", color="#4C72B0")
    plt.plot(x, qskills_sna_success, marker='o', linestyle='--', label="Qwen Skills - Not Used (Reconstruct fallback)", color="#4C72B0")
    plt.plot(x, gskills_sa_success + jitter, marker='o', linestyle='-', label="Codex Skills - Used", color="#DD8452")
    plt.plot(x, gskills_sna_success, marker='o', linestyle='--', label="Codex Skills - Not Used (Reconstruct fallback)", color="#DD8452")

    plt.xticks(x, models)
    plt.xlabel("Model Configuration")
    plt.ylabel("Success Rate")
    plt.ylim(0, 1.05)
    plt.title("Success Rate when Skills are Used vs Not Used")
    plt.legend()
    plt.tight_layout(rect=[0, 0, 1, 0.92])
    #plt.show()
    plt.savefig(base_dir + "/" + filename, dpi=300, bbox_inches='tight')
    plt.savefig(base_dir + "/" + filename.replace(".png", ".pdf"), dpi=300, bbox_inches='tight')
    plt.close() 


def plotdata(base_dir, data, filename):

    models = list(data.keys())
    fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharey=True)
    axes = axes.flatten()

    for i, model in enumerate(models):
        used_success = data[model]["used_success"]
        not_used_success = data[model]["not_used_success"]
        used_avail = data[model]["used_available"]
        used_unavail = data[model]["used_generated"]
        not_used_avail = data[model]["not_used_available"]
        not_used_unavail = data[model]["not_used_unavailable"]
        ax = axes[i]

        print(f"Model: {model}, {used_success} {used_avail}")

        blue = np.array([
            used_success * used_avail,
            not_used_success * not_used_avail
        ])
        orange = np.array([
            used_success * used_unavail,
            not_used_success * not_used_unavail
        ])

        x = np.array([0, 0.4])#np.arange(2)
        #ax.bar(x, blue, width=0.42, color="#4C72B0")
        #ax.bar(x, orange, width=0.42, bottom=blue, color="#DD8452")
        width = 0.08
        ax.bar(x, blue, width=width, color="#4C72B0", label="Skills available")
        ax.bar(x, orange, width=width, bottom=blue, color="#DD8452", label="Skills not available")       

        ax.set_xticks(x)
        ax.set_xticklabels(["Skills used", "Skills not used"])
        ax.set_title(model)
        ax.set_xlim(-0.1, 0.45)
        ax.margins(x=0)
        ax.set_ylim(0, 1.05)

        if i % 2 == 0:
            ax.set_ylabel("Success rate")

    # Hide last empty subplot
    #axes[-1].axis("off")

    # Shared legend
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#4C72B0"),
        plt.Rectangle((0, 0), 1, 1, color="#DD8452"),
    ]
    fig.legend(handles, ["Skills available", "Skills not available"], loc="upper center", ncol=2, frameon=False)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    #plt.show()
    plt.savefig(base_dir + "/" + filename, dpi=300, bbox_inches='tight')
    plt.savefig(base_dir + "/" + filename.replace(".png", ".pdf"), dpi=300, bbox_inches='tight')
    plt.close()


def run(base_dir_list):
    data = {"success_data": {}, "skillsused":  {"Qwen Skills": {}, "Codex Skills": {}},
            "skillactuals": {"Qwen Skills": {}, "Codex Skills": {}}}
    used_model_name = {'clp-chat-2-t0.0': "QC-QC", 'upgpt-codex-t0.0--clp-chat-2-t0.0': "GC-QC", 'upgpt-codex-t0.0': "GC-GC", 'clp-chat-2-t0.0--upgpt-codex-t0.0': "QC-GC"}

    for base_dir in base_dir_list:
        overallstats = readfile(base_dir + "/overallstats.json")
        if overallstats is None:
            print("No overallstats.json found in the specified directory.")
            return

        if "clpskills" in base_dir:
            skill_type = "Qwen Skills"
        else:
            skill_type = "Codex Skills"

        #if skill_type not in data:
        #    data[skill_type] = {}

        overallstats = overallstats["skillreuse"]
        model_name = list(overallstats.keys())[0]
        #data[skill_type][used_model_name[model_name]] = {}
        overallstats = overallstats[model_name]["skillreuse_zs"]["skill_data"]

        used_success = round((overallstats["skillusageturns"]["skill_avail_used"]["overall"]["successrate"] + overallstats["skillusageturns"]["skill_notavail_used"]["overall"]["successrate"]) / 2, 2)
        not_used_success = round((overallstats["skillusageturns"]["skill_avail_notused"]["overall"]["successrate"] + overallstats["skillusageturns"]["skill_notavail_notused"]["overall"]["successrate"]) / 2, 2)

        used_available = round((overallstats["skillusageturns"]["skill_avail_used"]["overall"]["count"]/overallstats["skillusageturns"]["total_eps_used_skill"]), 2)
        used_generated = round((overallstats["skillusageturns"]["skill_notavail_used"]["overall"]["count"]/overallstats["skillusageturns"]["total_eps_used_skill"]), 2)

        not_used_available = round((overallstats["skillusageturns"]["skill_avail_notused"]["overall"]["count"]/overallstats["skillusageturns"]["total_eps_not_used_skill"]), 2)
        not_used_unavailable = round((overallstats["skillusageturns"]["skill_notavail_notused"]["overall"]["count"]/overallstats["skillusageturns"]["total_eps_not_used_skill"]), 2)

        skill_avail_used_rate = overallstats["skillusageturns"]["skill_avail_used_rate"]

        if skill_type not in data["success_data"]:
            data["success_data"][skill_type] = {}

        data["success_data"][skill_type][used_model_name[model_name]] = (used_success, not_used_success)
        data["skillsused"][skill_type][used_model_name[model_name]] = skill_avail_used_rate*100

        data["skillactuals"][skill_type][used_model_name[model_name]] = (used_available*100, used_generated*100)

        """
        data[skill_type][used_model_name[model_name]] = {
            "used_success": used_success,
            "not_used_success": not_used_success,
            "used_available": used_available,
            "used_generated": used_generated,
            "not_used_available": not_used_available,
            "not_used_unavailable": not_used_unavailable
        }
        """
    print(data)

    #plotdata(base_dir_list[0], data, "skillusagestats.png")
    #plot_success_rate(base_dir_list[0], data, "skillusagesuccessrate.png")
    plot_multiple_subplots(base_dir_list[0], data, "skillreuseallstats.png")

if __name__ == "__main__":
    base_dir_list = ["rp_clpskills_clp_4",
                     "rp_clpskills_gpt_clp_4",
                     "rp_clpskills_gpt_4",
                     "rp_clpskills_clp_gpt_4",
                     "rp_gptskills_clp_4",
                     "rp_gptskills_gpt_clp_4",
                     "rp_gptskills_gpt_4",
                     "rp_gptskills_clp_gpt_4"
                    ]
    run(base_dir_list)
