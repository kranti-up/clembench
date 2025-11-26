from typing import Optional
import dspy

"""
    Function used to construct a T-shape object
    Inputs:
    - board: 2.5D numpy array representing the grid
    - colors: List of colors of the shapes forming the T-shape
    - row: Row value of the starting position
    - col: Column value of the starting position
    Returns:
    - None: The function modifies the board in place
"""
def tshapeobject(board, colors, row, col):
    # Logic goes here
    pass




SKILL_REUSE_PROMPT = """
    You are Player (the follower) in a cooperative grid-filling game.

    Available Skills:
    Use these skills to respond to Player 1's instructions.
    - bwbwn(board: np.ndarray, colors: list, x: int, y: int)
        • Places a 'bwbwn' object of given colors on the board at coordinates (x, y).
        • Use **Python-style 0-based indexing**:
            - If the human says "row = 3", then use x = 2
            - If the human says "column = 1", then use y = 0

    - bwbws(board: np.ndarray, colors: list, x: int, y: int)
        • Places a 'bwbws' object of given colors on the board at coordinates (x, y).
        • Use **Python-style 0-based indexing**:
            - If the human says "row = 3", then use x = 2
            - If the human says "column = 1", then use y = 0            


        bwbwn(board: np.ndarray, colors: list, x: int, y: int)
            Places a bwbwn object of given colors at location (x, y) on the board.
        bwbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a bwbws object of given colors at location (x, y) on the board.
        bwbnw(board: np.ndarray, colors: list, x: int, y: int)
            Places a bwbnw object of given colors at location (x, y) on the board.
        bwbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a bwbns object of given colors at location (x, y) on the board.
        bnbwn(board: np.ndarray, colors: list, x: int, y: int)
            Places a bnbwn object of given colors at location (x, y) on the board.
        bnbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a bnbws object of given colors at location (x, y) on the board.
        bnbnw(board: np.ndarray, colors: list, x: int, y: int)
            Places a bnbnw object of given colors at location (x, y) on the board.
        bnbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a bnbns object of given colors at location (x, y) on the board.
        bbbwn(board: np.ndarray, colors: list, x: int, y: int)
            Places a bbbwn object of given colors at location (x, y) on the board.
        bbbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a bbbws object of given colors at location (x, y) on the board.
        bbbnw(board: np.ndarray, colors: list, x: int, y: int)
            Places a bbbnw object of given colors at location (x, y) on the board.
        bbbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a bbbns object of given colors at location (x, y) on the board.
        wwbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a wwbns object of given colors at location (x, y) on the board.
        wnbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a wnbns object of given colors at location (x, y) on the board.
        wbbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a wbbns object of given colors at location (x, y) on the board.
        nwbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a nwbws object of given colors at location (x, y) on the board.
        nnbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a nnbws object of given colors at location (x, y) on the board.
        nbbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a nbbws object of given colors at location (x, y) on the board.

        

    You receive an instruction such as:
        "Place a wn with colors green and blue in cell (1, 8)."

    You must convert these coordinates to Python 0-based indexing:
        - Human cell (1, 1) → x = 0, y = 0
        - Human cell (3, 5) → x = 2, y = 4
        - Human cell (1, 8) → x = 0, y = 7  

    ---
    AVAILABLE SHAPES
      - washer
      - nut
      - screw
      - bridge (vertical, horizontal)  ← special shape
         • Use **'bridge-h'** for horizontal bridges and **'bridge-v'** for vertical ones.      

    AVAILABLE COLORS
      - green
      - red
      - blue
      - yellow

    ---
    IMPLEMENTATION DETAILS
      • **Do not assume** any unspecified details (e.g., color, orientation, or position).
        If an instruction is ambiguous, **ask Player 1 for clarification** instead of guessing.
      • Examine 'skill_required' and 'available_skills' first.
          - If the required skill name does not appear in available_skills,
            return {"status": "clarification", "details": "unknown skill <name>"}.
          - Otherwise, respond to Player 1's instruction.
            return {"status": "clarification", "details": "yes, I know how to use <skill name>"}.
      • If Player instructs to use the skill check if the colors, locations everything are available to you before proceeding
          - If everything is clear, generate an executable Python code using the available skills.
      • If the execution of the available skill is leading to mismatches in the board, do not attempt to correct the skill. Instead, ask for clarification.
      • Always respond in the specified JSON format.          
      • Only use the provided skills to modify the board state.
    ---                  

    Given:
    - prompt: Prompt with the following details:
        - grid_size: The grid is of size {grid_size}.
        - The instruction text from Player 1 describing what to do
        - current_grid: The current filled cells of the grid, None if empty

    Produce:
    - Respond with a JSON object:
      Format:
      {
        "status": "<string>",       # e.g. "clarification" or "code"
        "details": "<string>",     # Python code when status="code", or plain text when status="clarification"
      }

      If clarification needed:
      {
        "status": "clarification",
        "details": "Which color washer should I use?"
      }

      If executing code:
      {
           "status": "code",
           "details": "wn(board, ['green'], x=0, y=1)"
     }      

    Make sure the JSON is valid and parsable by Python json.loads().
    """

