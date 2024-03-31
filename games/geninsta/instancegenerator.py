import random
import string

from clemgame.clemgame import GameInstanceGenerator

from games.ccbts.utils.sampleformatter import get_incontext_samples

# set the name of the game in the script, as you named the directory
# this name will be used everywhere, including in the table of results
GAME_NAME = "geninsta"
# we will create 10 instances for each experiment; vary this as you wish
N_INSTANCES = 10
# if the generation involves randomness, remember to set a random seed
SEED = "42"


class GenInstaInstanceGenerator(GameInstanceGenerator):
    def __init__(self):
        # always do this to initialise GameInstanceGenerator
        super().__init__(GAME_NAME)   

    # define on_generate, a mandatory method
    def on_generate(self):
        # get the list of topics, which will be our experiments
        tests = self.load_json("resources/tests.json")
        # get the prompts for player a and player b
        # we'll keep the prompts fixed in all instances, replacing only the
        # necessary slots (but you can do it differently)

        game_id = 1
        for board in tests["boards"]:
            for board_object in tests[board]["objects"]:
                for variant in tests[board][board_object]["variants"]:
                    # create an experiment (for us, named after a topic)
                    experiment = self.add_experiment(f"{board}_{board_object}_{variant}")

                    self.train_samples = self.load_json(
                        f'resources/{tests[board][board_object][variant]["TRAIN_DATA_FILE_NAME"]}'
                    )
                    test_samples = self.load_json(
                        f'resources/{tests[board][board_object][variant]["TEST_DATA_FILE_NAME"]}'
                    )

                    prompt = self.load_template("resources/initial_prompts/prompt_a")
                    for board_type, objs_type in test_samples.items():
                        for obj, num_shapes in objs_type.items():
                            for total_shapes, combo_names in num_shapes.items():
                                for combo_name in num_shapes[total_shapes]:
                                    #samples_test = random.sample(test_samples[total_shapes][combo_name], 1)
                                    for sample in num_shapes[total_shapes][combo_name]:
                                    #for sample in samples_test:
                                        test_dialogues = sample["dialogues"][variant]["instructions"]
                                        n_turns = len(test_dialogues)

                                        # set the parameters
                                        # create a game instance, using a game_id counter/index
                                        instance = self.add_game_instance(experiment, game_id)
                                        # populate the game instance with its parameters
                                        instance["n_turns"] = n_turns
                                        instance["board_data"] = {
                                            "combo_name": sample["combo_name"],
                                            "shapes": sample["shapes"],
                                            "colors": sample["colors"],
                                            "x": sample["x"],
                                            "y": sample["y"],
                                            "dialogues": test_dialogues,
                                            "rows": tests["board"]["rows"],
                                            "cols": tests["board"]["cols"],
                                            "output_labels": ["Instructions"],
                                            "code": sample["code"],
                                        }
                                        # add the prompt to the game instance
                                        instance["prompt"] = prompt

                                        game_id += 1
        print(f"Generated instances for GenInsta game - {game_id - 1} instances.")




    # an additional method, specific for our example
    def create_prompt(self, prompt: str, **kwargs) -> str:
        """Replace a prompt template with slot values."""
        text = string.Template(prompt).safe_substitute(**kwargs)

        return text


if __name__ == "__main__":
    #random.seed(SEED)
    # always call this, which will actually generate and save the JSON file
    GenInstaInstanceGenerator().generate()    