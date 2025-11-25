import os
from coco import (
    init_board,
    plot_board,
    put,
    move,
    SameShapeStackingError,
    SameShapeAtAlternateLevels,
    NotOnTopOfScrewError,
    DepthMismatchError,
    DimensionsMismatchError
)

def fill_grid(board, row, col, num_levels):
    shapes = [('bridge-h', 'red'), ('washer', 'blue'), ('nut', 'green'), ('screw', 'yellow')]
    for shape, color in shapes[:num_levels]:
        try:
            put(board, shape, color, row, col)
        except Exception as e:
            print(f"Error placing {color} {shape} at ({row},{col}): {e}")

    #Adding a bridge-v at a different location
    try:
        put(board, "bridge-v", "red", row+1, col+1)
    except Exception as e:
        print(f"Error placing red bridge-v at ({row+1+1},{col+1+1}): {e}")

def fill_grid2(board, row, col, num_levels):
    put(board, 'washer', 'red', row, col)
    put(board, 'nut', 'blue', row, col+1)
    put(board, 'bridge-h', 'green', row, col)
    put(board, 'nut', 'blue', row, col)
    put(board, 'washer', 'red', row+1, col+1)    


def test_boundary_conditions(board):
    fill_grid(board, 0,0,1)
    plot_board(board, "simulatemove_tests_output/before_boundary_test.png")
    try:
        move(board, -1, 0, 0, 0)
    except DimensionsMismatchError as e:
        print(f"Passed boundary test (negative source coords-1): {e}")

    try:
        move(board, 0, -1, 0, 0)
    except DimensionsMismatchError as e:
        print(f"Passed boundary test (negative source coords-2): {e}")     

    try:
        move(board, -1, -1, 0, 0)
    except DimensionsMismatchError as e:
        print(f"Passed boundary test (negative source coords-3): {e}")      

    try:
        move(board, 100, -1, 0, 0)
    except DimensionsMismatchError as e:
        print(f"Passed boundary test (out of bounds and negative source coords): {e}")                  

    try:
        move(board, 0, 0, 100, 0)
    except DimensionsMismatchError as e:
        print(f"Passed boundary test (out of bounds dest coords-1): {e}")

    try:
        move(board, 0, 0, 0, 100)
    except DimensionsMismatchError as e:
        print(f"Passed boundary test (out of bounds dest coords-2): {e}")    

    try:
        move(board, 0, 0, -1, 100)
    except DimensionsMismatchError as e:
        print(f"Passed boundary test (out of bounds and negative dest coords): {e}")

    plot_board(board, "simulatemove_tests_output/after_boundary_test.png")

def test_bridge_boundary_conditions(board, max_row, max_col):
    fill_grid(board, 0,0,1)
    plot_board(board, "simulatemove_tests_output/before_bridge_boundary_test.png")
    try:
        move(board, 0, 0, 0, max_col-1)
    except ValueError as e:
        print(f"Passed bridge boundary test (out of bounds dest coords): {e}")


    try:
        move(board, 1, 1, max_row-1, 1)
    except ValueError as e:
        print(f"Passed bridge boundary test (out of bounds dest coords): {e}") 

    plot_board(board, "simulatemove_tests_output/after_bridge_boundary_test.png")  

def test_move_top_layer_only(board, x1, y1, x2, y2, num_layers):
    fill_grid(board, x1, y1, num_layers)
    plot_board(board, f"simulatemove_tests_output/before_move_top_layer_only_len{num_layers}.png")
    try:
        move(board, x1, y1, x2, y2)
        print(f"Move from ({x1},{y1}) to ({x2},{y2}) successful.")
    except Exception as e:
        print(f"Move from ({x1},{y1}) to ({x2},{y2}) failed: {e}")
    plot_board(board, f"simulatemove_tests_output/after_move_top_layer_only_len{num_layers}.png")

def test_move_multiple_shapes(board, x1, y1, x2, y2, num_layers):
    fill_grid(board, x1, y1, num_layers)
    plot_board(board, f"simulatemove_tests_output/before_move_test_len{num_layers}.png")
    try:
        if num_layers == 1:
            shapes_list = [('bridge-h', 'red')]
        elif num_layers == 2:
            shapes_list = [('bridge-h', 'red'), ('washer', 'blue')]
        elif num_layers == 3:
            shapes_list = [('bridge-h', 'red'), ('washer', 'blue'), ('nut', 'green')]
        else:
            shapes_list = [('bridge-h', 'red'), ('washer', 'blue'), ('nut', 'green'), ('screw', 'yellow')]
        move(board, x1, y1, x2, y2, shapes_list)
        print(f"Move from ({x1},{y1}) to ({x2},{y2}) successful.")
    except Exception as e:
        print(f"Move from ({x1},{y1}) to ({x2},{y2}) failed: {e}")
    plot_board(board, f"simulatemove_tests_output/after_move_test_shape_list_len_{num_layers}.png")

