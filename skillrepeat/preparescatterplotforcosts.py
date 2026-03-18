import matplotlib.pyplot as plt
import numpy as np
import json



def readfile(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def plotdata(base_dir, data, filename, use_markers=True):
    print(data)
    #input()

    plt.figure()

    ax = plt.gca()
    ax.grid(True, alpha=0.15)
    ax.set_axisbelow(True)    
    ax.spines['top'].set_visible(False)

    markers = ['*', 'o', '^']
    size_map = {"^":70, "o":70, "D":60}
    #for group, points in data.items():
    for (group, points), marker in zip(data.items(), markers):    
        costs = [p[2] for p in points]
        success = [p[1] for p in points]
        #plt.scatter(costs, success, label=group)
        plt.scatter(costs, success, label=group, marker=marker, s=60, linewidths=0.3, zorder=3)
        """
        for name, succ, cost in points:
            plt.annotate(name, (cost, succ), fontsize=8)
        """
        if use_markers:
            for name, succ, cost in points:
                plt.annotate(name, (cost, succ), fontsize=3)        

    plt.xlabel("Token Cost ($)")
    plt.ylabel("Success Rate")
    plt.ylim(0.0, 1.0)
    plt.grid(True)
    #plt.legend(bbox_to_anchor=(1.02, 0.5), loc="upper left", title="Skill Type")
    plt.tight_layout()
    plt.savefig(f"{base_dir}/{filename}", dpi=300, bbox_inches='tight')
    plt.savefig(f"{base_dir}/{filename.replace('.png', '.pdf')}", dpi=300, bbox_inches='tight')    
    plt.close()


def runalltogether(base_dir_list):

    data = {"No Skills": [], "Qwen Skills": [], "Codex Skills": []}

    datastats_noskill_clp = readfile(base_dir_list[0] + "/overallstats.json")
    coststats_noskill_clp = readfile(base_dir_list[0] + "/costinfo.json")
    data["No Skills"].append(("QC", datastats_noskill_clp["skillrepeat"]["clp-chat-2-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_noskill_clp["clp-chat-2-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))


    datastats_noskill_gpt = readfile(base_dir_list[1] + "/overallstats.json")
    coststats_noskill_gpt = readfile(base_dir_list[1] + "/costinfo.json")
    data["No Skills"].append(("GC", datastats_noskill_gpt["skillrepeat"]["upgpt-codex-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_noskill_gpt["upgpt-codex-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))


    datastats_noskill_clp_gpt = readfile(base_dir_list[2] + "/overallstats.json")
    coststats_noskill_clp_gpt = readfile(base_dir_list[2] + "/costinfo.json")
    data["No Skills"].append(("QC-GC", datastats_noskill_clp_gpt["skillrepeat"]["clp-chat-2-t0.0--upgpt-codex-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_noskill_clp_gpt["clp-chat-2-t0.0--upgpt-codex-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))


    datastats_noskill_gpt_clp = readfile(base_dir_list[3] + "/overallstats.json")
    coststats_noskill_gpt_clp = readfile(base_dir_list[3] + "/costinfo.json")
    data["No Skills"].append(("GC-QC", datastats_noskill_gpt_clp["skillrepeat"]["upgpt-codex-t0.0--clp-chat-2-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_noskill_gpt_clp["upgpt-codex-t0.0--clp-chat-2-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))    

    datastats_clpskill_clp = readfile(base_dir_list[4] + "/overallstats.json")
    coststats_clpskill_clp = readfile(base_dir_list[4] + "/costinfo.json")
    data["Qwen Skills"].append(("QC", datastats_clpskill_clp["skillrepeat"]["clp-chat-2-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_clpskill_clp["clp-chat-2-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))


    datastats_clpskill_clp_gpt = readfile(base_dir_list[5] + "/overallstats.json")
    coststats_clpskill_clp_gpt = readfile(base_dir_list[5] + "/costinfo.json")
    data["Qwen Skills"].append(("QC-GC", datastats_clpskill_clp_gpt["skillrepeat"]["clp-chat-2-t0.0--upgpt-codex-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_clpskill_clp_gpt["clp-chat-2-t0.0--upgpt-codex-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))


    datastats_clpskill_gpt_clp = readfile(base_dir_list[6] + "/overallstats.json")
    coststats_clpskill_gpt_clp = readfile(base_dir_list[6] + "/costinfo.json")
    data["Qwen Skills"].append(("GC-QC", datastats_clpskill_gpt_clp["skillrepeat"]["upgpt-codex-t0.0--clp-chat-2-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_clpskill_gpt_clp["upgpt-codex-t0.0--clp-chat-2-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))


    datastats_clpskill_gpt = readfile(base_dir_list[7] + "/overallstats.json")
    coststats_clpskill_gpt = readfile(base_dir_list[7] + "/costinfo.json")
    data["Qwen Skills"].append(("GC", datastats_clpskill_gpt["skillrepeat"]["upgpt-codex-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_clpskill_gpt["upgpt-codex-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))




    datastats_gptskill_clp = readfile(base_dir_list[8] + "/overallstats.json")
    coststats_gptskill_clp = readfile(base_dir_list[8] + "/costinfo.json")
    data["Codex Skills"].append(("QC", datastats_gptskill_clp["skillrepeat"]["clp-chat-2-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_gptskill_clp["clp-chat-2-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))

    datastats_gptskill_clp_gpt = readfile(base_dir_list[9] + "/overallstats.json")
    coststats_gptskill_clp_gpt = readfile(base_dir_list[9] + "/costinfo.json")
    data["Codex Skills"].append(("QC-GC", datastats_gptskill_clp_gpt["skillrepeat"]["clp-chat-2-t0.0--upgpt-codex-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_gptskill_clp_gpt["clp-chat-2-t0.0--upgpt-codex-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))

    datastats_gptskill_gpt_clp = readfile(base_dir_list[10] + "/overallstats.json")
    coststats_gptskill_gpt_clp = readfile(base_dir_list[10] + "/costinfo.json")
    data["Codex Skills"].append(("GC-QC", datastats_gptskill_gpt_clp["skillrepeat"]["upgpt-codex-t0.0--clp-chat-2-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_gptskill_gpt_clp["upgpt-codex-t0.0--clp-chat-2-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))


    datastats_gptskill_gpt = readfile(base_dir_list[11] + "/overallstats.json")
    coststats_gptskill_gpt = readfile(base_dir_list[11] + "/costinfo.json")
    data["Codex Skills"].append(("GC", datastats_gptskill_gpt["skillrepeat"]["upgpt-codex-t0.0"]["skillrepeat_zs"]["overall_stats"]["successrate"], coststats_gptskill_gpt["upgpt-codex-t0.0"]["skillrepeat"]["skillrepeat_zs"]["overall"]["total_cost"]))

    plotdata(base_dir_list[0], data, "all_skills_cost_scatter_plot.png", False)


def run(base_dir_list, noskills=None, gptskills=False):

    if not noskills:
        datastats_noskill_clp = readfile(base_dir_list[0] + "/overallstats.json")
        coststats_noskill_clp = readfile(base_dir_list[0] + "/costinfo.json")
        datastats_noskill_gpt = readfile(base_dir_list[1] + "/overallstats.json")
        coststats_noskill_gpt = readfile(base_dir_list[1] + "/costinfo.json")

    datastats_clpskill_clp = readfile(base_dir_list[2] + "/overallstats.json")
    coststats_clpskill_clp = readfile(base_dir_list[2] + "/costinfo.json")

    datastats_clpskill_clp_gpt = readfile(base_dir_list[3] + "/overallstats.json")
    coststats_clpskill_clp_gpt = readfile(base_dir_list[3] + "/costinfo.json")
    datastats_clpskill_gpt_clp = readfile(base_dir_list[4] + "/overallstats.json")
    coststats_clpskill_gpt_clp = readfile(base_dir_list[4] + "/costinfo.json")

    datastats_clpskill_gpt = readfile(base_dir_list[5] + "/overallstats.json")
    coststats_clpskill_gpt = readfile(base_dir_list[5] + "/costinfo.json")

    if not noskills:
        if not gptskills:
            skill_type = "Qwen3 Skills"
            filename = "qwenskills_cost_scatter_plot.png"
        else:
            skill_type = "Codex Skills"
            filename = "gptskills_cost_scatter_plot.png"
        data = {"No Skills": [], f"{skill_type}": []}

        data["No Skills"].append(("Qwen3", datastats_noskill_clp["skillrepeat"]["clp-chat-2-t0.0"]["skillrepeat_zs"]["skill_data"]["noskilldata"]["clp"]["success"], coststats_noskill_clp["clp-chat-2-t0.0"]["skillrepeat"]["skillrepeat_zs"]["noskills_clp"]["total_cost"]))
        data["No Skills"].append(("Codex", datastats_noskill_gpt["skillrepeat"]["upgpt-codex-t0.0"]["skillrepeat_zs"]["skill_data"]["noskilldata"]["gpt"]["success"], coststats_noskill_gpt["upgpt-codex-t0.0"]["skillrepeat"]["skillrepeat_zs"]["noskills_clp"]["total_cost"]))

        data[f"{skill_type}"].append(("Qwen3", datastats_clpskill_clp["skillrepeat"]["clp-chat-2-t0.0"]["skillrepeat_zs"]["skill_data"]["skillavaildata"]["success"], coststats_clpskill_clp["clp-chat-2-t0.0"]["skillrepeat"]["skillrepeat_zs"]["skills_avail"]["total_cost"]))
        data[f"{skill_type}"].append(("Qwen3-Codex", datastats_clpskill_clp_gpt["skillrepeat"]["clp-chat-2-t0.0--upgpt-codex-t0.0"]["skillrepeat_zs"]["skill_data"]["skillavaildata"]["success"], coststats_clpskill_clp_gpt["clp-chat-2-t0.0--upgpt-codex-t0.0"]["skillrepeat"]["skillrepeat_zs"]["skills_avail"]["total_cost"]))
        data[f"{skill_type}"].append(("Codex-Qwen3", datastats_clpskill_gpt_clp["skillrepeat"]["upgpt-codex-t0.0--clp-chat-2-t0.0"]["skillrepeat_zs"]["skill_data"]["skillavaildata"]["success"], coststats_clpskill_gpt_clp["upgpt-codex-t0.0--clp-chat-2-t0.0"]["skillrepeat"]["skillrepeat_zs"]["skills_avail"]["total_cost"]))
        data[f"{skill_type}"].append(("Codex", datastats_clpskill_gpt["skillrepeat"]["upgpt-codex-t0.0"]["skillrepeat_zs"]["skill_data"]["skillavaildata"]["success"], coststats_clpskill_gpt["upgpt-codex-t0.0"]["skillrepeat"]["skillrepeat_zs"]["skills_avail"]["total_cost"]))

        plotdata(base_dir_list[0], data, filename)

    else:
        if noskills["clp"]:
            filename = "no_clp_skills_cost_scatter_plot.png"
        else:
            filename = "no_gpt_skills_cost_scatter_plot.png"        
        data = {"No Skills": []}
        data["No Skills"].append(("Qwen3", datastats_clpskill_clp["skillrepeat"]["clp-chat-2-t0.0"]["skillrepeat_zs"]["skill_data"]["skillnonavaildata"]["success"], coststats_clpskill_clp["clp-chat-2-t0.0"]["skillrepeat"]["skillrepeat_zs"]["skills_notavail"]["total_cost"]))
        data["No Skills"].append(("Qwen3-Codex", datastats_clpskill_clp_gpt["skillrepeat"]["clp-chat-2-t0.0--upgpt-codex-t0.0"]["skillrepeat_zs"]["skill_data"]["skillnonavaildata"]["success"], coststats_clpskill_clp_gpt["clp-chat-2-t0.0--upgpt-codex-t0.0"]["skillrepeat"]["skillrepeat_zs"]["skills_notavail"]["total_cost"]))
        data["No Skills"].append(("Codex-Qwen3", datastats_clpskill_gpt_clp["skillrepeat"]["upgpt-codex-t0.0--clp-chat-2-t0.0"]["skillrepeat_zs"]["skill_data"]["skillnonavaildata"]["success"], coststats_clpskill_gpt_clp["upgpt-codex-t0.0--clp-chat-2-t0.0"]["skillrepeat"]["skillrepeat_zs"]["skills_notavail"]["total_cost"]))
        data["No Skills"].append(("Codex", datastats_clpskill_gpt["skillrepeat"]["upgpt-codex-t0.0"]["skillrepeat_zs"]["skill_data"]["skillnonavaildata"]["success"], coststats_clpskill_gpt["upgpt-codex-t0.0"]["skillrepeat"]["skillrepeat_zs"]["skills_notavail"]["total_cost"]))

        plotdata(base_dir_list[0], data, filename)




if __name__ == "__main__":
    """
    base_dir_list = ["rp_noskills_clp_4",
    "rp_noskills_gpt_4",
        "rp_clpskills_clp_4",
        "rp_clpskills_clp_gpt_4",
        "rp_clpskills_gpt_clp_4",
        "rp_clpskills_gpt_4",
                ]
    run(base_dir_list, {"clp":True, "gpt":False}, False)
    run(base_dir_list, None, False)
    base_dir_list[2] = "rp_gptskills_clp_4"
    base_dir_list[3] = "rp_gptskills_clp_gpt_4"
    base_dir_list[4] = "rp_gptskills_gpt_clp_4"
    base_dir_list[5] = "rp_gptskills_gpt_4"
    run(base_dir_list, None, True)    
    run(base_dir_list, {"clp":False, "gpt":True}, True)
    """
    base_dir_list = ["rp_noskills_clp_4",
    "rp_noskills_gpt_4",
    "rp_noskills_clp_gpt_4",
    "rp_noskills_gpt_clp_4",
        "rp_clpskills_clp_4",
        "rp_clpskills_clp_gpt_4",
        "rp_clpskills_gpt_clp_4",
        "rp_clpskills_gpt_4",
        "rp_gptskills_clp_4",
        "rp_gptskills_clp_gpt_4",
        "rp_gptskills_gpt_clp_4",
        "rp_gptskills_gpt_4",
                ]
    runalltogether(base_dir_list)