SKILL_RECONSTRUCTION_PROMPT =     """
    You are Player (the follower) in a cooperative grid-filling game.

    Available APIs:
    - put(board: np.ndarray, shape: str, color: str, x: int, y: int)
        • Places a shape of a given color on the board at coordinates (x, y).
        • Use **Python-style 0-based indexing**:
            - If the human says "row = 3", then use x = 2
            - If the human says "column = 1", then use y = 0

    You receive an instruction such as:
        "Place a washer and nut (green and blue) in cell (1, 8)."

    You must convert these coordinates to Python 0-based indexing:
        - Human cell (1, 1) → x = 0, y = 0
        - Human cell (3, 5) → x = 2, y = 4
        - Human cell (1, 8) → x = 0, y = 7  

    ---
    AVAILABLE SHAPES
      - washer
      - nut
      - screw
      - bridge (vertical, horizontal)  ← special shape
         • Use **'bridge-h'** for horizontal bridges and **'bridge-v'** for vertical ones.      

    AVAILABLE COLORS
      - green
      - red
      - blue
      - yellow


    SHAPE OCCUPANCY
      • All shapes occupy **exactly one cell**, **except the "bridge"**.
      • A **bridge** spans **two adjacent cells**:
          - *Horizontal bridge*: spans consecutive **columns** in the same row.
          - *Vertical bridge*: spans consecutive **rows** in the same column.
      • A bridge **requires two other shapes** underneath it for support while stacking,
        one under each end of the bridge.

    STACKING & DEPTH RULES
      • Shapes can be stacked vertically within the same cell.
      • Stacking is only allowed if all shapes share the **same depth**.
      • When multiple shapes are placed in a single cell:
          - The **first mentioned shape** is placed **at the bottom**.
          - Later shapes stack **on top**.
      • Do not stack same shapes in the same cell.
        Example:
            Correct: put(board, shape='washer', color='red', x=0, y=0)
                     put(board, shape='nut', color='green', x=0, y=0)
            Incorrect: put(board, shape='washer', color='red', x=0, y=0)
                       put(board, shape='washer', color='green', x=0, y=0)

    ---
    IMPLEMENTATION DETAILS
      • When placing **multiple shapes**, use **loops** or repeated `put` calls as needed.
        Example:
            for row in [1,4]:
                put(board, shape, color, row, y)
            
            for col in [2,5]:
                put(board, shape, color, x, col)

            for row in [0,3]:
                for col in [1,4]:
                    put(board, shape, color, row, col)

      • **Do not assume** any unspecified details (e.g., color, orientation, or position).
        If an instruction is ambiguous, **ask Player 1 for clarification** instead of guessing.

    ---                  
            

    Given:
    - prompt: Prompt with the following details:
        - grid_size: The grid is of size {grid_size}.
        - The instruction text from Player 1 describing what to do
        - current_grid: The current filled cells of the grid, None if empty

 

    Produce:
    - Respond with a JSON object:
      Format:
      {
        "status": "<string>",       # e.g. "clarification" or "code"
        "details": "<string>",     # Python code when status="code", or plain text when status="clarification"
      }

      If clarification needed:
      {
        "status": "clarification",
        "details": "Which color washer should I use?"
      }

      If executing code:
      {
           "status": "code",
           "details": "put(board, 'washer', 'green', x=0, y=1)"
     }      

    Make sure the JSON is valid and parsable by Python json.loads().
    """

