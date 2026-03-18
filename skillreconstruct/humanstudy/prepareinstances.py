import os
import random
import json

NUM_RANDOM_INSTANCES = 50
SEED = 76
CURRENT_DIR_PATH = "/home/admin/Desktop/codebase/cocobots/testimageccbts_local/clemnew/clembench/skillreconstruct/humanstudy"

class PrepareInstancesForHumanStudy:
    def __init__(self):
        random.seed(SEED)

    def readfile(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Instances file not found: {filepath}")

        instances = {}
        with open(filepath, 'r') as f:
            instances = json.load(f)

        if not instances:
            raise ValueError(f"No instances found in file: {filepath}")
        return instances


    def _prepare_instances_files(self, instances_data, random_gameids):
        print(random_gameids)        
        if not random_gameids or len(random_gameids) < 50:
            raise ValueError("Not enough game instances to prepare instances.")
        #Prepare 5 instances files from the 50 random gameids
        for i in range(5):
            gamedata = []            
            for gameid in random_gameids[i*10:(i+1)*10]:
                if gameid not in [gi["game_id"] for gi in instances_data["experiments"][0]["game_instances"]]:
                    raise ValueError(f"Selected game ID {gameid} not found in instances data.")
                for gi in instances_data["experiments"][0]["game_instances"]:
                    if gi["game_id"] == gameid:
                        gamedata.append(gi)
                        break
            selected_instances = {
                "experiments": [
                    {
                        "name": "skillreconstruct_zs",
                        "game_instances": gamedata
                    }
                ]
            }
                
            with open(os.path.join(CURRENT_DIR_PATH, f"instances_{i+1}.json"), 'w') as f:
                json.dump(selected_instances, f, indent=2)
        print("Prepared 5 instances files for human study.")

    def _extract_model_results(self, base_dir, random_gameids):
        print(random_gameids)
        found_episodes = []
        for model in os.listdir(base_dir):
            model_path = os.path.join(base_dir, model)
            if not os.path.isdir(model_path) or "-t0.0" not in model:
                continue

            for game in os.listdir(model_path):
                game_path = os.path.join(model_path, game)
                if not os.path.isdir(game_path):
                    continue

                for exp in os.listdir(game_path):
                    exp_path = os.path.join(game_path, exp)
                    if not os.path.isdir(exp_path):
                        continue
                    base_dir_name = base_dir.strip(os.sep).split(os.sep)[-1]
                    extresultspath = os.path.join(CURRENT_DIR_PATH, base_dir_name, model.strip(os.sep), game.strip(os.sep), exp.strip(os.sep))
                    os.makedirs(extresultspath, exist_ok=True)

                    episodes = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
                    for episode in episodes:
                        episode_num = int(episode.split("_")[-1])#.replace("00", ""))
                        if episode_num not in random_gameids:
                            continue
                        #copy the episode directory to the new location
                        if episode_num in found_episodes:
                            print(f"Warning: Duplicate episode number found, skipping copy: {episode_num} {episode}, {found_episodes}")
                            input()
                        found_episodes.append(episode_num)
                        src_episode_path = os.path.join(exp_path, episode)
                        dst_episode_path = os.path.join(extresultspath, episode)
                        if os.path.exists(dst_episode_path):
                            print(f"Warning: Destination path already exists, skipping copy: {dst_episode_path}")
                            continue
                        os.system(f"cp -r {src_episode_path} {dst_episode_path}")
        print(f"Extracted model results for {len(found_episodes)} selected game instances.")

        found_sorted = sorted(found_episodes)
        random_sorted = sorted(random_gameids)
        if found_sorted != random_sorted:
            print(f"Warning: Found episodes do not match selected random game IDs.")
            print(f"{found_sorted[:10]}, {random_sorted[:10]}")
            print(f"differences: {set(found_sorted) - set(random_sorted)}, {set(random_sorted) - set(found_sorted)}")
        else:
            print("No mismatch between model results and selected game IDs.")


    def run(self, instances_file, model_results_dir):
        instances_data = self.readfile(instances_file)

        print(f"Read {len(instances_data['experiments'][0]['game_instances'])} instances from {instances_file}")
        gameinstances = instances_data["experiments"][0]["game_instances"]
        gameids = [gi["game_id"] for gi in gameinstances]
        print(f"Number of game instances: {len(gameids)}")

        reconst_gameids = [189, 237, 486, 199, 102, 465, 152, 27, 214, 431, 121, 144, 154, 385, 430, 224, 250, 118, 42, 171, 433, 116, 170, 404, 272, 30, 3, 337, 211, 302, 460, 310, 402, 196, 380, 169, 277, 233, 12, 32, 339, 322, 469, 206, 77, 51, 125, 324, 478, 391]

        reconst_gameids = [gi//3 for gi in reconst_gameids]
        if any(gi > 165  for gi in reconst_gameids):
            print(f"Warning: Some reconstructed game IDs are out of bounds: {reconst_gameids}")
            input()

        if len(set(reconst_gameids)) != 50:
            print(f"Looks like there is a duplicate in the reconst game ids")
            print("Fetching another game id from the larger set")
            num_duplicate_gameids = len(reconst_gameids) - len(set(reconst_gameids))
            reconst_gameids = list(set(reconst_gameids))
            print(f"Number of duplicate game ids: {num_duplicate_gameids}")
            filtered_gameids = [gi for gi in gameids if gi not in reconst_gameids]
            newgameids = random.sample(filtered_gameids, k=num_duplicate_gameids)
            print(f"Added new game ids {newgameids} to reconst game ids")
            reconst_gameids.extend(newgameids)
            num_duplicate_gameids = len(reconst_gameids) - len(set(reconst_gameids))
            if num_duplicate_gameids > 0:
                print(f"Warning: Still have {num_duplicate_gameids} duplicate game ids after adding new ones.")
                input()

        random_gameids = reconst_gameids#random.sample(gameids, min(NUM_RANDOM_INSTANCES, len(gameids)))
        if len(random_gameids) < NUM_RANDOM_INSTANCES:
            print(f"Warning: Only {len(random_gameids)} instances available, less than the requested {NUM_RANDOM_INSTANCES}.")

        print(f"Selected {len(random_gameids)} random game instances for human study {random_gameids[:5]}.")
        #self._prepare_instances_files(instances_data, random_gameids)
        #self._extract_model_results(model_results_dir, random_gameids)
        with open(os.path.join(CURRENT_DIR_PATH, "selected_gameids.txt"), 'w') as f:
            for gameid in random_gameids:
                f.write(f"{gameid}\n")


    def preparerestoftheinstances(self, instances_file, existing_gameids_file):
        instances_data = self.readfile(instances_file)
        existing_game_ids = []

        if existing_gameids_file:
            with open(existing_gameids_file, 'r') as f:
                existing_game_ids = [line.strip() for line in f]

        if not existing_game_ids:
            print("No existing game IDs found, cannot prepare the rest of the instances.")
            input()

        existing_game_ids = [int(gi) for gi in existing_game_ids]
        game_ids = list(range(0, 165))
        rest_game_ids = list(set(game_ids) - set(existing_game_ids))
        print(f"Preparing the rest of the instances for game ids: {len(rest_game_ids)}")


        #Divide them into 10 instances per file and prepare the files
        num_instance_files = (len(rest_game_ids) + 9) // 10
        for i in range(6, 6 + num_instance_files):
            instance_game__ids = random.sample(rest_game_ids, min(10, len(rest_game_ids)))
            rest_game_ids = list(set(rest_game_ids) - set(instance_game__ids))
            gamedata = []
            for gameid in instance_game__ids:
                if gameid not in [gi["game_id"] for gi in instances_data["experiments"][0]["game_instances"]]:
                    print(f"Warning: Game ID {gameid} not found in instances data, skipping.")
                    input()

                for gi in instances_data["experiments"][0]["game_instances"]:
                    if gi["game_id"] == gameid:
                        gamedata.append(gi)
                        break
            selected_instances = {
                "experiments": [
                    {
                        "name": "skillreconstruct_zs",
                        "game_instances": gamedata
                    }
                ]
            }
            with open(os.path.join(CURRENT_DIR_PATH, f"instances_{i}.json"), 'w') as f:
                json.dump(selected_instances, f, indent=2)



if __name__ == "__main__":
    prepare_instances = PrepareInstancesForHumanStudy()
    #prepare_instances.run("/home/admin/Desktop/codebase/cocobots/testimageccbts_local/clemnew/clembench/skillreconstruct/in/instances_hs_clp.json", "/home/admin/Desktop/codebase/cocobots/testimageccbts_local/clemnew/clembench/skillreconstruct/rskills_gpt_2")
    prepare_instances.preparerestoftheinstances("/home/admin/Desktop/codebase/cocobots/testimageccbts_local/clemnew/clembench/skillreconstruct/in/instances_hs_clp.json","selected_gameids.txt")




