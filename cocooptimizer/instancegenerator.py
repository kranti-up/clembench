import random
import string
from typing import Dict
import os

from clemcore.clemgame import GameInstanceGenerator
from utils.prepareasciirep import PrepareASCIIRep


# set the name of the game in the script, as you named the directory
# this name will be used everywhere, including in the table of results
#GAME_NAME = "imageccbts"
# we will create 10 instances for each experiment; vary this as you wish
#N_INSTANCES = 10
# if the generation involves randomness, remember to set a random seed
SEED = 123

LANGUAGE = "en"


class CCBTSOptimizerInstanceGenerator(GameInstanceGenerator):
    def __init__(self):
        # always do this to initialise GameInstanceGenerator
        super().__init__(os.path.dirname(__file__))
        self.game_name = "cocooptimizer"
        self.prepare_ascii_rep = PrepareASCIIRep()



    def _prepare_prompts(self, variant: str, boardinfo, fill_labels) -> Dict[str, str]:

        prompt_files = {
            "prompt_a": f"resources/initial_prompts/{LANGUAGE}/initial_prompt_co.template",
            "turn_prompt_a": f"resources/initial_prompts/{LANGUAGE}/turn_prompt_co.template",
            "prompt_a_human": f"resources/initial_prompts/{LANGUAGE}/initial_prompt_co_human.template",
            "turn_prompt_a_human": f"resources/initial_prompts/{LANGUAGE}/turn_prompt_co_human.template",
        }

        promptsdict = {}
        for key, file_path in prompt_files.items():
            prompt_template = self.load_template(file_path)
            #if "turn" in key:
            #    promptsdict[key] = prompt_template#self.create_prompt(prompt_template)
            #else:
            promptsdict[key] = self.create_prompt(prompt_template, **fill_labels)

        return promptsdict


    def _prepare_samples_labels(self, varconfig: dict) -> Dict[str, str]:
        samples = {}

        if not varconfig:
            raise ValueError("varconfig is empty or None")

        if "TRAIN_DATA_FILE_NAME" not in varconfig or "TEST_DATA_FILE_NAME" not in varconfig:
            raise ValueError("TRAIN_DATA_FILE_NAME or TEST_DATA_FILE_NAME not found in varconfig")


        #print(varconfig["TRAIN_DATA_FILE_NAME"], varconfig["TEST_DATA_FILE_NAME"])

        #No validation samples for human-written instructions
        if varconfig["TRAIN_DATA_FILE_NAME"] == "":
            train_samples = []
        else:
            train_samples = self.load_json(
                f'resources/data/{LANGUAGE}/{varconfig["TRAIN_DATA_FILE_NAME"]}'
            )

        if varconfig["TEST_DATA_FILE_NAME"] == "":
            test_samples = []
        else:
            test_samples = self.load_json(
                f'resources/data/{LANGUAGE}/{varconfig["TEST_DATA_FILE_NAME"]}'
            )

        samples = {
            "train": train_samples,
            "test": test_samples,
            "prompt_incontext_labels": {"NUM_INCONTEXT_SAMPLES": varconfig["NUM_INCONTEXT_SAMPLES"]}
        }

        return samples

    def _prepare_inst_code_pairs_for_synthetic_data(self, dialogues: list) -> list:
        inst_code_pairs = []
        for turn in dialogues:
            instruction = turn.get("<Programmer>", None)
            code = turn.get("<Editor>", None)
            if instruction is not None and code is not None:
                inst_code_pairs.append({
                    "instruction": instruction,
                    "code": code
                })
        return inst_code_pairs


    # define on_generate, a mandatory method
    def on_generate(self, seed: int, **kwargs):
        num_instances = 0

        config = self.load_json(
            f"resources/config/{LANGUAGE}/taskconfig.json")

        use_only_success_samples = config["use_only_success_samples"]
        tot_instances = 0
        boards = config["boards"]
        for board in boards:
            objects = config[board]["objects"]
            for obj in objects:
                variants = config[board][obj]["variants"]
                for variant in variants:
                    num_ic_samples = config[board][obj][variant]["NUM_INCONTEXT_SAMPLES"]
                    ic_type = f"fs_{num_ic_samples}" if num_ic_samples > 0 else "zs"
                    experiment = self.add_experiment(f"{board}_{obj}_{variant}_{ic_type}")
                    samples = self._prepare_samples_labels(config[board][obj][variant])

                    for board_type, objs_type in samples["test"].items():
                        for boardobj, num_shapes in objs_type.items():
                            for total_shapes, combo_names in num_shapes.items():
                                for combo_name in num_shapes[total_shapes]:
                                    #print(len(num_shapes[total_shapes][combo_name]))
                                    for tsample in num_shapes[total_shapes][combo_name]:
                                        #if total_shapes not in ["2"]:# or "b" in combo_name:
                                        #    continue

                                        if "inst_code_pairs" not in tsample:
                                            # TODO: Need to handle this later for base datasets
                                            print("Skipping sample with missing inst_code_pairs")
                                            continue

                                        if use_only_success_samples and not tsample["reconstruction_status"] or tsample["reconstruction_aborted"]:
                                            print("Skipping sample with failed or aborted reconstruction")
                                            continue

                                        combo_name = tsample["combo_name"]
                                        inst_code_pairs = tsample["inst_code_pairs"] if "inst_code_pairs" in tsample else []
                                        func_def = f"def {combo_name}(board, colors, x, y)"
                                        func_usage = tsample["code"]["single_turn"]["usage"]
                                        target_board = tsample["generated_board"] if "generated_board" in tsample else None
                                        target_board_rep = tsample["generated_board_rep"] if "generated_board_rep" in tsample else None
                                        target_board_cells = tsample["gen_occupied_cells"] if "gen_occupied_cells" in tsample else None

                                        if board_type == "simple":
                                            use_inst_variant = "single_turn" if "single_turn" in tsample["dialogues"] else variant
                                            test_dialogues = tsample["dialogues"][use_inst_variant]["instructions"]
                                            board_size = {"rows": tsample["rows"],
                                                        "cols": tsample["cols"]}

                                        elif board_type == "regular":
                                            use_inst_variant = "regular" if "regular" in tsample["dialogues"] else variant
                                            test_dialogues = tsample["dialogues"][use_inst_variant]["instructions"]
                                            board_size = {"rows": 8,
                                                        "cols": 8}

                                        n_turns = config["max_turns"]


                                        instance = self.add_game_instance(experiment, tot_instances)
                                        instance["data"] = {}

                                        gt_code = tsample["code"]["single_turn"]
                                        if target_board_rep is None and variant != "reconstruct-multi_turn":
                                            ascii_rep_board, board_rep = self.prepare_ascii_rep.get_ascii_representation(gt_code, board_size)
                                            target_board_rep = ascii_rep_board
                                            target_board = board_rep
                                            target_board_cells = self.prepare_ascii_rep.get_occupied_cells_from_board(board_rep)
                                            inst_code_pairs = self._prepare_inst_code_pairs_for_synthetic_data(tsample["dialogues"]["multi_turn"]["instructions"])                                            

                                        boardinfo = {"board": target_board,
                                                     "board_type": board_type,
                                                     "object_type": boardobj,
                                                     "variant": variant,
                                                     "size": board_size,
                                                     "total_shapes": total_shapes,
                                                     "shapes": tsample["shapes"],
                                                     "colors": tsample["colors"],
                                                     "x": tsample["x"],
                                                     "y": tsample["y"],
                                                     "locations": {"row": tsample["x"][0]+1, "col": tsample["y"][0]+1},
                                                     "orientations": tsample["orientations"] if "orientations" in tsample else None,
                                                     "min_rows": tsample["min_rows"] if "min_rows" in tsample else None,
                                                     "min_cols": tsample["min_cols"] if "min_cols" in tsample else None,
                                                     "combo_name": combo_name,
                                                     "quadrant": tsample["quadrant"] if "quadrant" in tsample else None,
                                                     # Train Samples are not added - check later
                                                     #"train_samples": samples["train"],
                                                     "seed_template_name": tsample["seed_template"],
                                                     "code": tsample["code"],
                                                     "synthetic_instructions": test_dialogues[0]["<Programmer>"],
                                                     "target_board_rep": target_board_rep,
                                                     "target_board_cells": target_board_cells
                                                    }
                                        print(boardinfo["target_board_cells"])

                                        samples["prompt_incontext_labels"]["GOAL"] = target_board_rep#ascii_rep_board
                                        samples["prompt_incontext_labels"]["OBJECT_NAME"] = combo_name
                                        samples["prompt_incontext_labels"]["ERROR_FEEDBACK"] = "ERROR_FEEDBACK"
                                        samples["prompt_incontext_labels"]["INSTRUCTION"] = "\n"#"$INSTRUCTION"
                                        samples["prompt_incontext_labels"]["GRID_SIZE"] = f"{board_size['rows']} x {board_size['cols']}"
                                        samples["prompt_incontext_labels"]["SKILL_NAME"] = combo_name
                                        samples["prompt_incontext_labels"]["COLORS"] = tsample["colors"]
                                        samples["prompt_incontext_labels"]["LOCATION"] = {"row": tsample["x"][0]+1, "col": tsample["y"][0]+1}                                     


                                        samples["prompt_incontext_labels"]["ROW"] = board_size["rows"]
                                        samples["prompt_incontext_labels"]["COL"] = board_size["cols"]
                                        samples["prompt_incontext_labels"]["ROW_MAX"] = board_size["rows"] - 1
                                        samples["prompt_incontext_labels"]["COL_MAX"] = board_size["cols"] - 1
                                        print(board_size["rows"], board_size["cols"])
                                        if board_size["rows"] == 1:
                                            samples["prompt_incontext_labels"]["ROW_MAX_TEXT"] = "zeroth"
                                            samples["prompt_incontext_labels"]["COL_MAX_TEXT"] = "zeroth"
                                        elif board_size["rows"] == 2:
                                            samples["prompt_incontext_labels"]["ROW_MAX_TEXT"] = "first"
                                            samples["prompt_incontext_labels"]["COL_MAX_TEXT"] = "first"
                                        elif board_size["rows"] == 3:
                                            samples["prompt_incontext_labels"]["ROW_MAX_TEXT"] = "second"
                                            samples["prompt_incontext_labels"]["COL_MAX_TEXT"] = "second"
                                        elif board_size["rows"] == 4:
                                            samples["prompt_incontext_labels"]["ROW_MAX_TEXT"] = "third"
                                            samples["prompt_incontext_labels"]["COL_MAX_TEXT"] = "third"
                                        elif board_size["rows"] == 5:
                                            samples["prompt_incontext_labels"]["ROW_MAX_TEXT"] = "fourth"
                                            samples["prompt_incontext_labels"]["COL_MAX_TEXT"] = "fourth"
                                        elif board_size["rows"] == 6:
                                            samples["prompt_incontext_labels"]["ROW_MAX_TEXT"] = "fifth"
                                            samples["prompt_incontext_labels"]["COL_MAX_TEXT"] = "fifth"
                                        elif board_size["rows"] == 7:
                                            samples["prompt_incontext_labels"]["ROW_MAX_TEXT"] = "sixth"
                                            samples["prompt_incontext_labels"]["COL_MAX_TEXT"] = "sixth"
                                        elif board_size["rows"] == 8:
                                            samples["prompt_incontext_labels"]["ROW_MAX_TEXT"] = "seventh"
                                            samples["prompt_incontext_labels"]["COL_MAX_TEXT"] = "seventh"
                                        elif board_size["rows"] == 9:
                                            samples["prompt_incontext_labels"]["ROW_MAX_TEXT"] = "eighth"
                                            samples["prompt_incontext_labels"]["COL_MAX_TEXT"] = "eighth"
                                        elif board_size["rows"] == 10:
                                            samples["prompt_incontext_labels"]["ROW_MAX_TEXT"] = "ninth"
                                            samples["prompt_incontext_labels"]["COL_MAX_TEXT"] = "ninth"
                                        else:
                                            samples["prompt_incontext_labels"]["ROW_MAX_TEXT"] = str(board_size["rows"] - 1)
                                            samples["prompt_incontext_labels"]["COL_MAX_TEXT"] = str(board_size["cols"] - 1)


                                        promptsdict = self._prepare_prompts(variant, boardinfo, samples["prompt_incontext_labels"])

                                        instance["data"]["prompts_dict"] = promptsdict
                                        instance["data"]["use_dspy_optim"] = config["use_dspy_optim"]
                                        instance["data"]["use_dspy_optim_history"] = config["use_dspy_optim_history"]
                                        instance["data"]["use_dspy_optim_retry"] = config["use_dspy_optim_retry"]
                                        instance["data"]["use_diff_human_prompts"] = config["use_diff_human_prompts"]
                                        instance["data"]["n_turns"] = n_turns
                                        instance["data"]["num_dspy_optim_retry"] = config["num_dspy_optim_retry"]
                                        instance["data"]["ascii_rep"] = target_board_rep#ascii_rep_board
                                        instance["data"]["func_def"] = func_def
                                        instance["data"]["func_usage"] = func_usage
                                        instance["data"]["inst_code_pairs"] = inst_code_pairs
                                        instance["data"]["boardinfo"] = boardinfo
                                        # Train Samples are not added - check later
                                        #instance["data"]["boardinfo"].pop("train_samples")

                                        tot_instances += 1
                                        #if tot_instances == 10:
                                        #    break
                                    #break
                                #break
                            #break
                        #break
                    #break


        print(
            f"Generated instances for - {self.game_name} game - {tot_instances} instances."
        )

    # an additional method, specific for our example
    def create_prompt(self, prompt: str, **kwargs) -> str:
        """Replace a prompt template with slot values."""
        #print(prompt,"\n")
        #print(kwargs)
        #input()
        text = string.Template(prompt).substitute(**kwargs)
        return text


if __name__ == "__main__":
    random.seed(SEED)
    # always call this, which will actually generate and save the JSON file
    CCBTSOptimizerInstanceGenerator().generate(seed=SEED)