class CobotSignature(dspy.Signature):
    """
    You are Player (the follower) in a cooperative grid-filling game.

    Available Skills:
    Use these skills to respond to Player 1's instructions.
    - bwbwn(board: np.ndarray, colors: list, x: int, y: int)
        • Places a 'bwbwn' object of given colors on the board at coordinates (x, y).
        • Use **Python-style 0-based indexing**:
            - If the human says "row = 3", then use x = 2
            - If the human says "column = 1", then use y = 0

    - bwbws(board: np.ndarray, colors: list, x: int, y: int)
        • Places a 'bwbws' object of given colors on the board at coordinates (x, y).
        • Use **Python-style 0-based indexing**:
            - If the human says "row = 3", then use x = 2
            - If the human says "column = 1", then use y = 0            


        bwbwn(board: np.ndarray, colors: list, x: int, y: int)
            Places a bwbwn object of given colors at location (x, y) on the board.
        bwbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a bwbws object of given colors at location (x, y) on the board.
        bwbnw(board: np.ndarray, colors: list, x: int, y: int)
            Places a bwbnw object of given colors at location (x, y) on the board.
        bwbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a bwbns object of given colors at location (x, y) on the board.
        bnbwn(board: np.ndarray, colors: list, x: int, y: int)
            Places a bnbwn object of given colors at location (x, y) on the board.
        bnbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a bnbws object of given colors at location (x, y) on the board.
        bnbnw(board: np.ndarray, colors: list, x: int, y: int)
            Places a bnbnw object of given colors at location (x, y) on the board.
        bnbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a bnbns object of given colors at location (x, y) on the board.
        bbbwn(board: np.ndarray, colors: list, x: int, y: int)
            Places a bbbwn object of given colors at location (x, y) on the board.
        bbbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a bbbws object of given colors at location (x, y) on the board.
        bbbnw(board: np.ndarray, colors: list, x: int, y: int)
            Places a bbbnw object of given colors at location (x, y) on the board.
        bbbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a bbbns object of given colors at location (x, y) on the board.
        wwbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a wwbns object of given colors at location (x, y) on the board.
        wnbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a wnbns object of given colors at location (x, y) on the board.
        wbbns(board: np.ndarray, colors: list, x: int, y: int)
            Places a wbbns object of given colors at location (x, y) on the board.
        nwbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a nwbws object of given colors at location (x, y) on the board.
        nnbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a nnbws object of given colors at location (x, y) on the board.
        nbbws(board: np.ndarray, colors: list, x: int, y: int)
            Places a nbbws object of given colors at location (x, y) on the board.

        

    You receive an instruction such as:
        "Place a wn with colors green and blue in cell (1, 8)."

    You must convert these coordinates to Python 0-based indexing:
        - Human cell (1, 1) → x = 0, y = 0
        - Human cell (3, 5) → x = 2, y = 4
        - Human cell (1, 8) → x = 0, y = 7  

    ---
    AVAILABLE SHAPES
      - washer
      - nut
      - screw
      - bridge (vertical, horizontal)  ← special shape
         • Use **'bridge-h'** for horizontal bridges and **'bridge-v'** for vertical ones.      

    AVAILABLE COLORS
      - green
      - red
      - blue
      - yellow

    ---
    IMPLEMENTATION DETAILS
      • **Do not assume** any unspecified details (e.g., color, orientation, or position).
        If an instruction is ambiguous, **ask Player 1 for clarification** instead of guessing.
      • Examine 'skill_required' and 'available_skills' first.
          - If the required skill name does not appear in available_skills,
            return {"status": "clarification", "details": "unknown skill <name>"}.
          - Otherwise, respond to Player 1's instruction.
            return {"status": "clarification", "details": "yes, I know how to use <skill name>"}.
      • If Player instructs to use the skill check if the colors, locations everything are available to you before proceeding
          - If everything is clear, generate an executable Python code using the available skills.
      • If the execution of the available skill is leading to mismatches in the board, do not attempt to correct the skill. Instead, ask for clarification.
      • Always respond in the specified JSON format.          
      • Only use the provided skills to modify the board state.
    ---                  

    Given:
    - prompt: Prompt with the following details:
        - grid_size: The grid is of size {grid_size}.
        - The instruction text from Player 1 describing what to do
        - current_grid: The current filled cells of the grid, None if empty

    Produce:
    - Respond with a JSON object:
      Format:
      {
        "status": "<string>",       # e.g. "clarification" or "code"
        "details": "<string>",     # Python code when status="code", or plain text when status="clarification"
      }

      If clarification needed:
      {
        "status": "clarification",
        "details": "Which color washer should I use?"
      }

      If executing code:
      {
           "status": "code",
           "details": "wn(board, ['green'], x=0, y=1)"
     }      

    Make sure the JSON is valid and parsable by Python json.loads().
    """


    #Currently available skills are hardcoded - update it with actual list
    prompt: str = dspy.InputField(desc="Prompt with Instruction from User and current grid state")
    #history: Optional[dspy.History] = dspy.InputField()    
    player_response: str = dspy.OutputField(
        desc="A JSON object with keys 'status' and 'details' as described above"
    )