import copy
import random
import string
from typing import List, Dict, Tuple

from clemcore.clemgame import GameInstanceGenerator
from addincontextsamples import get_incontext_samples

# set the name of the game in the script, as you named the directory
# this name will be used everywhere, including in the table of results
GAME_NAME = "progsynthesis"
# we will create 10 instances for each experiment; vary this as you wish
N_INSTANCES = 5
# if the generation involves randomness, remember to set a random seed
SEED = 123

LANGUAGE = "en"


class ProgSynthInstanceGenerator(GameInstanceGenerator):
    def __init__(self, game_name):
        # always do this to initialise GameInstanceGenerator
        super().__init__(game_name)
        self.game_name = game_name



    def _prepare_prompts(self, variant: str, boardinfo, fill_labels) -> Dict[str, str]:

        promptsdict = {}
        if variant == "multi_turn":
            prompt_filename = f"resources/initial_prompts/{LANGUAGE}/initial_prompt_multiturn"
        elif variant in ["single_turn", "single_turn_sc", "single_turn_hai", "single_turn_hai_sc", "single_turn_mg"]:
            prompt_filename = f"resources/initial_prompts/{LANGUAGE}/initial_prompt_singleturn"
        elif variant in ["regular", "regular_hai", "regular_mg"]:
            prompt_filename = f"resources/initial_prompts/{LANGUAGE}/initial_prompt_regular"

        prompt = self.load_template(prompt_filename)
        incontext_samples = get_incontext_samples(boardinfo["board"],
                                                  boardinfo["object"],
                                                  variant,
                                                  fill_labels["NUM_INCONTEXT_SAMPLES"],
                                                  boardinfo["total_shapes"],
                                                  boardinfo["combo_name"],
                                                  boardinfo["train_samples"],
                                                  fill_labels,
                                                  boardinfo["seed_template_name"],
                                                  SEED )


        fill_labels["INCONTEXT_SAMPLES"] = incontext_samples

        prompt = self.create_prompt(prompt, **fill_labels)

        promptsdict = {"prompt_a": prompt}
        return promptsdict


    def _prepare_samples_labels(self, varconfig: dict) -> Dict[str, str]:
        samples = {}

        if not varconfig:
            raise ValueError("varconfig is empty or None")

        if "TRAIN_DATA_FILE_NAME" not in varconfig or "TEST_DATA_FILE_NAME" not in varconfig:
            raise ValueError("TRAIN_DATA_FILE_NAME or TEST_DATA_FILE_NAME not found in varconfig")


        print(varconfig["TRAIN_DATA_FILE_NAME"], varconfig["TEST_DATA_FILE_NAME"])

        #No validation samples for human-written instructions
        train_samples = self.load_json(
            f'resources/data/{LANGUAGE}/{varconfig["TRAIN_DATA_FILE_NAME"]}'
        )
        test_samples = self.load_json(
            f'resources/data/{LANGUAGE}/{varconfig["TEST_DATA_FILE_NAME"]}'
        )

        samples = {
            "train": train_samples,
            "test": test_samples,
            "prompt_incontext_labels": varconfig["fill_labels"],
        }
        samples["prompt_incontext_labels"]["NUM_INCONTEXT_SAMPLES"] = varconfig["NUM_INCONTEXT_SAMPLES"]

        return samples


    # define on_generate, a mandatory method
    def on_generate(self):
        num_instances = 0

        config = self.load_json(
            f"resources/config/{LANGUAGE}/taskconfig.json")

        tot_instances = 0
        boards = config["boards"]
        for board in boards:
            objects = config[board]["objects"]
            for obj in objects:
                variants = config[board][obj]["variants"]
                for variant in variants:
                    experiment = self.add_experiment(f"{board}_{obj}_{variant}")
                    samples = self._prepare_samples_labels(config[board][obj][variant])

                    for board_type, objs_type in samples["test"].items():
                        for boardobj, num_shapes in objs_type.items():
                            for total_shapes, combo_names in num_shapes.items():
                                for combo_name in num_shapes[total_shapes]:
                                    for sample in num_shapes[total_shapes][combo_name]:
                                        test_dialogues = sample["dialogues"][variant]["instructions"]
                                        n_turns = len(test_dialogues)
                                        instance = self.add_game_instance(experiment, tot_instances)
                                        instance["data"] = {}

                                        boardinfo = {"board": board,
                                                     "object": obj,
                                                     "variant": variant,
                                                     "size": {"rows": config["board"]["rows"],
                                                              "cols": config["board"]["cols"]},
                                                     "total_shapes": total_shapes,
                                                     "combo_name": combo_name,
                                                     "train_samples": samples["train"],
                                                     "seed_template_name": sample["seed_template"],
                                                    }
                                        promptsdict = self._prepare_prompts(variant, boardinfo, samples["prompt_incontext_labels"])

                                        instance["data"]["prompts_dict"] = promptsdict
                                        instance["data"]["n_turns"] = n_turns
                                        instance["data"]["output_labels"] = {"function": samples["prompt_incontext_labels"]["OUTPUT_LABEL_HORDER"],
                                                                             "usage": samples["prompt_incontext_labels"]["OUTPUT_LABEL_HORDER_USAGE"],
                                                                             "output": None}
                                        instance["data"]["user_instruction"] = sample["dialogues"][variant]["instructions"][0]["<Programmer>"]
                                        instance["data"]["gt_code"] = sample["dialogues"][variant]["instructions"][0]["<Editor>"]
                                        instance["data"]["boardinfo"] = boardinfo
                                        instance["data"]["boardinfo"].pop("train_samples")

                                        tot_instances += 1
                                        break
                                    break
                                break
                            break
                        break
                    break


        print(
            f"Generated instances for - {self.game_name} game - {tot_instances} instances."
        )

    # an additional method, specific for our example
    def create_prompt(self, prompt: str, **kwargs) -> str:
        """Replace a prompt template with slot values."""
        text = string.Template(prompt).substitute(**kwargs)
        return text


if __name__ == "__main__":
    random.seed(SEED)
    # always call this, which will actually generate and save the JSON file
    ProgSynthInstanceGenerator(GAME_NAME).generate()
