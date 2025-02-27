import string
import re
from typing import Dict, List, Tuple

from clemcore.backends import Model, CustomResponseModel, ContextExceededError
from clemcore.clemgame import GameBenchmark, GameScorer, Player, DialogueGameMaster, GameSpec
from clemcore.clemgame.metrics import METRIC_ABORTED, METRIC_LOSE, METRIC_REQUEST_COUNT, \
    METRIC_REQUEST_COUNT_VIOLATED, METRIC_REQUEST_COUNT_PARSED, METRIC_SUCCESS

import logging

logger = logging.getLogger(__name__)


class Guesser(Player):

    def __init__(self, model_name: str):
        super().__init__(model_name)
        #Enable this for generating mock responses
        #super().__init__(CustomResponseModel())

    def __call__(self, history, current_turn):
        try:
            return super().__call__(history, current_turn)
        except ContextExceededError:
            prompt = history[-1]
            return prompt, "CONTEXT EXCEEDED" , "CONTEXT EXCEEDED!"


    def _custom_response(self, messages, turn_idx):
        return "వివరణ:వివరణ\nసమాధానం:1"


class TeluguEvalGame(DialogueGameMaster):
    """This class implements a greeting game in which player A
    is greeting another player with a target name.
    """

    def __init__(self, game_name: str, game_path: str, experiment: Dict, player_models: List[Model]):
        super().__init__(game_name, game_path, experiment, player_models)
        self.language: int = experiment["language"]  # fetch experiment parameters here
        self.turns = []
        self.required_tags = experiment["required_tags"]
        self.aborted = False
        self.lost = False
        self.success = False
        self.number_of_turns = 0
        self.request_count = 0
        self.parsed_request_count = 0
        self.violated_request_count = 0


        self.model_a: str = player_models[0]  

    def _on_setup(self, **game_instance):
        self.game_instance = game_instance  # fetch game parameters here
        self.eval_answer = game_instance["answer"]

        # Create the players
        self.guesser = Guesser(self.model_a)


        # Add the players: these will be logged to the records interactions.json
        # Note: During game play the players will be called in the order added here
        self.add_player(self.guesser)
        logger.debug("Added player", self.guesser)



    def _on_before_game(self):
        # Do something before the game start e.g. add the initial prompts to the message list for the players
        self.add_user_message(self.guesser, self.game_instance["prompt"])
        logger.debug("Set the prompt")

    def _does_game_proceed(self):
        # Determine if the game should proceed. This is also called once initially.
        if len(self.turns) == 0:
            return True
        return False

    def _validate_player_response(self, player: Player, utterance: str) -> bool:
        # Check responses for specific players
        self.request_count += 1        
        logger.debug(f"Validating response, utterance: {utterance}")
        if player == self.guesser:
            # Check rule: utterance starts with key word
            if not utterance.startswith(self.required_tags[0]):
                self.aborted = True
                self.violated_request_count += 1
                return True
            # Check rule: required tags are included
            for required_tags in self.required_tags:
                if required_tags not in utterance:
                    self.aborted = True
                    self.violated_request_count += 1
        return True

    def _on_after_turn(self, turn_idx: int):
        self._log_game_end()        
        self.turns.append(self.success)

    def _on_parse_response(self, player: Player, utterance: str) -> Tuple[str, bool]:
        self.parsed_request_count += 1
        logger.debug(f"Parsing response, utterance: {utterance}")
        if player == self.guesser:
            explanation_match = re.search(rf'{self.required_tags[0]}\s*:\s*(.+)', utterance, re.UNICODE)
            answer_match = re.search(rf'{self.required_tags[1]}\s*:\s*(.+)', utterance, re.UNICODE)
            gen_explanation = None
            gen_answer = None
            if explanation_match:
                gen_explanation = explanation_match.group(1)
                logger.info(f"Extracted Explanation: {gen_explanation}")
            if answer_match:
                gen_answer = answer_match.group(1)
                if bool(re.fullmatch(r"\d+", gen_answer)):
                    gen_answer = int(gen_answer)
                else:
                    gen_answer = None
                logger.info(f"Extracted Answer: {gen_answer}")
            return {"explanation": gen_explanation, "answer": gen_answer}, True


    def _after_add_player_response(self, player: Player, response: Dict):
        logger.info(f"Received player response: {response} {self.required_tags}")
        if player == self.guesser:
            #Do the validation here
            if response['explanation'] is None or response['answer'] is None:
                self.abort = True
                self.log_to_self("Answer Validation", {"ground truth": self.eval_answer, "generated": response, "success": self.success})
                return

            gen_answer = response["answer"]
            logger.info(f"Gen Answer: {gen_answer}, Eval Answer: {self.eval_answer}")

            if int(gen_answer) == int(self.eval_answer):
                logger.info("Correct answer")
                self.success = True
            else:
                logger.info("Incorrect answer")
                self.lost = True
            self.log_to_self("Answer Validation", {"ground truth": self.eval_answer, "generated": gen_answer, "success": self.success})

    def _log_game_end(self):
        # log everything that is needed for score calculation and game evaluation
        self.log_key(METRIC_ABORTED, self.aborted)
        self.log_key(METRIC_LOSE, self.lost)
        self.log_key(METRIC_SUCCESS, self.success)
        self.log_key(METRIC_REQUEST_COUNT, self.request_count)
        self.log_key(METRIC_REQUEST_COUNT_PARSED, self.parsed_request_count)
        self.log_key(METRIC_REQUEST_COUNT_VIOLATED, self.violated_request_count)




class TeluguEvalScorer(GameScorer):
    def __init__(self, game_name: str, experiment_config, game_instance):
        super().__init__(game_name, experiment_config, game_instance)

    def compute_scores(self, episode_interactions: Dict) -> None:
        score = 0
        success = episode_interactions[METRIC_SUCCESS]

        if success:
            score = 1
        self.log_episode_score('Accuracy', score)


class TeluguEvalGameBenchmark(GameBenchmark):

    def __init__(self, game_spec: GameSpec):
        super().__init__(game_spec)

    def create_game_master(self, experiment: Dict, player_models: List[Model]) -> DialogueGameMaster:
        return TeluguEvalGame(self.game_name, self.game_path, experiment, player_models)
    
    def create_game_scorer(self, experiment_config, game_instance) -> GameScorer:
        return TeluguEvalScorer(self.game_name, experiment_config, game_instance)    
