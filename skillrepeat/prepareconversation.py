import os
import json
from typing import Dict, Any, List, Optional, Tuple


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

                    dialogues[model][game][exp] = {}

                    episodes = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
                    num_episodes = len(episodes)   
                    for episode in episodes:
                        episode_path = os.path.join(exp_path, episode)
                        interactions = os.path.join(episode_path, "interactions.json")

                        interactionsdata = self.readfile(interactions)
                        if "Evaluation" not in interactionsdata or "genresponse" not in interactionsdata["Evaluation"]:
                            continue

                        repeatdata = interactionsdata["Evaluation"]["genresponse"]["repeat"]

                        epdialogues = []
                        for rdata in repeatdata:
                            instruction = rdata.get("instruction", "")
                            status = rdata.get("response", "").get("status", "")
                            response = rdata.get("response", "").get("details", "")
                            epdialogues.append({"instruction": instruction, "status": status, "response": response, })
                        dialogues[model][game][exp][episode] = epdialogues

                with open(os.path.join(base_dir, f"{model}_dialogues.json"), 'w') as outfile:
                    json.dump(dialogues[model], outfile, indent=4)



if __name__ == "__main__":
    base_dir = "rp_clpskills_human_clp_4"
    prepare_conversation = PrepareConversation()
    prepare_conversation.run(base_dir)
