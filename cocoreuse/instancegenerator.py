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
        self.game_name = "cocoreuse"
        self.prepare_ascii_rep = PrepareASCIIRep()



    def _prepare_prompts(self, variant: str, boardinfo, fill_labels) -> Dict[str, str]:

        prompt_files = {
            "prompt_a": f"resources/initial_prompts/{LANGUAGE}/initial_prompt_a.template",
            "turn_prompt_a": f"resources/initial_prompts/{LANGUAGE}/turn_prompt_a.template",
            "prompt_b": f"resources/initial_prompts/{LANGUAGE}/initial_prompt_b.template",
            "turn_prompt_b": f"resources/initial_prompts/{LANGUAGE}/turn_prompt_b.template",
            "prompt_a_human": f"resources/initial_prompts/{LANGUAGE}/initial_prompt_a_human.template",
            "turn_prompt_a_human": f"resources/initial_prompts/{LANGUAGE}/turn_prompt_a_human.template",
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
            train_samples = None
        else:
            train_samples = self.load_json(
                f'resources/data/{LANGUAGE}/{varconfig["TRAIN_DATA_FILE_NAME"]}'
            )

        if varconfig["TEST_DATA_FILE_NAME"] == "":
            test_samples = None
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
    
    def _prepare_skills_list(self, config, train_samples: list, test_samples: list) -> list:
        skills_list = {"train": [], "test": []}
        for index, sample in enumerate([train_samples, test_samples]):
            if index == 0:
                use_list_name = "train"
                use_list = train_samples
            else:
                use_list_name = "test"
                use_list = test_samples

            if sample is None:
                continue

            for board_type, objs_type in sample.items():
                for boardobj, num_shapes in objs_type.items():
                    for total_shapes, combo_names in num_shapes.items():
                        for combo_name in num_shapes[total_shapes]:
                            #print(len(num_shapes[total_shapes][combo_name]))
                            for tsample in num_shapes[total_shapes][combo_name]:
                                skill_details = ""
                                if config["use_function_header_in_prompt"]:
                                    skill_details = tsample["optimized_function_header"]

                                if config["use_func_signature_only_in_prompt"]:
                                    skill_details += tsample["optimized_function_signature"]
                                else:
                                    skill_details += tsample["optimized_function"]
                                skills_list[use_list_name].append(skill_details)

        with open(f"resources/skills_list_{LANGUAGE}.txt", "w") as f:
            for data_type, skills in skills_list.items():
                if skills is None:
                    continue
                for skill in skills:
                    f.write(skill + "\n\n\n")

        print(len(skills_list["train"]), len(skills_list["test"]))
        return skills_list


    # define on_generate, a mandatory method
    def on_generate(self, seed: int, **kwargs):
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
                    num_ic_samples = config[board][obj][variant]["NUM_INCONTEXT_SAMPLES"]
                    ic_type = f"fs_{num_ic_samples}" if num_ic_samples > 0 else "zs"
                    experiment = self.add_experiment(f"{board}_{obj}_{variant}_{ic_type}")
                    samples = self._prepare_samples_labels(config[board][obj][variant])
                    total_available_skills = self._prepare_skills_list(config, samples["train"], samples["test"])


                    for board_type, objs_type in samples["test"].items():
                        for boardobj, num_shapes in objs_type.items():
                            for total_shapes, combo_names in num_shapes.items():
                                for combo_name in num_shapes[total_shapes]:
                                    #print(len(num_shapes[total_shapes][combo_name]))
                                    for tsample in num_shapes[total_shapes][combo_name]:
                                        #if total_shapes not in ["2"]:# or "b" in combo_name:
                                        #    continue

                                        combo_name = tsample["combo_name"]
                                        if "optimized_function_header" in tsample:
                                            func_header = tsample["optimized_function_header"]
                                            func_signature = tsample["optimized_function_signature"]
                                            func_definition = tsample["optimized_function"]
                                            func_usage = tsample["func_usage"]
                                        else:
                                            func_header = ""
                                            func_signature = f"def {combo_name}(board, colors, x, y)"
                                            func_definition = tsample["code"]["single_turn"]["function"]
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

                                        if target_board_rep is None:
                                            gt_code = tsample["code"]["single_turn"]                                            
                                            ascii_rep_board, board_rep = self.prepare_ascii_rep.get_ascii_representation(gt_code, board_size)
                                            target_board_rep = ascii_rep_board
                                            target_board = board_rep
                                            target_board_cells = self.prepare_ascii_rep.get_occupied_cells_from_board(board_rep)

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

                                        #samples["prompt_incontext_labels"]["GOAL"] = target_board_rep#ascii_rep_board
                                        #samples["prompt_incontext_labels"]["OBJECT_NAME"] = combo_name
                                        #samples["prompt_incontext_labels"]["ERROR_FEEDBACK"] = "ERROR_FEEDBACK"
                                        #samples["prompt_incontext_labels"]["INSTRUCTION"] = "\n"#"$INSTRUCTION"
                                        samples["prompt_incontext_labels"]["GRID_SIZE"] = f"{board_size['rows']} x {board_size['cols']}"
                                        samples["prompt_incontext_labels"]["SKILL_NAME"] = combo_name
                                        samples["prompt_incontext_labels"]["COLORS"] = tsample["colors"]
                                        samples["prompt_incontext_labels"]["LOCATION"] = {"row": tsample["x"][0]+1, "col": tsample["y"][0]+1}
                                        samples["prompt_incontext_labels"]["SKILLS_DEFINITIONS"] = "\n".join(total_available_skills["test"])

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
                                        instance["data"]["use_dspy_reuse"] = config["use_dspy_reuse"]
                                        instance["data"]["use_dspy_reuse_history"] = config["use_dspy_reuse_history"]
                                        instance["data"]["use_function_header_in_prompt"] = config["use_function_header_in_prompt"]
                                        instance["data"]["use_func_signature_only_in_prompt"] = config["use_func_signature_only_in_prompt"]
                                        instance["data"]["use_diff_human_prompts"] = config["use_diff_human_prompts"]
                                        instance["data"]["num_reuse_retry"] = config["num_reuse_retry"]
                                        instance["data"]["n_turns"] = n_turns
                                        instance["data"]["ascii_rep"] = target_board_rep#ascii_rep_board
                                        instance["data"]["func_header"] = func_header
                                        instance["data"]["func_signature"] = func_signature
                                        instance["data"]["func_definition"] = func_definition
                                        instance["data"]["func_usage"] = func_usage
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
