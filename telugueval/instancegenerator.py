"""
Generate instances for the game.

Creates files in ./in
"""
from tqdm import tqdm
import os
import logging
from clemcore.clemgame import GameInstanceGenerator

logger = logging.getLogger(__name__)

LANGUAGE = "te"


class TeluguEvalInstanceGenerator(GameInstanceGenerator):

    def __init__(self):
        super().__init__(os.path.dirname(__file__))

    def on_generate(self):
        # Create an experiment (here for mcq evaluation)
        experiment = self.add_experiment(f"{LANGUAGE}_nlu_qna_mcq")
        experiment["language"] = LANGUAGE  # experiment parameters
        experiment["required_tags"] = ["వివరణ", "సమాధానం"]

        # Load a list of prepared qna to choose from
        data_mcq = self.load_json(f"resources/nlu/qna/mcq/{LANGUAGE}/qna.json")

        # Load the prepared initial prompt
        prompt = self.load_template(f"resources/initial_prompts/{LANGUAGE}/prompt_nlu_qna_mcq.template")

        # We create one game for each name
        for game_id, qna_dict in tqdm(enumerate(data_mcq), desc="Generating instances"):
            # Replace the QUESTION in the templated initial prompt
            instance_prompt = prompt.replace("$QUESTION$", qna_dict['question'])

            # Create a game instance
            game_instance = self.add_game_instance(experiment, game_id)
            game_instance["prompt"] = instance_prompt  # game parameters
            game_instance["question"] = qna_dict['question']  # game parameters
            game_instance["answer"] = qna_dict['answer']


if __name__ == '__main__':
    # The resulting instances.json is automatically saved to the "in" directory of the game folder
    TeluguEvalInstanceGenerator().generate()