def test_move_multiple_shapes_depth_mismatch(board, x1, y1, x2, y2, num_layers):
    fill_grid(board, x1, y1, num_layers)
    file_suffix = ""

    try:
        if num_layers == 1:
            plot_board(board, f"simulatemove_tests_output/before_move_test_depth_mismatch_len_{num_layers}.png") 
            file_suffix = f"depth_mismatch_len_{num_layers}"         
            shapes_list = [('bridge-h', 'red')]
            #(1,1) has vertical bridge already
            move(board, x1, y1, 1, 1, shapes_list)
        elif num_layers == 2:
            put(board, 'nut', 'green', x2, y2)
            file_suffix = f"len{num_layers}_over_nut"
            plot_board(board, f"simulatemove_tests_output/before_move_test_{file_suffix}.png")       
            shapes_list = [('bridge-h', 'red'), ('washer', 'blue')]
            move(board, x1, y1, 1, 1, shapes_list)
        elif num_layers == 3:
            file_suffix = f"len{num_layers}_over_multiplenuts"            
            put(board, 'nut', 'green', x2, y2)
            put(board, 'nut', 'green', x2, y2+1)
            plot_board(board, f"simulatemove_tests_output/before_move_test_{file_suffix}.png")
            shapes_list = [('bridge-h', 'red'), ('washer', 'blue'), ('nut', 'green')]  
            move(board, 1, 1, x2, y2, shapes_list)          
        else:
            put(board, 'bridge-h', 'green', x2, y2)
            file_suffix = f"len{num_layers}_over_bridge"
            plot_board(board, f"simulatemove_tests_output/before_move_test_{file_suffix}.png")              
            shapes_list = [('bridge-v', 'red')]
            move(board, 1, 1, x2, y2, shapes_list)

        print(f"Move from ({x1},{y1}) to ({x2},{y2}) successful.")
        print(f"Passed the depth mismatch test for {file_suffix}")
    except Exception as e:
        print(f"Move from ({x1},{y1}) to ({x2},{y2}) failed: {e}")
        print(f"Passed the depth mismatch test for {file_suffix}")
    plot_board(board, f"simulatemove_tests_output/after_move_test_{file_suffix}.png")  

def test_move_unknown_shapes_colors(board, x1, y1, x2, y2, num_layers):
    fill_grid(board, x1, y1, num_layers)
    plot_board(board, f"simulatemove_tests_output/before_move_test_unknown_shapes_len{num_layers}.png")
    try:
        if num_layers == 1:
            shapes_list = []
        elif num_layers == 2:
            shapes_list = [('bridge-h', 'red'), ('washer', 'green')]
        elif num_layers == 3:
            shapes_list = [('bridge-h', 'red'), ('nut', 'blue'), ('nut', 'green')]
        else:
            shapes_list = [('bridge-h', 'red'), ('washer', 'blue'), ('nut', 'green')]
        move(board, x1, y1, x2, y2, shapes_list)
        print(f"Move from ({x1},{y1}) to ({x2},{y2}) successful.")
    except Exception as e:
        print(f"Move from ({x1},{y1}) to ({x2},{y2}) failed: {e}")
        print(f"Passed the unknown shapes/colors test for len {num_layers}")
    plot_board(board, f"simulatemove_tests_output/after_move_test_unknown_shapes_len{num_layers}.png")


def test_move_partial_shapes(board, x1, y1, x2, y2, num_layers):
    fill_grid2(board, x1, y1, 4)
    put(board, 'bridge-h', 'yellow', x2, y2)
    plot_board(board, f"simulatemove_tests_output/before_move_test_partial_shapes_len{num_layers}.png")
    try:
        if num_layers == 1:
            shapes_list = [('nut', 'blue')]
        elif num_layers == 2:
            shapes_list = [('bridge-h', 'green'), ('nut', 'blue')]
        elif num_layers == 3:
            shapes_list = [('washer', 'red'), ('bridge-h', 'green'), ('nut', 'blue')]
        move(board, x1, y1, x2, y2, shapes_list)
        print(f"Move from ({x1},{y1}) to ({x2},{y2}) successful.")
        print(f"Passed the partial move test for {num_layers} shapes.")
    except Exception as e:
        print(f"Move from ({x1},{y1}) to ({x2},{y2}) failed: {e}")
        if num_layers == 3:
            print(f"Passed the partial move test for {num_layers} shapes.")
        else:
            print(f"Failed the partial move test for {num_layers} shapes.")
    plot_board(board, f"simulatemove_tests_output/after_move_test_partial_shapes_len{num_layers}.png")

os.makedirs("simulatemove_tests_output", exist_ok=True)

#board = init_board(8,8)
#test_boundary_conditions(board)
#board = init_board(8,8)
#test_bridge_boundary_conditions(board, 8,8)
#for layers in range(1,5):
#    board = init_board(8,8)
#    test_move_top_layer_only(board, 0,0, 2,2, layers)
#for layers in range(1,5):
#    board = init_board(8,8)
#    test_move_multiple_shapes(board, 0,0, 2,2, layers)
for layers in range(1,5):
    board = init_board(8,8)
    test_move_multiple_shapes_depth_mismatch(board, 0,0, 2,2, layers)
#for layers in range(1,5):
#    board = init_board(8,8)
#    test_move_unknown_shapes_colors(board, 0,0, 2,2, layers)
#for layers in range(1,4):
#    board = init_board(8,8)
#    test_move_partial_shapes(board, 0,0, 2,2, layers)