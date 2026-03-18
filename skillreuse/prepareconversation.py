import os
import json
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class PrepareConversation:
    def __init__(self):
        pass

    def readfile(self, filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    
    def run(self, base_dir):
        if not base_dir:
            raise ValueError("Basedir must be provided.")
        
        
        if not os.path.exists(base_dir) or not os.path.isdir(base_dir):
            raise ValueError(f"Basedir {base_dir} does not exist.")
        
        dialogues = {}

        for model in os.listdir(base_dir):
            model_path = os.path.join(base_dir, model)
            if not os.path.isdir(model_path):
                continue
            dialogues[model] = {}

            for game in os.listdir(model_path):
                game_path = os.path.join(model_path, game)
                if not os.path.isdir(game_path):
                    continue

                dialogues[model][game] = {}

                for exp in os.listdir(game_path):
                    exp_path = os.path.join(game_path, exp)
                    if not os.path.isdir(exp_path):
                        continue

                    dialogues[model][game][exp] = {"used_oracle_code_as_skill_not_available":{"success":{}, "abort": {},  "failure":{}},
                                                   "dialogues": {"success":{}, "abort": {},  "failure":{}}}

                    episodes = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
                    num_episodes = len(episodes)
                    ep_turns = {"success": {2:[], 3:[], 4:[], 5:[]}, "abort": {2:[], 3:[], 4:[], 5:[]}, "failure": {2:[], 3:[], 4:[], 5:[]}}
                    for episode in episodes:
                        episode_path = os.path.join(exp_path, episode)
                        interactions = os.path.join(episode_path, "interactions.json")

                        interactionsdata = self.readfile(interactions)
                        if "Evaluation" not in interactionsdata or "genresponse" not in interactionsdata["Evaluation"]:
                            continue

                        reusedata = interactionsdata["Evaluation"]["genresponse"]["reuse"]
                        if interactionsdata["Aborted"]:
                            epstatus = "abort"
                        elif interactionsdata["Lose"]:
                            epstatus = "failure"
                        else:
                            epstatus = "success"
                        epdialogues = []
                        num_shapes = len(interactionsdata["Evaluation"]["boardinfo"]["simple_reuse"]["shapes"])
                        used_oracle_code_as_skill_not_available = interactionsdata["Evaluation"]["used_oracle_code_as_skill_not_available"]
                        num_ep_turns = len(interactionsdata["Evaluation"]["genresponse"]["reuse"])

                        for rdata in reusedata:

                            turn_number = rdata.get("current_turn", "")
                            instruction = rdata.get("instruction", "")
                            if "response" not in rdata:
                                status = ""
                                response = ""
                            else:
                                status = rdata.get("response", "").get("status", "")
                                response = rdata.get("response", "").get("details", "")
                            epdialogues.append({"turn_number": turn_number+1, "instruction": instruction, "status": status, "response": response, })
                        dialogues[model][game][exp]["dialogues"][epstatus].update({episode:epdialogues})
                        if used_oracle_code_as_skill_not_available:
                            #dialogues[model][game][exp]["used_oracle_code_as_skill_not_available"][epstatus]["count"] += 1
                            #dialogues[model][game][exp]["used_oracle_code_as_skill_not_available"][epstatus]["ep_turns"].append(num_ep_turns)
                            ep_turns[epstatus][num_shapes].append(num_ep_turns)

                    overall_status = {"success": {2: {}, 3: {}, 4: {}, 5: {}},
                                      "abort": {2: {}, 3: {}, 4: {}, 5: {}},
                                      "failure": {2: {}, 3: {}, 4: {}, 5: {}}}
                    for status in ["success", "abort", "failure"]:
                        for num_shapes in [2, 3, 4, 5]:
                            overall_status[status][num_shapes]["min"] = int(np.min(ep_turns[status][num_shapes])) if ep_turns[status][num_shapes] else 0
                            overall_status[status][num_shapes]["max"] = int(np.max(ep_turns[status][num_shapes])) if ep_turns[status][num_shapes] else 0
                            overall_status[status][num_shapes]["avg"] = round(float(np.mean(ep_turns[status][num_shapes])), 2) if ep_turns[status][num_shapes] else 0
                            overall_status[status][num_shapes]["median"] = int(np.median(ep_turns[status][num_shapes])) if ep_turns[status][num_shapes] else 0
                            overall_status[status][num_shapes]["count"] = len(ep_turns[status][num_shapes])
                            overall_status[status][num_shapes]["one_turn_eps_count"] = sum(1 for turns in ep_turns[status][num_shapes] if turns == 1)
                        overall_status[status]["total_count"] = sum(overall_status[status][num_shapes]["count"] for num_shapes in [2, 3, 4, 5])
                        overall_status[status]["one_turn_eps_count"] = sum(overall_status[status][num_shapes]["one_turn_eps_count"] for num_shapes in [2, 3, 4, 5])
                        dialogues[model][game][exp]["used_oracle_code_as_skill_not_available"][status] = overall_status[status]
                with open(os.path.join(base_dir, f"{model}_dialogues.json"), 'w') as outfile:
                    json.dump(dialogues[model][game][exp]["dialogues"], outfile, indent=4)

                with open(os.path.join(base_dir, f"{model}_skilunavail_epstats.json"), 'w') as outfile:
                    json.dump({f"{model}": {f"{game}": {f"{exp}": dialogues[model][game][exp]["used_oracle_code_as_skill_not_available"]}}}, outfile, indent=4)



if __name__ == "__main__":
    base_dir = "rp_clpskills_clp_4"
    prepare_conversation = PrepareConversation()
    prepare_conversation.run(base_dir)
