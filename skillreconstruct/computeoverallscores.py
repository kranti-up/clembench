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
    
def getshapesinfo(occupied_cells: dict) -> Dict[str, int]:
    """Get shape information from occupied_cells dictionary.
    
    Args:
        occupied_cells: Dictionary mapping cell coordinates to lists of elements in those cells.
    Returns:
        A dictionary with shape types as keys and their counts as values.
    """
    print(occupied_cells)

    prepascii = PrepareASCIIRep()
    shapes_list = []
    for key, value in occupied_cells.items():
        shape_info = prepascii._prepare_shape_color_dict(value, True)
        shapes_list.append(shape_info)

    print(shapes_list)



def parse_interactions(interactions: Dict[str, Any]) -> Tuple[Dict[str, Any], int, Optional[int], Optional[int], Optional[int], Optional[str]]:
    ev = interactions.get("Evaluation", {})
    reconst_gen = ev.get("reconst_genresponse", {})
    code_data = {
        "used_clarification": reconst_gen.get("used_clarification", False),
        "num_clarifications": reconst_gen.get("num_clarifications", 0),
        "used_move": reconst_gen.get("used_move", False),
        "num_moves": reconst_gen.get("num_moves", 0),
        "used_undo": reconst_gen.get("used_undo", False),
        "num_undos": reconst_gen.get("num_undos", 0),
        "used_remove": reconst_gen.get("used_remove", False),
        "num_removes": reconst_gen.get("num_removes", 0),
        "used_clear": reconst_gen.get("used_clear", False),
        "num_clears": reconst_gen.get("num_clears", 0),
        "use_dspy_reconst": ev.get("use_dspy_reconst", ev.get("use_dspy", "Not defined")),
        "use_dspy_history": ev.get("use_dspy_history", "Not defined"),
        "used_retry_reconst": reconst_gen.get("used_retry_reconst", False),
    }
    num_turns = ev.get("play_turns_reconst", interactions.get("Complete turns", 0))
    optim_turns = ev.get("play_turns_optim", 0)
    boardinfo = ev.get("boardinfo", {})
    # boardinfo may be nested under a sub-key (e.g. "simple"); unwrap if needed
    if isinstance(boardinfo, dict) and "shapes" not in boardinfo:
        # Try the first sub-key that contains a dict with "shapes"
        for val in boardinfo.values():
            if isinstance(val, dict) and "shapes" in val:
                boardinfo = val
                break
    shapes = boardinfo.get("shapes") if isinstance(boardinfo, dict) else None
    total_shapes = len(shapes) if isinstance(shapes, list) else boardinfo.get("total_shapes") if isinstance(boardinfo, dict) else None
    play_turns = interactions.get("Played turns")
    n_turns = interactions.get("n_turns")
    combo_name = boardinfo.get("combo_name")
    shapes_list = boardinfo.get("shapes")
    colors_list = boardinfo.get("colors")
    optim_success = ev.get("optim_success")
    return code_data, num_turns, optim_turns, total_shapes, play_turns, n_turns, combo_name, shapes_list, colors_list, optim_success


def parse_scores(scores: Dict[str, Any]) -> Tuple[Optional[float], Optional[bool]]:
    es = scores.get("episode scores", {})
    main = es.get("Main Score")
    reconst = es.get("reconstruction_status")
    return main, reconst


