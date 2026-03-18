import os
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple
import statistics
import numpy as np


def read_json_file(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def process_episode(episode_path: str) -> Dict[str, Any]:
    
    stats = {"used_cfq": False,
             "num_cfq": 0,
             "used_corrections": False,
             "num_corrections": 0,
             "num_turns": 0,
             "ep_status": False,
             }    
    
    interactions_path = os.path.join(episode_path, "interactions.json")

    if os.path.exists(interactions_path):
        interactions = read_json_file(interactions_path) or {}

        ev = interactions.get("Evaluation", None)
        if ev  is None:
            print("No Evaluation found inside interactions")
            return None

        genresp = ev.get("repeat_genresponse", None)
        if genresp is None:
            return None
        stats["used_cfq"] = genresp["used_clarification"]
        stats["num_cfq"] = genresp["num_clarifications"]
        used_remove = genresp["used_remove"]
        num_remove = genresp["num_removes"]

        used_move = genresp["used_remove"]
        num_move = genresp["num_moves"]

        used_clear = genresp["used_clear"]
        num_clear = genresp["num_clears"]        

        if used_remove or used_move or used_clear:
            stats["used_corrections"] = True

        stats["num_corrections"] = num_remove+num_move+num_clear
        stats["num_turns"] = ev["play_turns_repeat"]

        #if ev["play_turns_reconst"] == 0:
        #    print(f"0 turns in ep: {episode_path}")
        #    input()

        #if stats["num_turns"] == 0:
        #    print(f"0 turns in  stats ep: {episode_path}")
        #    input()            

        if not interactions["Success"]:
            stats["ep_status"] = False
        else:
            stats["ep_status"] = True

        return stats
    else:
        return None

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


                cfq_episodes: List[str] = []
                corr_episodes: List[str] = []
                ep_cfq_counts: List[int] = []
                ep_corr_counts: List[int] = []
                reconst_turns: List[int] = []
                

                episodes = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
                num_episodes = len(episodes)
                num_success_eps = 0
                num_failed_eps = 0

                for episode in episodes:
                    episode_path = os.path.join(exp_path, episode)
                    ep_stats = process_episode(episode_path)
                    if ep_stats is None:
                        #print(f"Skipping episode {episode_path}, received None response")
                        continue
                    
                    if ep_stats["ep_status"]:
                        use_key = "Success"
                        num_success_eps += 1
                    else:
                        use_key = "Failure"
                        num_failed_eps += 1

                    if ep_stats["used_cfq"]:
                        cfq_episodes.append({use_key: episode})

                    if ep_stats["num_cfq"]:
                        ep_cfq_counts.append({use_key: ep_stats["num_cfq"]})

                    if ep_stats["used_corrections"]:
                        corr_episodes.append({use_key: episode})                        

                    if ep_stats["num_corrections"]:
                        ep_corr_counts.append({use_key: ep_stats["num_corrections"]})

                    #if ep_stats["num_turns"] == 0:
                    #    print(f"0 turns in stats result for ep: {episode}")
                    #    input()
                    reconst_turns.append({use_key: ep_stats["num_turns"]})

                num_cfq_success_episodes = 0
                num_cfq_failure_episodes = 0
                for ep in cfq_episodes:
                    for k,v in ep.items():
                        if k == "Success":
                            num_cfq_success_episodes +=1
                        else:
                            num_cfq_failure_episodes += 1

                num_corr_success_episodes = 0
                num_corr_failure_episodes = 0
                for ep in corr_episodes:
                    for k,v in ep.items():
                        if k == "Success":
                            num_corr_success_episodes +=1
                        else:
                            num_corr_failure_episodes += 1                            
                    

                num_cfq_count_success_episodes = 0
                num_cfq_count_failure_episodes = 0
                for ep in ep_cfq_counts:
                    for k,v in ep.items():
                        if k == "Success":
                            num_cfq_count_success_episodes +=1
                        else:
                            num_cfq_count_failure_episodes += 1

                num_corr_count_success_episodes = 0
                num_corr_count_failure_episodes = 0
                for ep in ep_corr_counts:
                    for k,v in ep.items():
                        if k == "Success":
                            num_corr_count_success_episodes +=1
                        else:
                            num_corr_count_failure_episodes += 1

                print(f"num_cfq_episodes: Success {num_cfq_success_episodes}, Failure: {num_cfq_failure_episodes}")
                num_cfq_sucess_rate = round((num_cfq_success_episodes/num_success_eps),2)
                num_cfq_failure_rate = round((num_cfq_failure_episodes/num_failed_eps),2)
                print(f"num_cfq_sucess_rate: {num_cfq_sucess_rate}, num_cfq_failure_rate = {num_cfq_failure_rate}")
                
                print(f"num_corr_episodes: Success {num_corr_success_episodes}, Failure: {num_corr_failure_episodes}")
                num_corr_sucess_rate = round((num_corr_success_episodes/num_success_eps),2)
                num_corr_failure_rate = round((num_corr_failure_episodes/num_failed_eps),2)
                print(f"num_corr_sucess_rate: {num_corr_sucess_rate}, num_corr_failure_rate = {num_corr_failure_rate}")

                print(f"num_cfq_count_episodes: Success {num_cfq_count_success_episodes}, Failure: {num_cfq_count_failure_episodes}")
                num_cfq_count_sucess_rate = round((num_cfq_count_success_episodes/num_success_eps),2)
                num_cfq_count_failure_rate = round((num_cfq_count_failure_episodes/num_failed_eps),2)
                print(f"num_cfq_count_sucess_rate: {num_cfq_count_sucess_rate}, num_cfq_count_failure_rate = {num_cfq_count_failure_rate}")
                
                print(f"num_corr_count_episodes: Success {num_corr_count_success_episodes}, Failure: {num_corr_count_failure_episodes}")
                num_corr_count_sucess_rate = round((num_corr_count_success_episodes/num_success_eps),2)
                num_corr_count_failure_rate = round((num_corr_count_failure_episodes/num_failed_eps),2)
                print(f"num_corr_count_sucess_rate: {num_corr_count_sucess_rate}, num_corr_count_failure_rate = {num_corr_count_failure_rate}")

                if reconst_turns:
                    reconst_success_turns, reconst_failure_turns = [], []

                    for rtturn in reconst_turns:
                        if "Success" in rtturn:
                            reconst_success_turns.append(rtturn["Success"])
                        else:
                            reconst_failure_turns.append(rtturn["Failure"])

                    min_turns_success = min(reconst_success_turns)
                    max_turns_success = max(reconst_success_turns)
                    median_turns_success = statistics.median(reconst_success_turns)

                    min_turns_failure = min(reconst_failure_turns)
                    max_turns_failure = max(reconst_failure_turns)
                    median_turns_failure = statistics.median(reconst_failure_turns)

                    print(f"Success: min_turns: {min_turns_success}, max_turns: {max_turns_success}, median_turns: {median_turns_success}")
                    print(f"Failure: min_turns: {min_turns_failure}, max_turns: {max_turns_failure}, median_turns: {median_turns_failure}")
                else:
                    min_turns = None
                    max_turns = None
                    median_turns = None

                results[game][model][exp] = {"num_cfq_success_episodes": num_cfq_success_episodes,
                                             "num_cfq_failure_episodes": num_cfq_failure_episodes,
                                             "num_cfq_sucess_rate": num_cfq_sucess_rate,
                                             "num_cfq_failure_rate": num_cfq_failure_rate,
                                            "num_corr_success_episodes": num_corr_success_episodes,
                                            "num_corr_failure_episodes": num_corr_failure_episodes,
                                            "num_corr_sucess_rate": num_corr_sucess_rate,
                                            "num_corr_failure_rate": num_corr_failure_rate,
                                            "num_cfq_count_success_episodes": num_cfq_count_success_episodes,
                                            "num_cfq_count_failure_episodes": num_cfq_count_failure_episodes,
                                            "num_cfq_count_sucess_rate": num_cfq_count_sucess_rate,
                                            "num_cfq_count_failure_rate": num_cfq_count_failure_rate,
                                            "num_corr_count_success_episodes": num_corr_count_success_episodes,
                                            "num_corr_count_failure_episodes": num_corr_count_failure_episodes,
                                            "num_corr_count_sucess_rate": num_corr_count_sucess_rate,
                                            "num_corr_count_failure_rate":num_corr_count_failure_rate,    
                                             "cfq_episodes": cfq_episodes,
                                              "corr_episodes": corr_episodes, "reconst_turns": reconst_turns,
                                              "min_turns_success": min_turns_success, "max_turns_success": max_turns_success, "median_turns_success": median_turns_success, "min_turns_failure": min_turns_failure,
                                              "max_turns_failure": max_turns_failure, "median_turns_failure": median_turns_failure}

    with open(f"{base_dir}/overall_dialog_resuls.json", "w") as f:
        json.dump(results, f, indent=2)

                    


def main():
    parser = argparse.ArgumentParser(description="Compute overall scores from experiment directories")
    parser.add_argument("base_dir", nargs="?", default="r1", help="Base directory containing model results")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose printing")
    args = parser.parse_args()

    compute_scores(args.base_dir, verbose=not args.quiet)


if __name__ == "__main__":
    main()                    
