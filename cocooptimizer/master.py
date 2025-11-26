import os
import re
import copy
from copy import deepcopy
from typing import List, Dict, Tuple
import numpy as np
import json
from html import escape
from clemcore.clemgame.metrics import METRIC_ABORTED, METRIC_LOSE, METRIC_REQUEST_COUNT, \
    METRIC_REQUEST_COUNT_VIOLATED, METRIC_REQUEST_COUNT_PARSED, METRIC_SUCCESS, BENCH_SCORE
from clemcore.clemgame import DialogueGameMaster, GameBenchmark, GameScorer, GameSpec, Player, GameError, ParseError
from clemcore.backends import Model


from players import CodeOptimizer
from utils.prepareasciirep import PrepareASCIIRep



import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class CCBTSOptimizerMaster(DialogueGameMaster):
    def __init__(
        self,
        game_spec: GameSpec,
        experiment: Dict,
        player_models: List[str]
    ):
        super().__init__(game_spec, experiment, player_models)
        # save experiment and player attributes that will be necessary later
        logger.info(f"Initializing ImageCCBTSMaster: model_a = {player_models[0]} ")
        self.model_a = player_models[0]
        self.model_b = player_models[1] if len(player_models) > 1 else player_models[0]

    def _on_setup(self, **game_instance) -> None:
        """Setup the episode (mandatory)."""

        #logging.disable(logging.CRITICAL)
        self.prepare_ascii_rep = PrepareASCIIRep()
        self.instancedata = game_instance["data"]
        self.game_id = game_instance["game_id"]

        data = self.instancedata
        self.use_dspy_optim = data["use_dspy_optim"]
        self.use_dspy_optim_history = data["use_dspy_optim_history"]
        self.use_retry_for_optimization = data["use_dspy_optim_retry"]
        self.num_optim_retry = data["num_dspy_optim_retry"]        
        self.n_turns = data["n_turns"]
        self.board_info = data["boardinfo"]

        self.prompts_dict = data["prompts_dict"]
        self.prompt_player_a_base = self.prompts_dict["prompt_a"]
        self.prompt_player_a_human = self.prompts_dict["prompt_a_human"]        
        self.turn_prompt_a = self.prompts_dict.get("turn_prompt_a", "")
        self.turn_prompt_a_human = self.prompts_dict.get("turn_prompt_a_human", "")
        self.player_a_goal = data["boardinfo"]["target_board_rep"]

        self.combo_name = data["boardinfo"]["combo_name"]
        self.funcdef = data["func_def"]
        self.funcusage = data["func_usage"]
        self.inst_code_pairs = data["inst_code_pairs"]
        self.targetboard = data["boardinfo"]["board"]
        #self.targetboard_rep = data["boardinfo"]["target_board_rep"]
        self.targetboard_cells = data["boardinfo"]["target_board_cells"]

        if self.targetboard_cells is not None:
            for key, values in self.targetboard_cells.items():
                for index, val in enumerate(values):
                    self.targetboard_cells[key][index] = tuple(val)



        # initialise game variables:
        self.current_turn: int = 0

        self.log_key('n_turns', self.n_turns)
        self.turn_scores = [0] * (self.n_turns)

        # initialise attributes that will be used for the evaluation scores
        self.aborted: bool = False
        self.lose: bool = False
        self.success: bool = False
        self.complete_turns: int = 0
        self.set_pass_turn = True        

        self.current_optim_retry: int = 0
        self.used_retry_optim: bool = False

        # initialise common metrics:
        self.request_count: int = 0
        self.parsed_request_count: int = 0
        self.violated_request_count: int = 0 

        logger.info(f"GT Data:\n{self.inst_code_pairs}")

        # instantiate players:
        self.player_a = CodeOptimizer(self.model_a, "A", self.board_info["variant"], self.use_dspy_optim, self.use_dspy_optim_history)
        self.player_a_type = self.player_a.get_player_type()
        # add players, including assigning their initial prompts:
        if self.player_a_type == "human":
            self.prompt_player_a = self.prompt_player_a_human
        elif self.player_a_type == "programmatic":
            self.prompt_player_a = self.prompt_player_a_base
        else:
            if self.use_dspy_optim:
                self.prompt_player_a = self.player_a.get_player_prompt()
            else:
                self.prompt_player_a = self.prompt_player_a_base
        self.add_player(self.player_a)#, initial_prompt=self.prompt_player_a)

        self.gamedata = {
            "boardinfo": self.board_info,
            "funcdef": self.funcdef,
            "funcusage": self.funcusage,
            "gtinstruction_code_pairs": self.inst_code_pairs,
            "target_board_layer_rep": self.player_a_goal,
            "target_board_cells": self.targetboard_cells,
            "target_board": self.targetboard,
            "genresponse": None,
            "n_turns": self.n_turns,
            "play_turns": None,
            "loss_reason": None,
            "optimization_status": None,
            "use_dspy_optim": self.use_dspy_optim,
            "use_dspy_optim_history": self.use_dspy_optim_history,
            "max_optim_retry": self.num_optim_retry,
            "total_optim_retry": self.current_optim_retry,
            "used_retry_optim": self.used_retry_optim,
        }
        self.genresponse = []
        self.genboard = None
        self.gen_board_cells = None   

    def _on_before_game(self) -> None:
        """Initialise the dialogue history (firstlast specific)."""
        p1_data = f"Instruction-Code Pairs: {json.dumps(self.inst_code_pairs)}\nError Feedback: None"
        if self.player_a_type == "human":
            pass
        else:
            p1_messages = self.prompt_player_a+"\n"+str(p1_data)

        if self.use_dspy_optim:
            action = {'type': 'send message', 'content': p1_messages}
            self.log_event(from_='GM', to='Player 1', action=action)


        self.set_context_for(self.player_a, p1_messages)
        logger.info(f"Ground truth layer rep:\n{self.player_a_goal}")
        logger.info(f"Ground truth occupied cells:\n{self.targetboard_cells}")                 


    def _on_after_game(self) -> None:
        """Executed once at the end, after exiting the play loop."""
        #Do the game validation
        # log a final message saying that the game did come to an end:
        #action = {'type': 'info', 'content': 'end game'}
        #self.log_event(from_='GM', to='GM', action=action)
        self.gamedata["genresponse"] = self.genresponse
        #TODO: Check what to log here
        #self.gamedata["genboard"] = self.genboard
        self.gamedata["play_turns"] = self.current_round
        self._log_game_end()  

    def _set_pass_turn(self, player: Player, pass_turn) -> None:
        """Set the turn to be passed for a player (game specific)."""
        logger.info(f"Setting pass turn for player: {pass_turn}")
        self.set_pass_turn = pass_turn

    #def _should_pass_turn(self):
    #    #Currently not checking for any condition to pass the turn
    #    logger.info(f"Checking if turn should be passed: {self.set_pass_turn}")
    #    return self.set_pass_turn
    


    def _does_game_proceed(self) -> None:
        """Check if the game loop should continue (game specific)."""
        logger.info(f"Inside _does_game_proceed: Current Round: {self.current_round}, aborted: {self.aborted}, lose: {self.lose}, success: {self.success}")
        # Determine if the game should proceed. This is also called once initially.
        #if self.current_round < self.n_turns and not self.aborted and not self.lose and not self.success:
        if self.current_round < self.n_turns and not self.aborted and not self.lose and not self.success:        
            logger.info(f"Game continues: {self.current_round} < {self.n_turns}")
            return True

        if self.success:
            action_type = "info"
            action_content = "The game is successful; target board is reconstructed successfully."

        else:
            if not self.aborted:# and self.current_round == self.n_turns:
                self.lose = True

        logger.info(f"Game status: {self.success}, {self.lose}, {self.aborted}")

        if self.lose:
            action_type = "info"
            action_content = "Maximum turns reached; lost game"
        elif self.aborted:
            action_type = "invalid format"
            action_content = "The game has been aborted due to an invalid input."

        self.log_to_self(action_type, action_content)
        #self._log_game_end()
        return False

    def _advance_game(self, player: Player, parsed_response: Dict):
        """Advance the game with the parsed response."""
        logger.info(f"Advancing game with parsed response: player = {player}")
        if player == self.player_a:
            # The validitiy of the generated code can be checked during scoring.
            # If there are no issues in format, the game is considered successful.
            # increment current turn:
            self.current_turn += 1
            # increment complete turns:
            self.complete_turns += 1

            if parsed_response.get("status") == "success":
                #self._set_pass_turn(self.player_a, True)
                self.success = True
                self.correct_response = True
                #self.gencode = parsed_response
                # set the current turn's score to 1:
                self.turn_scores[self.current_turn-1] = 1


            elif parsed_response.get("status") == "failure":
                # No need to check if retry is allowed here; it is handled in _set_violated_req_count() which triggers parseerror
                #self._set_pass_turn(self.player_a, False)

                action_type = "info"
                action_content = "The player grid did not match with the target grid. Retrying..."

                self.log_to_self(action_type, action_content)                
                #self.lose = True
                # set the reason for the loss:
                #self.gamedata["loss_reason"] = parsed_response.get("error", "Unknown error")
                self.turn_scores[self.current_turn-1] = 0

    def _prepare_data_for_reuse(self):

        generated_board = self.targetboard
        generated_board_rep = self.player_a_goal
        gen_occupied_cells = self.targetboard_cells

        reuse_data = {  "board_info": self.board_info,
                        "use_dspy_optim": self.use_dspy_optim,
                        "use_dspy_optim_history": self.use_dspy_optim_history,
                        "use_optim_retry": self.use_retry_for_optimization,
                        "num_optim_retry": self.num_optim_retry,
                        "use_diff_human_prompts": None,
                        "optimization_status": self.success,
                        "n_turns": self.n_turns,
                        "played_turns": self.current_round,
                        "generated_board": generated_board,
                        "generated_board_rep": generated_board_rep,
                        "gen_occupied_cells": gen_occupied_cells
                    }
        return reuse_data
    
    def _prepare_function_header(self, func_name: str) -> str:
        return f"# Optimized function for object {func_name}\n" + f"# This function uses the following shapes:\n# {self.board_info['shapes']}\n\n"



    def _save_optimized_function(self, func_name: str, func_code: str, func_usage: str):
        func_header = self._prepare_function_header(func_name)
        self.gamedata["optimized_function"] = func_code
        self.gamedata["optimized_function_header"] = func_header
        self.gamedata["func_usage"] = func_usage
        self.gamedata["optimized_function_signature"] = f"def {func_name}(board, colors, x, y):"
        reuse_data = self._prepare_data_for_reuse()
        if reuse_data:
            reuse_data["optimized_function"] = func_code
            reuse_data["optimized_function_header"] = func_header

        reuse_data["func_usage"] = func_usage
        reuse_data["optimized_function_signature"] = f"def {func_name}(board, colors, x, y):"


        """Save the optimized function to a file."""
        os.makedirs("optimized_functions", exist_ok=True)
        filename = f"combo_name_{self.combo_name}_optimized_v1.json"
        if os.path.exists(filename):
            logger.info(f"File {filename} already exists.")
            current_version = filename.split("_v")[-1].split(".py")[0]
            if current_version.isdigit():
                new_version_num = int(current_version) + 1
            else:
                raise ValueError(f"Unexpected filename format: {filename} to increment version for saving optimized function.")

            filename = f"combo_name_{self.combo_name}_optimized_v{new_version_num}.json"

        with open(os.path.join("optimized_functions", filename), "w") as f:
            #json.dump(inst_code_pairs, f, indent=4)
            json.dump(reuse_data, f, indent=4)

        """
        with open(filename, "w") as f:
            f.write(f"# Optimized function for object {func_name}\n")
            f.write(f"# This function uses the following shapes:\n# {self.board_info['shapes']}\n\n")
            #f.write(f"# Import put(), move() etc functions as follows:\n#from coco import (\n#\tinit_board,\n#\tput,\n#\tmove,\n#\tremove,\n#\tclear,\n#\tundo\n#)\n\n")
            f.write(func_code + "\n\n")
            #Commenting function usage because that uses a specific colors and location values
            #f.write(f"# Function Usage:\n# create an empty board with dimensions as per the game\n# board=init_board(max_rows, max_columns)\n# {func_usage}\n")
        """            

    def _check_function_def(self, optim_func: str):
        """Check if the optimized function has the correct definition."""
        pattern = rf'def\s+{self.combo_name}\s*\(\s*board\s*,\s*colors\s*,\s*x\s*,\s*y\s*\)\s*:'
        if not re.search(pattern, optim_func):
            optim_func_error = f"Optimized function does not have the correct definition. Expected 'def {self.combo_name}(board, colors, x, y):'"
            return False, optim_func_error
        return True, None


    def _validate_optimized_code(self, optim_func):
        correct_def, optim_error = self._check_function_def(optim_func)
        if not correct_def:
            logger.error("Optimized function definition is incorrect. Retry")
            optim_error = f"Error feedback:\n{optim_error}"
            return False, optim_error

        usage = self.funcusage
        optim_error = None
        logger.info(f"Validating optimized code with usage:\n{usage}")
        optim_board, optim_error = self.prepare_ascii_rep.execute_optimized_response(self.board_info["size"], None, optim_func, usage)
        if optim_board is None:
            logger.error("Error executing optimized code. No board generated.")
            optim_error = f"Error feedback:\n{optim_error}"
            return False, optim_error
        optim_cells = self.prepare_ascii_rep.get_ascii_representation_from_board_forvalidation(optim_board, self.board_info["size"])
        #gt_cells = self.prepare_ascii_rep.get_ascii_representation_forvalidation(self.gtcode, self.board_info["size"])
        logger.info(f"Optimized board cells:\n{type(optim_cells)}, {optim_cells}")
        logger.info(f"Target board cells:\n{type(self.targetboard_cells)}, {self.targetboard_cells}")
        if optim_cells == self.targetboard_cells:
            logger.info("The optimized code generates the correct board.")
            return True, None
        else:
            logger.error("The optimized code does not generate the correct board.")
            diff_grid = self.prepare_ascii_rep.get_layer_representation_diff_for_optimization(self.targetboard_cells, optim_cells)
            return False, diff_grid
        
    def _handle_playera_response(self, response: str) -> str:
        return self._model_response_cleanup(response)

    def _prepare_playera_reprobe_response(self, optim_error):
        logger.info(f"Preparing reprobe response for Player A. Current turn: {self.current_turn}, Error:\n{optim_error}")

        input_data = f"Optimized function did not reconstruct the target grid correctly. Retry\nFunction Definition: def {self.combo_name}(board, colors, x, y)\n"# Function Usage: {self.funcusage}"

        turn_prompt_co = input_data + "\n" + f"Target Grid:\n{self.player_a_goal}\n{optim_error}"
        if not self.use_dspy_optim:
            add_anchors = "[[ ## prompt ## ]]"
            p1_data = add_anchors + "\n" + turn_prompt_co + "\n\n" + "Do not generate any other reasoning traces as it will fail code execution\n\n" + "Respond with the corresponding output fields, starting with the field `[[ ## optimized_function ## ]]`, and then ending with the marker for `[[ ## completed ## ]]`."
        else:
            p1_data = turn_prompt_co

        return p1_data


    def _parse_response(self, player: Player, response: str) -> str:
        # increase the number of API requests:
        self.request_count += 1
        logger.debug(f"Current turn: {self.current_turn}, Received response from player: {player}:{type(response)}")
        parse_a = {"status": "failure", "details": None, "error": None}
        if player == self.player_a:
            self._set_parsed_req_count()       
            optimized_function = self._handle_playera_response(response)
            logger.info(f"Parsed response from player A:\n{optimized_function}")

            action = {'type': 'parsed response',
                    'content': f"Optimized function:\n{optimized_function}"}
            self.log_event(from_='GM', to='GM', action=action)

            if optimized_function is None:
                error = "No optimized function found in the response."
                #self._set_violated_req_count(error)
                parse_a["status"] = "failure"
                parse_a["error"] = error
                return parse_a

            #action = {'type': 'get message',
            #          'content': optimized_function}
            #self.log_event(from_='Player 1', to='GM', action=action)

            optim_func_status, optim_error = self._validate_optimized_code(optimized_function)
            if optim_func_status:
                parse_a["status"] = "success"
                parse_a["details"] = optimized_function
                self.gamedata["optimization_status"] = {"status": parse_a["status"], "details": parse_a["details"], "error": None}
                self._save_optimized_function(self.combo_name, optimized_function, self.funcusage)
                return parse_a

            else:
                #self._set_violated_req_count(optim_error)
                #TODO: May need to add the turn prompt based on the value of current turn
                p2_prompt = self._prepare_playera_reprobe_response(optim_error)

                if self.use_dspy_optim:
                    action = {'type': 'send message', 'content': p2_prompt}
                    self.log_event(from_='GM', to='Player 2', action=action)

                #self.current_optim_retry += 1
                self.used_retry_optim = True
                self.gamedata["used_retry_optim"] = self.used_retry_optim  
                self.set_context_for(self.player_a, p2_prompt)           

            return parse_a              

    def _model_response_cleanup(self, response: str) -> str:
        clean_response = re.sub(r'```json(.*?)```', r'\1', response, flags=re.DOTALL).strip()
        clean_response = re.sub(r'```(.*?)```', r'\1', clean_response, flags=re.DOTALL).strip()
        clean_response = re.sub(r'```', '', clean_response).strip()
        #Remove [[ ## instruction ## ]] and [[ ## completed ## ]] from the response
        #clean_response = re.sub(r'\[\[\s*##\s*instruction\s*##\s*\]\]', '', clean_response, flags=re.IGNORECASE).strip()
        #clean_response = re.sub(r'\[\[\s*##\s*player_response\s*##\s*\]\]', '', clean_response, flags=re.IGNORECASE).strip()        
        clean_response = re.sub(r'\[\[\s*##\s*optimized_function\s*##\s*\]\]', '', clean_response, flags=re.IGNORECASE).strip()
        clean_response = re.sub(r'\[\[\s*##\s*completed\s*##\s*\]\]', '', clean_response, flags=re.IGNORECASE).strip()
        #Remove brackets like[[ or ]]
        clean_response = re.sub(r'(?m)^\s*\[\[\s*$','', clean_response).strip()
        clean_response = re.sub(r'(?m)^\s*\]\]\s*$','', clean_response).strip()
        return clean_response
    
    def _on_parse_error(self, error: ParseError):
        """Abort the game due to failed parsing."""
        logger.error(f"Parse error: {error}")
        # set the game to be aborted:
        self.aborted = True
        # increase the counter of requests that violate the move format rule:
        self.violated_request_count += 1
        # log the abortion event:
        action = {'type': 'invalid format', 'content': 'abort'}
        self.log_event(from_='GM', to='GM', action=action)              
        
    def _on_game_error(self, error: GameError):
        """Lose the game due to violated rules."""
        self.lose = True
        # log the fact that the game is now lost:
        action = {'type': 'rule violation',
                  'content': error.reason}
        self.log_event(from_='GM', to='GM', action=action)        

    def _set_parsed_req_count(self) -> None:
        # increase the counter of requests that conform to form rules
        self.parsed_request_count += 1  

        # log the event that the string was valid (no strange characters)
        action = {'type': 'valid response', 'content': 'response conforms to rules'}
        self.log_event(from_='GM', to='GM', action=action)

    def _set_violated_req_count(self, error) -> None:
        # increase the counter of requests that violate the move format rule
        self.violated_request_count += 1

        # log the event that the string was invalid (strange characters)
        # We are logging the error in ParseError, so no need to log it here
        #action = {'type': 'invalid format', 'content': f'response does not conform to rules. {error}'}
        #self.log_event(from_='GM', to='GM', action=action)

        retry = False
        if error:
            if self.use_retry_for_optimization and self.current_optim_retry < self.num_optim_retry:
                logger.info(f"Response did not conform to rules. Reprobing the player. Current retry: {self.current_optim_retry+1}")
                self.log_event(from_='GM', to='GM', action={'type': 'info', 'content': 'Response did not conform to rules. Reprobing the player.'})
                self.current_optim_retry += 1
                self.used_retry_optim = True
                self.gamedata["used_retry_optim"] = self.used_retry_optim
                retry = True
            else:
                logger.error(f"Response did not conform to rules. Reprobing tries exceeded.")
                self.log_event(from_='GM', to='GM', action={'type': 'info', 'content': 'Response did not conform to rules. Reprobing tries exceeded.'})
        if not retry:
            raise ParseError(error)

    def _log_game_end(self) -> None:
        """Aux to log variables needed for scoring (firstlast specific)"""
        self.log_key("Played turns", self.current_turn)
        self.log_key("Complete turns", self.complete_turns)
        self.log_key('Turn scores', self.turn_scores)        
        self.log_key(METRIC_ABORTED, self.aborted)
        self.log_key(METRIC_LOSE, self.lose)
        self.log_key(METRIC_SUCCESS, self.success)        
        self.log_key(METRIC_REQUEST_COUNT, self.request_count)
        self.log_key(METRIC_REQUEST_COUNT_PARSED, self.parsed_request_count)
        self.log_key(METRIC_REQUEST_COUNT_VIOLATED, self.violated_request_count)

        self.log_key("Evaluation", self.gamedata)
        logger.info("Game ended. Logged game data.")  

    def compute_turn_score(self):
        return self.turn_scores[self.current_turn-1]

    def compute_episode_score(self):
        """
        Calculate a score for the episode based on successful turns and target number of turns.
        Returns:
            Episode score value in range 0-100.
        """
        turn_score_sum = sum(self.turn_scores)
        success_ratio = turn_score_sum / self.n_turns
        return success_ratio * 100

