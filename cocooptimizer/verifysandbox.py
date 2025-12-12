import os
import json
import numpy as np

from utils.coco import init_board, put, plot_board
from llm_sandbox import SandboxSession, SandboxBackend

def savecontainer():
    # Save container state after execution
    with SandboxSession(
        backend=SandboxBackend.DOCKER,
        lang="python",
        commit_container=True,
        image="sandbox_llm",
        verbose=True,
        skip_environment_setup=True
    ) as session:
        # Install packages and setup environment
        session.run("print('Environment configured')")    

def checksandbox():
    error_fnc = None
    code_exec = f"""
import numpy as np
import json
from coco import put, init_board, plot_board
board=init_board(8,8)
error = {error_fnc}
try:
    put(board, 'bridge-h','red', 8,8)
    print("Placed shape successfully.")
except Exception as e:
    error = str(e)   
    print("Error placing shape:", error)
np.save("board.npy", board)
with open("result.json", "w") as f:
    data = {{"error": error}}
    json.dump(data, f)
"""
    with SandboxSession(image="sandbox_llm", keep_template=True, lang="python", verbose=True, skip_environment_setup=True) as session:
        sandbox_result = session.run(code_exec)
        #print(sandbox_result)
        print(sandbox_result.stdout)

        # Copy files out
        session.copy_from_runtime("/sandbox/board.npy", "board.npy")    
        session.copy_from_runtime("/sandbox/result.json", "result.json")        



def checkfunc2():
    current_board = init_board(8, 8)
    response = "put(board, 'bridge-h','red', 7,7)"
    code_exec = f"""
import numpy as np
import json
import copy
from coco import(
        init_board,
        plot_board,
        put,
        move,
        remove,
        clear,
        SameShapeStackingError,
        SameShapeAtAlternateLevels,
        NotOnTopOfScrewError,
        DepthMismatchError,
)


error = None
board=np.array({current_board.tolist()})
try:
    {response}
except Exception as e:
    error = str(e)    
np.save("board.npy", board)
with open("result.json", "w") as f:
    data = {{"error": error}}
    json.dump(data, f)
"""    
    
    with SandboxSession(image="sandbox_llm", keep_template=True, lang="python", verbose=True, skip_environment_setup=True) as session:
        sandbox_result = session.run(code_exec)
        #print(sandbox_result)
        print(sandbox_result)

        # Copy files out
        session.copy_from_runtime("/sandbox/board.npy", "board.npy")    
        session.copy_from_runtime("/sandbox/result.json", "result.json")        


#checksandbox()
#checkfunc2()
"""
board = np.load("board.npy")    
plot_board(board, "sbout.png")

with open("result.json", "r") as f:
    result_data = json.load(f)
    print("Error:", result_data.get("error"))

"""
savecontainer()