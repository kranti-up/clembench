import os
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from utils.prepareasciirep import PrepareASCIIRep


def read_json_file(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None

def isinstanceinfoavailable(episode_path):
    interactions_path = os.path.join(episode_path, "interactions.json")
    if os.path.exists(interactions_path):
        return True
    return False

def _prepare_instance_info(episode_path):
    interaction_data = {}
    interactions_path = os.path.join(episode_path, "interactions.json")
    if os.path.exists(interactions_path):
        interactions = read_json_file(interactions_path) or {}      

        interaction_data["overall_success"] = interactions["Success"]
        interaction_data["overall_abort"] = interactions["Aborted"]
        interaction_data["overall_loss"] = interactions["Lose"]                

        ev = interactions.get("Evaluation", {})
        interaction_data["reconst_success"] = ev["reconstruction_status"]
        interaction_data["optim_success"] = ev["optim_success"]

        boardinfo = ev["boardinfo"]["simple"]
        interaction_data["reconst_gt_code_board"] = {"function": boardinfo["code"]["single_turn"]["function"],
                        "usage": boardinfo["code"]["single_turn"]["usage"],}
        interaction_data["comboname"] = boardinfo["combo_name"]

        instruct_code_pairs = ev["reconst_genresponse"]["inst_code_pairs"]
        fseqcode = ""
        if instruct_code_pairs:
            for icode in instruct_code_pairs:
                if icode["status"] == "code":
                    fseqcode+=f'\n{icode["details"]}'
        interaction_data["reconst_gen_code"] = fseqcode

        if interaction_data["optim_success"]:
            interaction_data["optimized_function"] = ev["optim_genresponse"]["optimized_function"]
        else:
            interaction_data["optimized_function"] = None

        return interaction_data
    else:
        return None



def process_episode(episode_path: str, statsdict) -> Dict[str, Any]:
    interavail = isinstanceinfoavailable(episode_path)
    if not interavail:
        return

    interdata = _prepare_instance_info(episode_path)
    if not interdata:
        return

    if interdata["overall_success"] != (interdata["reconst_success"] and interdata["optim_success"]):
        print(f"Difference between overall success and reconst success flag for episode: {episode_num}")
        input()

    if not interdata["overall_success"]:
        #Not a successful episode, no need to verify
        return

    if interdata["optimized_function"] is None:
        print(f"Somethign wrong with optimized data, optimization is success but no optimized function is available")
        input()

    episode_num = episode_path.split("/")[-1]

    #Episode is success, so reconst and optim both are successful
    gtboard_code = interdata["reconst_gt_code_board"]
    reconst_code = interdata["reconst_gen_code"]
    optim_code = interdata["optimized_function"]
    optim_code_mod = {"function": optim_code, "usage": gtboard_code["usage"]}
    boardsize = {"rows": 8, "cols": 8}

    pascii = PrepareASCIIRep()

    gtboard_cells = pascii.get_occupied_cells(gtboard_code, boardsize)
    board, error, code_stats = pascii.execute_generated_response(reconst_code, boardsize,None)
    if error:
        print(f"Reconst board execution lead to failure for episode: {episode_num}")
        print(reconst_code)
        input()

    reconstboard_cells = pascii.get_ascii_representation_from_board_forvalidation(board, boardsize)
    optimboard_cells = pascii.get_occupied_cells(optim_code_mod, boardsize)

    if gtboard_cells != reconstboard_cells:
        print(f"GTBoard not matching with Reconst Board for episode: {episode_num} ")
        statsdict["mismatch"]["gt_reconst_mismatch"].append({"episode": episode_num, "gt_code":gtboard_code, "reconst_code":reconst_code})

    if gtboard_cells != optimboard_cells:
        print(f"GTBoard not matching with Optim Board for episode: {episode_num} ")
        statsdict["mismatch"]["gt_optim_mismatch"].append({"episode": episode_num, "gt_code":gtboard_code, "optim_code":optim_code_mod})

    if reconstboard_cells != reconstboard_cells:
        print(f"Reconst Board not matching with Optim Board for episode: {episode_num} ")
        statsdict["mismatch"]["reconst_optim_mismatch"].append({"episode": episode_num, "reconst_code":reconst_code, "optim_code":optim_code_mod})

    #if interdata["comboname"] in ["bhwbv"]:#, "bhwbvw", "bhbvbvwn", "bvbhbhnw"]:
    #    print(gtboard_cells)
    #    print(reconstboard_cells)
    #    print(optimboard_cells)
    #    print(gtboard_code["usage"])
    #    input()



def compute_scores(base_dir: str, verbose: bool = True) -> Dict[str, Any]:

    results: Dict[str, Any] = {}

    for model in os.listdir(base_dir):
        model_path = os.path.join(base_dir, model)
        if not os.path.isdir(model_path):
            continue

        for game in os.listdir(model_path):
            game_path = os.path.join(model_path, game)
            if not os.path.isdir(game_path):
                continue
            results.setdefault(game, {})
            results[game].setdefault(model, {})

            for exp in os.listdir(game_path):
                exp_path = os.path.join(game_path, exp)
                if not os.path.isdir(exp_path):
                    continue
                results[game][model].setdefault(exp, {})

                episodes = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
                num_episodes = len(episodes)
                expstats = {"mismatch":{"gt_reconst_mismatch":[],"gt_optim_mismatch":[],"reconst_optim_mismatch":[]},}

                for episode in episodes:
                    episode_path = os.path.join(exp_path, episode)
                    process_episode(episode_path, expstats)

                results[game][model][exp] = {"mismatch": expstats["mismatch"],}

    with open(f"{base_dir}/codemismatch.json", 'w', encoding='utf-8') as file:
        json.dump(results, file, indent=4)


def main():
    parser = argparse.ArgumentParser(description="Compute overall scores from experiment directories")
    parser.add_argument("base_dir", nargs="?", default="/home/admin/Desktop/codebase/cocobots/testimageccbts_local/clemnew/clembench/skillreconstruct/rskills_clp_2", help="Base directory containing model results")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose printing")
    args = parser.parse_args()

    compute_scores(args.base_dir, verbose=not args.quiet)


if __name__ == "__main__":
    main()