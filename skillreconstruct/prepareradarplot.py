import matplotlib.pyplot as plt
import numpy as np
import json



def readfile(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def plotdata(base_dir, qwendata, gptdata):
    # 1) Radar plot: Reconstruction / Optimization | Reconstruction Task / Overall
    labels = ["Reconstruction", "Optimization | Reconstruction Task", "Overall"]
    #qwen = [0.685, 0.929, 0.636]
    #gpt = [0.933, 1.0, 0.933]

    qwen_closed = qwendata + qwendata[:1]
    gpt_closed = gptdata + gptdata[:1]
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    plt.figure()
    ax = plt.subplot(111, polar=True)
    ax.tick_params(axis='y', labelsize=14)
    ax.plot(angles, qwen_closed, marker="o", label="Qwen3-Coder")
    ax.plot(angles, gpt_closed, marker="s", label="GPT5.2-Codex")
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=14)
    ax.set_ylim(0, 1.05)
    plt.legend(bbox_to_anchor=(1.15, 1.1), fontsize=12)
    plt.tight_layout()
    #plt.show()
    plt.savefig(f"{base_dir}/radar_plot.png", dpi=300)
    plt.savefig(f"{base_dir}/radar_plot.pdf", bbox_inches="tight", dpi=300)
    plt.close()


def plotoptim(base_dir, qwen_opt, gpt_opt):
    #metrics = ["Has FN?", "Has Loop?", "Reduced put()", "Reduced byte len"]
    metrics = [    "Function\nDefinition",
    "Loop\nUsage",
    "Reduced\nPrimitive Code",
    "Reduced\nByte Length"]
    #qwen_opt = [1.00, 0.71, 0.73, 0.18]
    #gpt_opt  = [1.00, 1.00, 1.00, 0.48]

    x = np.arange(len(metrics))
    offset = 0.04
    x_qwen = x - offset
    x_gpt = x + offset

    plt.figure()
    for i in range(len(metrics)):
        plt.plot([x_qwen[i], x_gpt[i]], [qwen_opt[i], gpt_opt[i]], linewidth=1)
    plt.scatter(x_qwen, qwen_opt, marker="o", label="Qwen3-Coder")
    plt.scatter(x_gpt, gpt_opt, marker="s", label="GPT5.2-Codex")
    plt.xticks(x, metrics, fontsize=11)
    plt.ylabel("Success Rate", fontsize=14)
    plt.xlabel("Optimization Metric", fontsize=14)
    plt.ylim(0, 1.05)
    plt.yticks(fontsize=12)
    plt.grid(axis="y", linewidth=0.5, alpha=0.4)
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, fontsize=12)
    #plt.title("Optimization Metric Success")
    plt.tight_layout()
    #plt.show()    
    plt.savefig(f"{base_dir}/optim_plot.png", dpi=300)
    plt.savefig(f"{base_dir}/optim_plot.pdf", bbox_inches="tight", dpi=300)
    plt.close()    


def run(base_dir_clp, base_dir_gpt):
    datastats_clp = readfile(base_dir_clp + "/overallstats.json")
    optim_clp = readfile(base_dir_clp + "/overall_optimal_results.json")
    datastats_gpt = readfile(base_dir_gpt + "/overallstats.json")
    optim_gpt = readfile(base_dir_gpt + "/overall_optimal_results.json")

    if not datastats_clp or not datastats_gpt:
        print("Error: Could not read overall_stats.json from one or both directories.")
        return

    qwendata = [
        datastats_clp["skillreconstruct"]["clp-chat-2-t0.0"]["skillreconst_zs"]["reconst_optim_stats"]["reconst_success_rate"],
        datastats_clp["skillreconstruct"]["clp-chat-2-t0.0"]["skillreconst_zs"]["reconst_optim_stats"]["optim_success_rate"],
        datastats_clp["skillreconstruct"]["clp-chat-2-t0.0"]["skillreconst_zs"]["overall_stats"]["successrate"]
    ]

    qwenopt = [
        optim_clp["skillreconstruct"]["clp-chat-2-t0.0"]["skillreconst_zs"]["func name rate"],
        optim_clp["skillreconstruct"]["clp-chat-2-t0.0"]["skillreconst_zs"]["func_loop_rate"],
        optim_clp["skillreconstruct"]["clp-chat-2-t0.0"]["skillreconst_zs"]["func_less_putcalls_rate"],
        optim_clp["skillreconstruct"]["clp-chat-2-t0.0"]["skillreconst_zs"]["func_less_bytelen_rate"]
    ]

    gptdata = [
        datastats_gpt["skillreconstruct"]["upgpt-codex-t0.0"]["skillreconst_zs"]["reconst_optim_stats"]["reconst_success_rate"],
        datastats_gpt["skillreconstruct"]["upgpt-codex-t0.0"]["skillreconst_zs"]["reconst_optim_stats"]["optim_success_rate"],
        datastats_gpt["skillreconstruct"]["upgpt-codex-t0.0"]["skillreconst_zs"]["overall_stats"]["successrate"]
    ]

    gptopt = [
        optim_gpt["skillreconstruct"]["upgpt-codex-t0.0"]["skillreconst_zs"]["func name rate"],
        optim_gpt["skillreconstruct"]["upgpt-codex-t0.0"]["skillreconst_zs"]["func_loop_rate"],
        optim_gpt["skillreconstruct"]["upgpt-codex-t0.0"]["skillreconst_zs"]["func_less_putcalls_rate"],
        optim_gpt["skillreconstruct"]["upgpt-codex-t0.0"]["skillreconst_zs"]["func_less_bytelen_rate"]
    ]    

    #plotdata(base_dir_clp, qwendata, gptdata)

    plotoptim(base_dir_clp, qwenopt, gptopt)

if __name__ == "__main__":
    base_dir_clp = "rskills_clp_2"
    base_dir_gpt = "rskills_gpt_2"
    run(base_dir_clp, base_dir_gpt)    

