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

def parse_scores(scores: Dict[str, Any]) -> Tuple[Optional[float], Optional[bool]]:
    es = scores.get("episode scores", {})
    main = es.get("Main Score")
    reconst = es.get("reconstruction_status")
    return main, reconst


def process_episode(episode_path: str) -> Dict[str, Any]:
    
    stats = {"repeat_status": [],
             "overall_success": [],
             "overall_loss": [],
             "overall_abort": [],
             "num_repeat_turns": 0,
             }    
    
    interactions_path = os.path.join(episode_path, "interactions.json")
    scores_path = os.path.join(episode_path, "scores.json")



    if os.path.exists(interactions_path):
        interactions = read_json_file(interactions_path) or {}
        ev = interactions.get("Evaluation", {})        
        repeat_status = 1 if ev.get("repeat_success") == True else 0
        stats["repeat_status"].append(repeat_status)
        if interactions.get("Aborted") == True:
            stats["overall_abort"].append(1)
        elif interactions.get("Lose") == True:
            stats["overall_loss"].append(1)
        elif repeat_status == True:
            stats["overall_success"].append(1)

        stats["num_repeat_turns"] = ev.get("play_turns_repeat")

    return stats


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

                accuracy_data: List[float] = []
                failed_episodes: List[str] = []
                failed_episodes_data: List[str] = []
                aborted_episodes: List[str] = []
                repeat_success_episodes: List[int] = []
                repeat_turns: List[int] = []

                episodes = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
                num_episodes = len(episodes)

                for episode in episodes:
                    episode_path = os.path.join(exp_path, episode)
                    ep_stats = process_episode(episode_path)
                    accuracy_data.extend(ep_stats.get("overall_success", []))
                    failed_episodes.extend(ep_stats.get("overall_loss", []))     
                    if ep_stats["overall_loss"] and ep_stats["overall_loss"][0] == 1:
                        failed_episodes_data.append(episode)
                    aborted_episodes.extend(ep_stats.get("overall_abort", []))
                    repeat_success_episodes.extend(ep_stats.get("repeat_status", []))

                    if ep_stats["repeat_status"] and ep_stats["repeat_status"][0]==1:
                        repeat_turns.append(ep_stats.get("num_repeat_turns"))

                total_aborted = len(aborted_episodes)
                total_failed = len(failed_episodes)
                total_episodes = num_episodes
                total_success_episodes = total_episodes - total_aborted - total_failed
                aborted_percent = round((total_aborted / total_episodes),2) if total_episodes > 0 else 0.0
                failed_percent = round((total_failed / total_episodes),2) if total_episodes > 0 else 0.0
                success_percent = round(1.0 - aborted_percent - failed_percent,2)

                total_repeat_success = sum(repeat_success_episodes)
                repeat_rate = round((total_repeat_success / total_episodes),2) if total_episodes > 0 else 0.0


                print(f"Number of Episodes: {total_episodes}, Success: {total_success_episodes}, Aborted: {total_aborted}, Failed: {total_failed}")
                print(f"Repeat Success Rate: {repeat_rate}, Aborted: {aborted_percent}, Failed: {failed_percent}")

                min_repeat_turns, median_repeat_turns, max_repeat_turns = np.min(repeat_turns), np.median(repeat_turns), np.max(repeat_turns)
                print(f"Min Repeat turns: {min_repeat_turns}, Median Repeat turns: {median_repeat_turns}, Max Repeat turns: {max_repeat_turns}")

                #print(f"Failed Episodes: {failed_episodes_data}")


def main():
    parser = argparse.ArgumentParser(description="Compute overall scores from experiment directories")
    parser.add_argument("base_dir", nargs="?", default="/home/admin/Desktop/codebase/cocobots/testimageccbts_local/clemnew/clembench/skillrepeat/rp1_clpskills_clp", help="Base directory containing model results")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose printing")
    args = parser.parse_args()

    compute_scores(args.base_dir, verbose=not args.quiet)


if __name__ == "__main__":
    main()