def process_episode(episode_path: str) -> Dict[str, Any]:
    stats = {
        "accuracy_vals": [],
        "failed_episodes": [],
        "aborted_episodes": [],
        "code_stats": {},
        "dialog_turns": 0,
        "optim_dialog_turns": 0,
        "total_shapes": None,
        "outcome": "unknown",
        "play_turns": None,
        "n_turns": None,
        "reconstruction_status": None,
        "optim_success": None,
    }

    interactions_path = os.path.join(episode_path, "interactions.json")
    scores_path = os.path.join(episode_path, "scores.json")

    if os.path.exists(interactions_path):
        interactions = read_json_file(interactions_path) or {}
        code_data, num_turns, optim_turns, total_shapes, play_turns, n_turns, combo_name, shapes_list_gt, colors_list_gt, optim_success = parse_interactions(interactions)
        stats["code_stats"] = code_data
        stats["dialog_turns"] = num_turns
        stats["optim_dialog_turns"] = optim_turns
        stats["total_shapes"] = total_shapes
        stats["play_turns"] = play_turns
        stats["n_turns"] = n_turns
        stats["combo_name"] = combo_name
        stats["optim_success"] = optim_success
        stats["shapes_list_gt"] = shapes_list_gt
        stats["colors_list_gt"] = colors_list_gt
        # Get reconstruction_status and optim_success from Evaluation section
        ev = interactions.get("Evaluation", {})
        stats["reconstruction_status"] = ev.get("reconstruction_status")
        if stats["optim_success"] is None:
            stats["optim_success"] = ev.get("optim_success")

    if os.path.exists(scores_path):
        scores = read_json_file(scores_path) or {}
        main_score, reconst_status_from_scores = parse_scores(scores)
        # Use reconstruction_status from interactions.json if not already set
        if stats["reconstruction_status"] is None:
            stats["reconstruction_status"] = reconst_status_from_scores

        if isinstance(main_score, float) and np.isnan(main_score):
            stats["accuracy_vals"].append(0)
            stats["aborted_episodes"].append(os.path.basename(episode_path))
            stats["outcome"] = "aborted"
        elif main_score == 0:
            stats["failed_episodes"].append(os.path.basename(episode_path))
            stats["outcome"] = "failed"
            stats["accuracy_vals"].append(0)
            
            # Determine if episode is conclusive_wrong or non_conclusive (only for failed episodes)
            reconst_status = stats["reconstruction_status"]
            play_turns = stats["play_turns"]
            n_turns = stats["n_turns"]
            
            if reconst_status is False:
                if play_turns is not None and n_turns is not None:
                    if play_turns == n_turns:
                        stats["outcome"] = "non_conclusive"
                    elif play_turns < n_turns:
                        stats["outcome"] = "conclusive_wrong"
        else:
            stats["accuracy_vals"].append(main_score)
            stats["outcome"] = "success"
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
                aborted_episodes: List[str] = []
                conclusive_wrong_episodes: List[str] = []
                non_conclusive_episodes: List[str] = []
                optim_failed_episodes: List[str] = []
                optim_success_episodes: List[str] = []
                reconst_success_episodes: List[str] = []
                reconst_failed_episodes: List[str] = []
                code_stats: Dict[str, Any] = {}
                # dialog_stats_by_shape maps shape_key -> list of (episode, turns, reconst_status)
                dialog_stats_by_shape: Dict[str, List[Tuple[str, int]]] = {}
                optim_dialog_stats_by_shape: Dict[str, List[Tuple[str, int]]] = {}
                shape_stats: Dict[str, Dict[str, int]] = {}
                shape_code_stats: Dict[str, Dict[str, Any]] = {}
                failed_episodes_by_shape: Dict[str, List[str]] = {}
                conclusive_wrong_episodes_by_shape: Dict[str, List[str]] = {}
                non_conclusive_episodes_by_shape: Dict[str, List[str]] = {}

                episodes = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
                num_episodes = len(episodes)

                for episode in episodes:
                    episode_path = os.path.join(exp_path, episode)
                    ep_stats = process_episode(episode_path)
                    # determine shape key early so it's available to all aggregations
                    total_shapes = ep_stats.get("total_shapes")
                    shape_key_str = str(total_shapes) if total_shapes is not None else "unknown"
                    accuracy_data.extend(ep_stats.get("accuracy_vals", []))
                    failed_episodes.extend(ep_stats.get("failed_episodes", []))                   
                    aborted_episodes.extend(ep_stats.get("aborted_episodes", []))

                    if ep_stats.get("code_stats"):
                        code_stats[episode] = ep_stats["code_stats"]
                        # update per-shape code stats
                        code_data = ep_stats["code_stats"]
                        # ensure shape_code_stats entry
                        if shape_key_str not in shape_code_stats:
                            shape_code_stats[shape_key_str] = {
                                "used_clarification_count": 0,
                                "num_clarifications": 0,
                                "ep_clarifications": [],
                                "ep_remove": [],
                                "ep_move": [],
                                "ep_clear": [],
                                "ep_undo": [],
                                "ep_reconst_retry": [],
                            }
                        scs = shape_code_stats[shape_key_str]
                        if code_data.get("used_clarification"):
                            scs["used_clarification_count"] += 1
                            scs["ep_clarifications"].append(episode)
                        scs["num_clarifications"] += int(code_data.get("num_clarifications", 0))
                        if code_data.get("used_remove"):
                            scs["ep_remove"].append(episode)
                        if code_data.get("used_move"):
                            scs["ep_move"].append(episode)
                        if code_data.get("used_clear"):
                            scs["ep_clear"].append(episode)
                        if code_data.get("used_undo"):
                            scs["ep_undo"].append(episode)
                        if code_data.get("used_retry_reconst"):
                            scs["ep_reconst_retry"].append(episode)
                    if ep_stats.get("dialog_turns") is not None:
                        # Group dialog turns by total_shapes: store (episode, turns, reconst_status)
                        dialog_stats_by_shape.setdefault(shape_key_str, []).append(
                            (episode, int(ep_stats["dialog_turns"]), ep_stats.get("reconstruction_status"))
                        )
                    if ep_stats.get("optim_dialog_turns") is not None:
                        optim_dialog_stats_by_shape.setdefault(shape_key_str, []).append(
                            (episode, int(ep_stats["optim_dialog_turns"]), ep_stats.get("optim_success"))
                        )
                    # aggregate by total_shapes
                    # use shape_key_str defined above
                    if shape_key_str not in shape_stats:
                        shape_stats[shape_key_str] = {
                            "total": 0,
                            "reconst_success": 0,
                            "reconst_failure": 0,
                            "optim_success": 0,
                            "optim_failure": 0,
                            "aborted": 0,
                            "conclusive_wrong": 0,
                            "non_conclusive": 0,
                        }

                    outcome = ep_stats.get("outcome", "unknown")

                    if outcome == "aborted":
                        shape_stats[shape_key_str]["aborted"] += 1
                    elif outcome == "conclusive_wrong":
                        shape_stats[shape_key_str]["conclusive_wrong"] += 1
                        conclusive_wrong_episodes.append(episode)
                        conclusive_wrong_episodes_by_shape.setdefault(shape_key_str, []).append(episode)
                        failed_episodes_by_shape.setdefault(shape_key_str, []).append(episode)
                    elif outcome == "non_conclusive":
                        shape_stats[shape_key_str]["non_conclusive"] += 1
                        non_conclusive_episodes.append(episode)
                        non_conclusive_episodes_by_shape.setdefault(shape_key_str, []).append(episode)
                        failed_episodes_by_shape.setdefault(shape_key_str, []).append(episode)
                    elif outcome == "failed":
                        failed_episodes_by_shape.setdefault(shape_key_str, []).append(episode)
                    shape_stats[shape_key_str]["total"] += 1

                    # Track reconst and optim using flags from interactions.json
                    ep_reconst_status = ep_stats.get("reconstruction_status")
                    if ep_reconst_status is True:
                        reconst_success_episodes.append(episode)
                        shape_stats[shape_key_str]["reconst_success"] += 1
                        # Track optim_success only among reconst-successful episodes
                        ep_optim_success = ep_stats.get("optim_success")
                        if ep_optim_success is True:
                            optim_success_episodes.append(episode)
                            shape_stats[shape_key_str]["optim_success"] += 1
                        elif ep_optim_success is False:
                            optim_failed_episodes.append(episode)
                            shape_stats[shape_key_str]["optim_failure"] += 1
                    elif ep_reconst_status is False:
                        reconst_failed_episodes.append(episode)
                        shape_stats[shape_key_str]["reconst_failure"] += 1

                total_aborted = len(aborted_episodes)
                total_failed = len(failed_episodes)
                total_optim_failed = len(optim_failed_episodes)
                total_optim_success = len(optim_success_episodes)
                total_reconst_success = len(reconst_success_episodes)
                total_reconst_failed = len(reconst_failed_episodes)
                total_episodes = num_episodes
                total_run_episodes = total_episodes - total_aborted

                ttr_accuracy = round(total_reconst_success / total_episodes, 2) if total_episodes > 0 else 0
                reconst_accuracy = round(total_reconst_success / total_run_episodes, 2) if total_run_episodes > 0 else 0
                optim_accuracy = round(total_optim_success / total_reconst_success, 2) if total_reconst_success > 0 else 0

                # legacy flat lists (kept for backward compatibility)
                ep_clarifications_flat = [ep for ep, d in code_stats.items() if d.get("used_clarification")]
                ep_remove_flat = [ep for ep, d in code_stats.items() if d.get("used_remove")]
                ep_move_flat = [ep for ep, d in code_stats.items() if d.get("used_move")]
                ep_clear_flat = [ep for ep, d in code_stats.items() if d.get("used_clear")]
                ep_undo_flat = [ep for ep, d in code_stats.items() if d.get("used_undo")]
                ep_reconst_retry_flat = [ep for ep, d in code_stats.items() if d.get("used_retry_reconst")]

                # grouped by shape: create dictionaries mapping shape_key -> lists/counts
                used_clarification_by_shape: Dict[str, bool] = {}
                num_clarifications_by_shape: Dict[str, int] = {}
                ep_clarifications_by_shape: Dict[str, List[str]] = {}
                ep_remove_by_shape: Dict[str, List[str]] = {}
                ep_move_by_shape: Dict[str, List[str]] = {}
                ep_clear_by_shape: Dict[str, List[str]] = {}
                ep_undo_by_shape: Dict[str, List[str]] = {}
                ep_reconst_retry_by_shape: Dict[str, List[str]] = {}

                for sk, scs in shape_code_stats.items():
                    used_clarification_by_shape[sk] = scs.get("used_clarification_count", 0) > 0
                    num_clarifications_by_shape[sk] = scs.get("num_clarifications", 0)
                    ep_clarifications_by_shape[sk] = scs.get("ep_clarifications", [])
                    ep_remove_by_shape[sk] = scs.get("ep_remove", [])
                    ep_move_by_shape[sk] = scs.get("ep_move", [])
                    ep_clear_by_shape[sk] = scs.get("ep_clear", [])
                    ep_undo_by_shape[sk] = scs.get("ep_undo", [])
                    ep_reconst_retry_by_shape[sk] = scs.get("ep_reconst_retry", [])

                # expose grouped lists under the main ep_* names (shape-keyed)
                ep_clarifications = ep_clarifications_by_shape
                ep_remove = ep_remove_by_shape
                ep_move = ep_move_by_shape
                ep_clear = ep_clear_by_shape
                ep_undo = ep_undo_by_shape
                ep_reconst_retry = ep_reconst_retry_by_shape


                # compute percentages per shape
                for k, v in shape_stats.items():
                    total = v.get("total", 0)
                    reconst_succ = v.get("reconst_success", 0)
                    reconst_fail = v.get("reconst_failure", 0)
                    optim_succ = v.get("optim_success", 0)
                    optim_fail = v.get("optim_failure", 0)
                    aborted = v.get("aborted", 0)
                    conclusive_wrong = v.get("conclusive_wrong", 0)
                    non_conclusive = v.get("non_conclusive", 0)

                    v["reconst_success_pct"] = round((reconst_succ / total), 2) if total > 0 else 0.0
                    v["reconst_failure_pct"] = round((reconst_fail / total), 2) if total > 0 else 0.0
                    v["optim_success_pct"] = round((optim_succ / reconst_succ), 2) if reconst_succ > 0 else 0.0
                    v["optim_failure_pct"] = round((optim_fail / reconst_succ), 2) if reconst_succ > 0 else 0.0
                    v["aborted_pct"] = round((aborted / total), 2) if total > 0 else 0.0
                    v["conclusive_wrong_pct"] = round((conclusive_wrong / total), 2) if total > 0 else 0.0
                    v["non_conclusive_pct"] = round((non_conclusive / total), 2) if total > 0 else 0.0

                # Build dialog_stats summary grouped by shape, split by success/failure
                dialog_stats: Dict[str, Any] = {}
                for sk, ep_list in dialog_stats_by_shape.items():
                    all_turns = [t for (_, t, _) in ep_list]
                    success_turns = [t for (_, t, rs) in ep_list if rs is True]
                    failure_turns = [t for (_, t, rs) in ep_list if rs is False]

                    def _turn_summary(turns_list):
                        if not turns_list:
                            return {"count": 0, "avg": 0, "median": 0, "min": 0, "max": 0}
                        return {
                            "count": len(turns_list),
                            "avg": round(sum(turns_list) / len(turns_list), 2),
                            "median": round(float(np.median(turns_list)), 2),
                            "min": min(turns_list),
                            "max": max(turns_list),
                        }

                    dialog_stats[sk] = {
                        "total": _turn_summary(all_turns),
                        "success": _turn_summary(success_turns),
                        "failure": _turn_summary(failure_turns),
                    }

                # Build optim_dialog_stats summary grouped by shape, split by success/failure
                optim_dialog_stats: Dict[str, Any] = {}
                for sk, ep_list in optim_dialog_stats_by_shape.items():
                    all_turns = [t for (_, t, _) in ep_list]
                    success_turns = [t for (_, t, os_flag) in ep_list if os_flag is True]
                    failure_turns = [t for (_, t, os_flag) in ep_list if os_flag is False]

                    optim_dialog_stats[sk] = {
                        "total": _turn_summary(all_turns),
                        "success": _turn_summary(success_turns),
                        "failure": _turn_summary(failure_turns),
                    }

                save_data = {
                    "num_episodes": num_episodes,
                    "accuracy": round((float(np.sum(accuracy_data)) / num_episodes), 2) if num_episodes > 0 else 0,
                    "num_failed_episodes": total_failed,
                    "num_aborted_episodes": total_aborted,
                    "num_reconst_success_episodes": total_reconst_success,
                    "num_reconst_failed_episodes": total_reconst_failed,
                    "num_optim_failed_episodes": total_optim_failed,
                    "num_optim_success_episodes": total_optim_success,
                    "num_conclusive_wrong_episodes": len(conclusive_wrong_episodes),
                    "num_non_conclusive_episodes": len(non_conclusive_episodes),
                    "failed_episodes": failed_episodes,
                    "aborted_episodes": aborted_episodes,
                    "optim_failed_episodes": optim_failed_episodes,
                    "conclusive_wrong_episodes": conclusive_wrong_episodes,
                    "non_conclusive_episodes": non_conclusive_episodes,
                    "ttr_accuracy": ttr_accuracy,
                    "reconst_accuracy": reconst_accuracy,
                    "optim_accuracy": optim_accuracy,
                    "used_clarification": any(d.get("used_clarification") for d in code_stats.values()),
                    "num_clarifications": sum(d.get("num_clarifications", 0) for d in code_stats.values()),
                    # ep_* now grouped by shape (shape_key -> list of episodes)
                    "ep_clarifications": ep_clarifications,
                    "ep_remove": ep_remove,
                    "ep_move": ep_move,
                    "ep_clear": ep_clear,
                    "ep_undo": ep_undo,
                    "ep_reconst_retry": ep_reconst_retry,
                    "failed_episodes_by_shape": failed_episodes_by_shape,
                    "conclusive_wrong_episodes_by_shape": conclusive_wrong_episodes_by_shape,
                    "non_conclusive_episodes_by_shape": non_conclusive_episodes_by_shape,
                    # legacy flat lists retained under _flat names
                    "ep_clarifications_flat": ep_clarifications_flat,
                    "ep_remove_flat": ep_remove_flat,
                    "ep_move_flat": ep_move_flat,
                    "ep_clear_flat": ep_clear_flat,
                    "ep_undo_flat": ep_undo_flat,
                    "ep_reconst_retry_flat": ep_reconst_retry_flat,
                    "dialog_stats": dialog_stats,
                    "optim_dialog_stats": optim_dialog_stats,
                    "shape_stats": shape_stats,
                    "shape_code_stats": shape_code_stats,
                    # grouped-by-shape summaries for quick access
                    "used_clarification_by_shape": used_clarification_by_shape,
                    "num_clarifications_by_shape": num_clarifications_by_shape,
                    "ep_clarifications_by_shape": ep_clarifications_by_shape,
                    "ep_remove_by_shape": ep_remove_by_shape,
                    "ep_move_by_shape": ep_move_by_shape,
                    "ep_clear_by_shape": ep_clear_by_shape,
                    "ep_undo_by_shape": ep_undo_by_shape,
                    "ep_reconst_retry_by_shape": ep_reconst_retry_by_shape,
                }

                if verbose:
                    print(f"Game: {game}, Model: {model}, Experiment: {exp}")
                    print(f"Total Episodes:{total_episodes}, Reconst Success: {total_reconst_success}, Reconst Failed: {total_reconst_failed}, Aborted: {total_aborted}, Failed: {total_failed}")
                    print(f"Conclusive Wrong: {len(conclusive_wrong_episodes)}, Non-Conclusive: {len(non_conclusive_episodes)}")
                    print(f"Optim Success: {total_optim_success}, Optim Failed: {total_optim_failed}")
                    print(f"ttr_accuracy: {ttr_accuracy}, reconst_accuracy: {reconst_accuracy}, optim_accuracy: {optim_accuracy}")

                results[game][model][exp] = save_data

    outpath = os.path.join(base_dir, "overall_results.json")
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2)

    return results


def main():
    parser = argparse.ArgumentParser(description="Compute overall scores from experiment directories")
    parser.add_argument("base_dir", nargs="?", default="/home/admin/Desktop/codebase/cocobots/testimageccbts_local/clemnew/clembench/skillreconstruct/r3_3_cfqfix_clp_reconstruct", help="Base directory containing model results")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose printing")
    args = parser.parse_args()

    compute_scores(args.base_dir, verbose=not args.quiet)


if __name__ == "__main__":
    main()