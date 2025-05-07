import random
import copy
from typing import List, Dict, Tuple
from string import ascii_lowercase as letters
import importlib

import numpy as np
import json

import clemcore.clemgame.metrics as ms
from clemcore.clemgame import GameMaster, GameBenchmark, GameScorer, GameSpec
from clemcore.backends import Model
#from clemcore import get_logger

from instancegenerator import GAME_NAME
from codevalidator import CodeValidator
from computemetrics import ComputeMetrics

# use the framework logger to log events relevant at runtime;
# this is independent from the game records / transcript
import logging

logger = logging.getLogger(__name__)



class ProgSynthMaster(GameMaster):
    def __init__(
        self,
        gamename: str,
        game_path: str,
        experiment: Dict,
        player_backends: List[str],
        other_modules: classmethod,
    ):
        super().__init__(gamename, game_path, experiment, player_backends)
        # save experiment and player attributes that will be necessary later
        self.model_a = player_backends[0]

        # initialise attributes that will be used for the evaluation scores
        self.aborted: bool = False
        self.lose: bool = False
        self.success: bool = False
        self.complete_turns: int = 0

    def setup(self, data: Dict, game_id: int) -> None:
        """Setup the episode (mandatory)."""

        #logging.disable(logging.CRITICAL)
        self.instancedata = data

        self.n_turns = data["n_turns"]
        self.userinst = data["user_instruction"]
        self.gtcode = data["gt_code"]
        self.board_info = data["boardinfo"]
        self.prompts_dict = data["prompts_dict"]
        self.output_labels = data["output_labels"]
        self.prompt_player_a = self.prompts_dict["prompt_a"]

        logger.info(f"User Goal: {self.goal}")
        logger.info(f"Ground Truth Code: {self.gtcode["total_code"]}")
        self.codevalidator = CodeValidator(self.gtcode)

        # initialise game variables
        self.current_turn: int = 0

        # initialise common metrics
        self.request_counts = [0] * (self.n_turns + 1)
        self.parsed_request_counts = [0] * (self.n_turns + 1)
        self.violated_request_counts = [0] * (self.n_turns + 1)   

        self.gamedata = {
            "boardinfo": self.board_info,
            "instruction": self.userinst,
            "gt_code": self.gtcode,
            "gencode": None,
            "n_turns": self.n_turns,
            "play_turns": None,
        }
        self.gencode = None            

        # add initial prompts to each player's messages
        self.initiate(self.prompt_player_a, None)

        # always log the details of the players in this format (see logdoc)
        self.log_players(
            {
                "GM": "Game master for DMSystem",
                "Player 1": f"Player A: {self.model_a}",
            }
        )

        # log any additional keys that will be relevant for evaluation
        self.log_key("n_turns", self.n_turns)

    def initiate(self, prompt_player_a: str, prompt_player_b: str) -> None:
        """Initialise the dialogue history (firstlast specific)."""
        # always call log_next_turn what a turn starts
        self.log_next_turn()

        # append the initial message of each player to their history
        # the value user means the message is from an interlocutor of the model
        self.player_a.history.append({"role": "user", "content": prompt_player_a})

        # also log the messages as events for the transcriptions
        #action = {"type": "send message", "content": prompt_player_a}
        #self.log_event(from_="GM", to="Player 1", action=action)


    def proceed(self) -> None:
        """Check if the game loop should continue (dmsystem specific)."""
        return (
            self.current_turn < self.n_turns
            and not self.aborted
            and not self.lose
            and not self.success
        )
    
    def play(self) -> None:
        """Play the game until the end (mandatory)."""
        # play the game
        while self.proceed():
            self.current_turn += 1
            # always call log_next_turn when a new turn starts
            self.log_next_turn()
            self.turn()

        #If the game is aborted, in turn() self.aborted is set to True, no need to check here
        if self.complete_turns == self.n_turns:
            status = self.codevalidator.validate_code(self.gencode)
            if status:
                self.success = True
            else:
                self.lose = True

        self.gamedata["gencode"] = self.gencode
        self.gamedata["play_turns"] = self.complete_turns

      
        if self.success:
            action_content = "The game is successful; all the generated data matched."
        elif self.lose:
            action_content = "Lost game"
        elif self.aborted:
            action_content = "The game has been aborted due to an invalid input."
        else:
            action_content = "Game ended with an unknown status."

        action = {"type": "info", "content": action_content}

        self.log_event(from_="GM", to="GM", action=action)

        # Log the prompt of the player to understand the flow
        #action = {"type": "player prompt", "content": self.dsystem.get_player_prompt()}
        #self.log_event(from_="GM", to="GM", action=action)


        # log a final message saying that the game did came to an end
        #action = {"type": "info", "content": "end game"}
        #self.log_event(from_="GM", to="GM", action=action)
        # log all temporary game variables that are needed for evaluation
        self.log_eval_assets()

    def log_eval_assets(self) -> None:
        """Aux to log variables needed for scoring (firstlast specific)"""
        self.log_key("Played turns", self.current_turn)
        self.log_key("Complete turns", self.complete_turns)
        self.log_key(ms.METRIC_ABORTED, self.aborted)
        self.log_key(ms.METRIC_LOSE, self.lose)
        self.log_key(ms.METRIC_REQUEST_COUNT, self.request_counts)
        self.log_key(ms.METRIC_REQUEST_COUNT_PARSED, self.parsed_request_counts)
        self.log_key(ms.METRIC_REQUEST_COUNT_VIOLATED, self.violated_request_counts)
        self.log_key("Evaluation", self.gamedata)


    def parse(self, response: str) -> Dict[str, str]:
        """Check if utterance is valid and contains defined labels."""
        try:
            answer = {label: response.split(value)[1].strip() if value in response else None
                    for label, value in self.output_labels.items() if value is not None}
            

            logger.info(f"Parsed Answer: {answer}")
            input()

            missing_labels = []
            if None in answer.values():
                missing_labels = [label for label, result in answer.items() if result is None]
                logger.error(f"Labels {missing_labels} not found in response: {response}")
                #return None
            
            if missing_labels:
                if "output" in missing_labels:
                    answer["output"] = response.strip()
                if "function" in missing_labels:
                    answer["function"] = response.strip()
                if "usage" in missing_labels:
                    answer["usage"] = ""


            logger.info(f"After parsing: answer = {answer}")
            return answer
        except Exception as e:
            logger.error(f"An error occurred while parsing the answer: {e}")
            return None


    def _check_validity(self, answer: str) -> bool:
        """Check if answer is valid and correct (firstlast specific)."""
        # parse answer
        answer = self.parse(answer)
        if answer is None:
            self.aborted = True
            # log the abortion event
            action = {'type': 'invalid format', 'content': 'abort'}
            self.log_event(from_='GM', to='GM', action=action)
            # increase the counter of requests that violate form rules
            self.violated_request_counts[self.current_turn] += 1
            return False

        self.gencode = answer
        action = {"type": "metadata", "content": "response confirms to rules"}
        self.log_event(from_="GM", to="GM", action=action)
        return True


    def _get_code(self, player: str) -> str:
        """Get utterance from a player and log it (firstlast specific)."""
        assert player in ("a", "b")
        if player == "a":
            if self.current_turn == 1:
                self.player_a.history[-1]["content"] += "\n\n" + self.userinst

            action = {'type': 'send message', 'content': self.player_a.history[-1]["content"]}
            self.log_event(from_='GM', to='Player 1', action=action)

            # make an API call (or get a programmatic response) from player a
            prompt, raw_answer, answer = self.player_a(
                self.player_a.history, self.current_turn, None, None
            )
            # add API call to the records
            action = {"type": "get message", "content": answer}
            self.log_event(
                from_="Player 1",
                to="GM",
                action=action,
                call=(copy.deepcopy(prompt), raw_answer),
            )

        # increase the number of API requests
        # TODO: For Modular DM, there are multiple calls to the sub-modules which are not counted here
        self.request_counts[self.current_turn] += 1
        return answer


    def turn(self) -> None:
        """Perform a game turn, utterances by A and B (firstlast specific)."""
        # TODO: Where to add violated requests?
        # get player A's reply and add it to its history
        answer_a = self._get_code("a")

        logger.info(f"Received answer from player A: {answer_a}")
        # check if the game should be aborted or lost
        is_valid_turn = self._check_validity(answer_a, "a")
        if not is_valid_turn:
            # stop game
            self.aborted = True
            return None

        self.complete_turns += 1

