import matplotlib.pyplot as plt
import numpy as np
import json

class PrepareLinePlot:
    def __init__(self):
        pass

    def readfile(self, filepath):
        with open(filepath, "r") as f:
            return json.load(f)        


    def plotdata(self, base_dir, clar_data, corr_data, success_data, turns_data):
        elements = [2, 3, 4, 5]

        clar_data["Qwen3-Coder"] = clar_data["Qwen3"]
        clar_data["GPT5.2-Codex"] = clar_data["Codex"]
        clar_data.pop("Qwen3")
        clar_data.pop("Codex")

        corr_data["Qwen3-Coder"] = corr_data["Qwen3"]
        corr_data["GPT5.2-Codex"] = corr_data["Codex"]
        corr_data.pop("Qwen3")
        corr_data.pop("Codex")


        success_data["Qwen3-Coder"] = success_data["Qwen3"]
        success_data["GPT5.2-Codex"] = success_data["Codex"]
        success_data.pop("Qwen3")
        success_data.pop("Codex")


        if turns_data:
            turns_data["Qwen3-Coder"] = turns_data["Qwen3"]
            turns_data["GPT5.2-Codex"] = turns_data["Codex"]
            turns_data.pop("Qwen3")
            turns_data.pop("Codex")


        model_colors = {
            "Qwen3-Coder": "tab:blue",
            "GPT5.2-Codex": "tab:orange"
        }

        markers = {
            "Qwen3-Coder": "o",
            "GPT5.2-Codex": "s"
        }

        if turns_data:
            fig, axes = plt.subplots(2, 2, figsize=(12,9))#, sharey=True)
        else:
            fig, axes = plt.subplots(1, 3, figsize=(16, 5))#, sharey=True)

        def plot_metric(ax, data, title, linestyle="-", linewidth=2):
            for model, yvals in data.items():
                xvals = elements[:len(yvals)]
                ax.plot(
                    xvals, yvals,
                    linestyle=linestyle,
                    marker=markers[model],
                    color=model_colors[model],
                    linewidth=linewidth,
                    label=model
                )
            ax.set_title(title, fontsize=12)
            ax.set_xlabel("Number of Elements/Object", fontsize=12)
            ax.set_xticks(elements)
            ax.set_ylim(0, 1.05)
            ax.set_ylabel("Fraction of Episodes", fontsize=12)
            ax.tick_params(axis='both', labelsize=12)            
            ax.grid(axis="y", linewidth=0.5, alpha=0.4)

        def plot_success_metric(ax, data, title, linestyle="-", linewidth=2):
            for model, yvals in data.items():
                xvals = elements[:len(yvals)]
                ax.plot(
                    xvals, yvals,
                    linestyle=linestyle,
                    marker=markers[model],
                    color=model_colors[model],
                    linewidth=linewidth,
                    label=model
                )
            ax.set_title(title, fontsize=12)
            ax.set_xlabel("Number of Elements/Object", fontsize=12)
            ax.set_xticks(elements)
            ax.set_ylim(0, 1.05)
            ax.set_ylabel("Overall success rate", fontsize=12)
            ax.tick_params(axis='both', labelsize=12)            
            ax.grid(axis="y", linewidth=0.5, alpha=0.4)            

        def plot_turns_metric(ax, data, title, linestyle="-"):
            for model, yvals in data.items():
                xvals = elements[:len(yvals)]
                ax.plot(
                    xvals, yvals,
                    linestyle=linestyle,
                    marker=markers[model],
                    color=model_colors[model],
                    linewidth=2,
                    label=model
                )
            ax.set_title(title)
            ax.set_xlabel("Number of Elements/Object")
            ax.set_xticks(elements)
            ax.grid(axis="y", linewidth=0.5, alpha=0.4)            

        if turns_data:
            plot_metric(axes[0,0], clar_data, "Clarification", linestyle=":", linewidth=2)
            plot_metric(axes[0,1], corr_data, "Correction", linestyle="-", linewidth=2)
            plot_metric(axes[1,0], success_data, "Success Rate", linestyle="--", linewidth=2)
            plot_turns_metric(axes[1,1], turns_data, "Average Turns (Success)", linestyle="-")

            axes[0,0].set_ylabel("Fraction of Episodes")
            axes[1,0].set_ylabel("Value")

            handles, labels = axes[0,0].get_legend_handles_labels()
            fig.legend(handles, labels, loc="upper center", ncol=2, fontsize=12)
        else:
            plot_metric(axes[0], clar_data, "Clarification Rate", linestyle=":", linewidth=2)
            plot_metric(axes[1], corr_data, "Correction Rate", linestyle="-", linewidth=2)
            #plot_metric(axes[2], success_data, "Success Rate", linestyle="-", linewidth=2)
            plot_success_metric(axes[2], success_data, "Success Rate", linestyle="-", linewidth=2)
            #axes[0].set_ylabel("Fraction of Episodes")

            handles, labels = axes[0].get_legend_handles_labels()
            fig.legend(handles, labels, loc="upper center", ncol=2, fontsize=12)

        plt.tight_layout(rect=[0,0,1,0.9])
        plt.savefig(f"{base_dir}/dialogue_stats_human.png", dpi=300, bbox_inches='tight')
        plt.savefig(f"{base_dir}/dialogue_stats_human.pdf", dpi=300, bbox_inches='tight')
        plt.close()

    def run(self, base_dir_clp, base_dir_gpt):
        datastats_clp = self.readfile(base_dir_clp + "/overallstats.json")
        datastats_gpt = self.readfile(base_dir_gpt + "/overallstats.json")

        if not datastats_clp or not datastats_gpt:
            print("Error: Could not read overall_stats.json from one or both directories.")
            return

        element_counts = [10,34,73,48]


        qwendata = [
            datastats_clp["skillreconstruct"]["clp-chat-2-t0.0"]["skillreconst_zs"]["clarifications"]["details"]["cfq_counts_per_shape"],
            datastats_clp["skillreconstruct"]["clp-chat-2-t0.0"]["skillreconst_zs"]["corrections"]["details"]["corr_counts_per_shape"],
            datastats_clp["skillreconstruct"]["clp-chat-2-t0.0"]["skillreconst_zs"]["shape_stats"]["overall"]
        ]
        qwenturns = []
        for numshape in ["2","3","4","5"]:
            qwenturns.append(datastats_clp["skillreconstruct"]["clp-chat-2-t0.0"]["skillreconst_zs"]["shape_stats"][numshape]["success"]["reconst"]["average"])


        """
        gptdata = [
            datastats_gpt["skillreconstruct"]["upgpt-codex-t0.0"]["skillreconst_zs"]["clarifications"]["details"]["cfq_counts_per_shape"],
            datastats_gpt["skillreconstruct"]["upgpt-codex-t0.0"]["skillreconst_zs"]["corrections"]["details"]["corr_counts_per_shape"],
            datastats_gpt["skillreconstruct"]["upgpt-codex-t0.0"]["skillreconst_zs"]["shape_stats"]["overall"]
        ]
        """        
        gptdata = [
            datastats_gpt["skillreconstruct"]["human-t0.0--clp-chat-2-t0.0"]["skillreconst_zs"]["clarifications"]["details"]["cfq_counts_per_shape"],
            datastats_gpt["skillreconstruct"]["human-t0.0--clp-chat-2-t0.0"]["skillreconst_zs"]["corrections"]["details"]["corr_counts_per_shape"],
            datastats_gpt["skillreconstruct"]["human-t0.0--clp-chat-2-t0.0"]["skillreconst_zs"]["shape_stats"]["overall"]
        ]



        gptturns = []
        for numshape in ["2","3","4","5"]:
            #gptturns.append(datastats_gpt["skillreconstruct"]["upgpt-codex-t0.0"]["skillreconst_zs"]["shape_stats"][numshape]["success"]["reconst"]["average"])
            gptturns.append(datastats_gpt["skillreconstruct"]["human-t0.0--clp-chat-2-t0.0"]["skillreconst_zs"]["shape_stats"][numshape]["success"]["reconst"]["average"])



        for i in range(3):
            for data in [qwendata, gptdata]:
                for j in range(2):
                    data[i] = {int(k): v for k,v in data[i].items()}


        #Sort the dictionary based on the keys
        qwendata[0] = dict(sorted(qwendata[0].items()))
        qwendata[1] = dict(sorted(qwendata[1].items()))
        qwendata[2] = dict(sorted(qwendata[2].items()))
        gptdata[0] = dict(sorted(gptdata[0].items()))
        gptdata[1] = dict(sorted(gptdata[1].items()))
        #gptdata[1] = {2:0,3:0,4:gptdata[1][4],5:0}
        gptdata[2] = dict(sorted(gptdata[2].items()))

        clar_qwen_rate = [round(c/t, 2) for c,t in zip(qwendata[0].values(), element_counts)]
        clar_gpt_rate  = [round(c/t, 2) for c,t in zip(gptdata[0].values(), element_counts)]

        corr_qwen_rate = [round(c/t, 2) for c,t in zip(qwendata[1].values(), element_counts)]
        corr_gpt_rate  = [round(c/t, 2) for c,t in zip(gptdata[1].values(), element_counts)]
 

        success_qwen_rate = [c for c,t in zip(qwendata[2].values(), element_counts)]
        success_gpt_rate  = [c for c,t in zip(gptdata[2].values(), element_counts)]


        clar_data = {"Qwen3": clar_qwen_rate, "Codex": clar_gpt_rate}
        corr_data = {"Qwen3":corr_qwen_rate, "Codex": corr_gpt_rate}
        success_data = {"Qwen3": success_qwen_rate, "Codex": success_gpt_rate}
        turns_data = {"Qwen3": qwenturns, "Codex": gptturns}

        #self.plotdata(base_dir_clp, clar_data, corr_data, success_data, turns_data)
        self.plotdata(base_dir_clp, clar_data, corr_data, success_data, None)

if __name__ == "__main__":
    base_dir_clp = "rskills_clp_2"
    #base_dir_gpt = "rskills_gpt_2"
    base_dir_gpt = "rskills_human_2"
    plp = PrepareLinePlot()
    plp.run(base_dir_clp, base_dir_gpt)