class CCBTSOptimizerScorer(GameScorer):
    """Scorer for the firstlast game."""
    def __init__(self, game_name: str, experiment: Dict, game_instance: Dict):
        super().__init__(game_name, experiment, game_instance)
        #self.codevalidator = CodeValidator()        

    def score_turns(self, episode_interactions: Dict) -> None:
        """Calculate and log turn-level scores."""
        played_turns = episode_interactions['Played turns']
        turn_scores = episode_interactions['Turn scores']
        for turn in range(0, played_turns):
            self.log_round_score(turn, "turn score", turn_scores[turn])

    def log_main_score(self, episode_interactions: Dict):
        complete_turns = episode_interactions['Complete turns']
        n_turns = episode_interactions['n_turns']
        aborted = int(episode_interactions[METRIC_ABORTED])
        success = int(episode_interactions[METRIC_SUCCESS])
        # IMPORTANT: aborted episodes MUST have a bench score of NaN!
        bench_score = 1 if success else 0 if not aborted else np.nan
        self.log_episode_score(BENCH_SCORE, bench_score)

    def game_specific_score(self, episode_interactions: Dict) -> None:
        # check the validity of the code:
        board_size = episode_interactions["Evaluation"]["boardinfo"]["size"]
        variant = episode_interactions["Evaluation"]["boardinfo"]["variant"]
        #gtcode = episode_interactions["Evaluation"]["gtcode"]
        #gencode = episode_interactions["Evaluation"]["gencode"]
        # Compute all three metrics: EM, CB and ES
        # TODO: Add LLM Judge scores
    
      

    def compute_scores(self, episode_interactions: Dict) -> None:
        # Log turn-level scores
        self.score_turns(episode_interactions)
        # Log main score
        self.log_main_score(episode_interactions)
        # Log game-specific scores
        self.game_specific_score(episode_interactions)

     
class CCBTSOptimizerBenchmark(GameBenchmark):
    """Integrate the game into the benchmark run."""

    def __init__(self, game_spec: GameSpec):
        super().__init__(game_spec)

    # copy this, replacing the name of the game master in the return statement
    def create_game_master(
        self, experiment: Dict, player_models: List[Model]
    ) -> DialogueGameMaster:
        return CCBTSOptimizerMaster(self.game_spec, experiment, player_models)

    def create_game_scorer(self, experiment: Dict, game_instance: Dict) -> GameScorer:
        return CCBTSOptimizerScorer(self.game_name, experiment, game_instance)      