class ProgSynthScorer(GameScorer):
    def __init__(self, game_name: str, experiment: Dict, game_instance: Dict):
        super().__init__(game_name, experiment, game_instance)
        self.cm = ComputeMetrics()

    def compute_scores(self, episode_interactions: Dict) -> None:
        played_turns = episode_interactions["Played turns"]
        complete_turns = episode_interactions["Complete turns"]
        # turn 0 was only the initial prompts, so we disregard it here
        reqs = episode_interactions[ms.METRIC_REQUEST_COUNT][1:]
        p_reqs = episode_interactions[ms.METRIC_REQUEST_COUNT_PARSED][1:]
        v_reqs = episode_interactions[ms.METRIC_REQUEST_COUNT_VIOLATED][1:]
        n_turns = len(reqs)

        for turn in range(0, played_turns):
            self.log_turn_score(turn, ms.METRIC_REQUEST_COUNT, reqs[turn])
            self.log_turn_score(turn, ms.METRIC_REQUEST_COUNT_PARSED, p_reqs[turn])
            self.log_turn_score(turn, ms.METRIC_REQUEST_COUNT_VIOLATED, v_reqs[turn])

        aborted = int(episode_interactions[ms.METRIC_ABORTED])
        lose = int(episode_interactions[ms.METRIC_LOSE]) if not aborted else 0
        success = 1 - lose if not aborted else 0
        bench_score = complete_turns / n_turns if not aborted else np.nan

        self.log_episode_score(ms.METRIC_ABORTED, aborted)
        self.log_episode_score(ms.METRIC_LOSE, lose)
        self.log_episode_score(ms.METRIC_SUCCESS, success)
        self.log_episode_score(ms.METRIC_REQUEST_COUNT, sum(reqs))
        self.log_episode_score(ms.METRIC_REQUEST_COUNT_PARSED, sum(p_reqs))
        self.log_episode_score(ms.METRIC_REQUEST_COUNT_VIOLATED, sum(v_reqs))
        self.log_episode_score(ms.METRIC_REQUEST_SUCCESS, sum(p_reqs) / sum(reqs))
        self.log_episode_score(ms.BENCH_SCORE, bench_score)

        self.log_episode_score("Played turns", played_turns)
        self.log_episode_score("Complete turns", complete_turns)
        self.log_episode_score("Max turns", n_turns)

        #TODO: Need to add game specific metrics : Exact match, CodeBLEU, and Execution Success



class DMSystemBenchmark(GameBenchmark):
    """Integrate the game into the benchmark run."""

    def __init__(self, game_spec: GameSpec):
        super().__init__(game_spec)

    # defines whether the game is single player or not
    def is_single_player(self):
        return True

    # add a description of your game
    def get_description(self):
        return (
            "A simple game in which a human collaborate with a bot to complete a task."
        )

    # copy this, replacing the name of the game master in the return statement
    def create_game_master(
        self, experiment: Dict, player_models: List[Model]
    ) -> GameMaster:
        return ProgSynthMaster(self.game_name, self.game_path, experiment, player_models, None)

    def create_game_scorer(self, experiment_config, game_instance) -> GameScorer:
        return ProgSynthScorer(self.game_name, experiment_config, game_instance)