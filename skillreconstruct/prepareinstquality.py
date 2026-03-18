import os
import numpy as np
import json



class PrepareInstQuality:
    def __init__(self):
        pass


    def readfile(self, filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data

    def run(self, base_dir, clp_model=True):
        if not base_dir:
            raise ValueError("Basedir must be provided.")

        if not clp_model:
            filename = "upgpt-codex-t0.0_dialogues.json"
        else:
            filename = "clp-chat-2-t0.0_dialogues.json"

        filepath = f"{base_dir}/{filename}"
        convdata = self.readfile(f"{base_dir}/{filename}")
        if convdata is None:
            raise ValueError("No conversation file available")

        succ_interactions = convdata["skillreconstruct"]["skillreconst_zs"]["success"]
        ep_turns = []
        for ep_num, ep_data in succ_interactions.items():
            #ep_turns.append(len(ep_data))
            ep_words = []
            for index, data in enumerate(ep_data):
                inst_word_count = len(data["instruction"].strip().split(" "))
                ep_words.append(inst_word_count)
                convdata["skillreconstruct"]["skillreconst_zs"]["success"][ep_num][index]["word_count"] = inst_word_count
       #print(ep_turns)

        with open(f"{base_dir}/moddlgs.json", 'w') as filepath:
            json.dump(convdata, filepath, indent=4)
if __name__ == "__main__":
    base_dir = "rskills_clp_2"
    piq = PrepareInstQuality()
    piq.run(base_dir, True)        
