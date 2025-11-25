import matplotlib.pyplot as plt
import numpy as np


def plot_screw(ax, x, y, factor=3, color="b", cell_size=1):
    if color == 'y':
        color = 'orange'


    circle = plt.Circle(
        (x + cell_size / 2, y + cell_size / 2),
        cell_size / factor,
        edgecolor="k",
        facecolor=color,
    )
    ax.add_patch(circle)
    return


def plot_washer(ax, x, y, color="r", cell_size=1):
    if color == 'y':
        color = 'orange'

    diamond = plt.Polygon(
        [
            (x + cell_size / 2, y),
            (x + cell_size, y + cell_size / 2),
            (x + cell_size / 2, y + cell_size),
            (x, y + cell_size / 2),
        ],
        linewidth=1,
        closed=True,
        edgecolor="k",
        facecolor=color,
    )
    ax.add_patch(diamond)
    return


def plot_nut(ax, x, y, factor=1.4, color="g", cell_size=1):
    if color == 'y':
        color = 'orange'

    square = plt.Rectangle(
        (
            x + (cell_size - cell_size / factor) / 2,
            y + (cell_size - cell_size / factor) / 2,
        ),
        cell_size / factor,
        cell_size / factor,
        linewidth=1,
        edgecolor="k",
        facecolor=color,
    )
    ax.add_patch(square)
    return


def plot_bridge_h(ax, x, y, factor=1.6, color="g", cell_size=1):
    if color == 'y':
        color = 'orange'

    bridge = plt.Rectangle(
        (
            x + (cell_size - cell_size / factor) / 2,
            y + (cell_size - cell_size / factor) / 2,
        ),
        (cell_size / factor + (cell_size - cell_size / factor) / 2) * 2,
        cell_size / factor,
        linewidth=1,
        edgecolor="k",
        facecolor=color,
    )
    ax.add_patch(bridge)
    return


def plot_bridge_v(ax, x, y, factor=1.6, color="g", cell_size=1):
    if color == 'y':
        color = 'orange'


    bridge = plt.Rectangle(
        (
            x + (cell_size - cell_size / factor) / 2,
            y + (cell_size - cell_size / factor) / 2,
        ),
        cell_size / factor,
        (cell_size / factor + (cell_size - cell_size / factor) / 2) * 2,
        linewidth=1,
        edgecolor="k",
        facecolor=color,
    )
    ax.add_patch(bridge)
    return


def set_up_board_plot(rows, cols, cell_size):
    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(2.5, 2.5), dpi=1000)

    # Loop through rows and columns to create the grid
    for row in range(rows):
        for col in range(cols):
            # Define the coordinates and size of each rectangle
            x = col
            y = row
            width = 1
            height = 1

            # Create a rectangle for each cell in the grid
            rect = plt.Rectangle(
                (x, y), width, height, linewidth=1, edgecolor="k", facecolor="w"
            )
            ax.add_patch(rect)

    # Set axis limits to match the grid size
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)

    # ---- Put ticks at cell centers and use them as labels ----
    ax.set_xticks(np.arange(cols) + 0.5)
    ax.set_yticks(np.arange(rows) + 0.5)

    ax.set_xticklabels(range(1, cols + 1))
    ax.set_yticklabels(range(1, rows + 1))

    #ax.tick_params(axis="both", length=0, pad=5)
    ax.tick_params(axis="both", length=0, pad=5, labelsize=5)  # <-- small font

    # Column numbers on top
    ax.xaxis.tick_top()

    # Axis titles
    ax.set_xlabel("Columns →", labelpad=2, fontsize=6)
    ax.xaxis.set_label_position('top')

    ax.set_ylabel("Rows →", labelpad=2, fontsize=6)    
    ax.yaxis.set_label_position('left')

    ax.set_aspect("equal", adjustable="box")

    # invert y, to move 0,0 to top left
    plt.gca().invert_yaxis()

    return fig, ax


def plot_board(board, filename=None):
    max_height, depth, rows, cols = board.shape

    fig, ax = set_up_board_plot(rows, cols, cell_size=1)

    for this_layer in board:
        obj = this_layer[0].T
        clr = this_layer[1].T

        for r in range(obj.shape[1]):
            for c in range(obj.shape[0]):
                if obj[r, c] == "S":
                    plot_screw(ax, r, c, color=clr[r, c])
                if obj[r, c] == "W":
                    plot_washer(ax, r, c, color=clr[r, c])
                if obj[r, c] == "N":
                    plot_nut(ax, r, c, color=clr[r, c])
                if obj[r, c] == "L":
                    plot_bridge_h(ax, r, c, color=clr[r, c])
                if obj[r, c] == "T":
                    plot_bridge_v(ax, r, c, color=clr[r, c])
    if filename:
        #plt.savefig(filename, dpi=300)
        plt.savefig(filename, dpi=1000)
    plt.close()


long_to_short = {"washer": "W", "nut": "N", "screw": "S"}
short_to_long = {"W": "washer", "N": "nut", "S": "screw", "L": "bridge-h", "R": "bridge-h", "T": "bridge-v", "B": "bridge-v"}
long_to_short_color = {"red": "r", "blue": "b", "green": "g", "yellow": "y"}


# custom exceptions
class SameShapeStackingError(Exception):
    "Raised when same shapes are stacked on top of each other"
    pass


class SameShapeAtAlternateLevels(Exception):
    "Raised when same shapes are stacked at alternate levels"
    pass


class NotOnTopOfScrewError(Exception):
    "Raised when a shape is placed on top of a screw"
    pass


class DepthMismatchError(Exception):
    "Raised when the depth of the new shape does not match the depth of existing shapes"
    pass


class BridgePlacementError(Exception):
    "Raised when a bridge is placed at levels greater than 2"
    pass


class DimensionsMismatchError(Exception):
    "Raised when the dimensions of the board do not match the dimensions of input x,y"
    pass


def get_top_layer(board, x, y):
    this_stack = board[:, 0, x, y]
    top_layer = np.where(this_stack == "0")[0]
    if top_layer.size > 0:
        top_layer = top_layer[0]
    else:
        raise (ValueError(f"Placement not possible, Current stack is full{top_layer.size}"))
    return top_layer

def get_total_occupied_layers(board, x, y):
    this_stack = board[:, 0, x, y]
    occupied_layers = np.where(this_stack != "0")[0]
    return occupied_layers.size


# TODO: operate on copy of board, so that original board
# can be returned if placement not possible? (rather than
# raising an exception)
def put(board, shape, color, x, y):
    if x >= board.shape[2] or y >= board.shape[3]:
        raise (DimensionsMismatchError("Row, Column values exceed board dimensions. Placement not possible"))

    top_layer = get_top_layer(board, x, y)

    if shape == "bridge-h":
        if y + 1 >= board.shape[3]:
            raise (ValueError("Grid boundary exceeded while placing bridge-h. Placement not possible"))

        if top_layer >= 2:
            raise (BridgePlacementError("Cannot place bridge at levels greater than 2. Placement not possible"))

        top_layer_adjacent = get_top_layer(board, x, y + 1)
        if top_layer != top_layer_adjacent:
            raise (DepthMismatchError("Depth is mismatched while placing bridge-h. Placement not possible"))

        board[top_layer, 0, x, y] = "L"
        board[top_layer, 1, x, y] = color


        board[top_layer, 0, x, y + 1] = "R"
        board[top_layer, 1, x, y + 1] = color
    elif shape == "bridge-v":
        if x + 1 >= board.shape[2]:
            raise (ValueError("Grid boundary exceeded while placing bridge-v. Placement not possible"))

        if top_layer >= 2:
            raise (BridgePlacementError("Cannot place bridge at levels greater than 2. Placement not possible"))
        
        top_layer_adjacent = get_top_layer(board, x + 1, y)
        if top_layer != top_layer_adjacent:
            raise (DepthMismatchError("Depth is mismatched while placing bridge-v. Placement not possible"))        
        board[top_layer, 0, x, y] = "T"
        board[top_layer, 1, x, y] = color

        board[top_layer, 0, x + 1, y] = "B"
        board[top_layer, 1, x + 1, y] = color
    else:
        # check if it is being placed on top of another screw
        if top_layer > 0:
            if board[top_layer - 1, 0, x, y] == "S":
                raise (NotOnTopOfScrewError("Cannot place shape on top of a screw. Placement not possible"))
            if board[top_layer - 1, 0, x, y] == long_to_short[shape]:
                raise (SameShapeStackingError("Cannot stack the same shapes on top of each other. Placement not possible"))

        if top_layer > 1:
            # check if same shape is placed at alternate levels
            if board[top_layer - 2, 0, x, y] == long_to_short[shape]:
                raise (SameShapeAtAlternateLevels("Cannot place the same shape at alternate levels. Placement not possible"))

        board[top_layer, 0, x, y] = long_to_short[shape]
        board[top_layer, 1, x, y] = color
    # check whether resulting board is legal
    return


def init_board(rows=6, cols=6, max_height=4, depth=2):
    # the board is represented via stacked matrices:
    # there are max_height layers (by default 4), representing the stacking
    # each layer has depth channels (by default 2), one of which will
    # hold the shape information, the other the colour information
    # each layer is a 2d matrix with dimensions as given by rows and cols
    return np.full((max_height, depth, rows, cols), "0", dtype=str)


def place_on_board(board, obj_board, x, y):
    board[
        :, :, slice(x, x + obj_board.shape[2]), slice(y, y + obj_board.shape[3])
    ] = obj_board
    return board


def board_rot90(board):
    board_r = np.rot90(board, axes=(2, 3))
    bridge_rot_dict = {
        "R": "T",
        "L": "B",
        "T": "L",
        "B": "R",
        "W": "W",
        "N": "N",
        "S": "S",
        "0": "0",
    }
    board_r[:, 0] = np.vectorize(bridge_rot_dict.get)(board_r[:, 0])
    return board_r



def _validate_shapes(board, x, y, shapes_list, start_range, end_range):
    assert all(isinstance(s, tuple) and len(s)==2 for s in shapes_list)
    assert 0 <= start_range < end_range <= board.shape[0]
    assert end_range == get_total_occupied_layers(board, x, y)
    assert end_range - start_range == len(shapes_list)

    for layer_offset, (shape, color) in enumerate(shapes_list):
        layer = start_range + layer_offset
        if layer >= board.shape[0]:
            raise (ValueError("Not enough shapes at source location to move"))

        board_shape = board[layer, 0, x, y]
        board_color = board[layer, 1, x, y]


        if board_shape in ["R", "B"]:
            raise (ValueError("Non-anchor token found at source location"))
        
        if board_shape == "0" or board_shape not in short_to_long:
            raise (ValueError(f"Unknown shape at source location; board_shape: {board_shape}, board_color: {board_color}"))
        
        if color.lower() not in long_to_short_color:
            raise (ValueError(f"Unknown color at source location; board_shape: {board_shape}, board_color: {board_color}"))

        color_formatted = long_to_short_color[color.lower()]

        print(f"Validating shape at layer {layer}, expected: ({shape}, {color_formatted}), found: ({short_to_long[board_shape]}, {board_color})")

        if short_to_long[board_shape] != shape or board_color != color_formatted:
            raise (ValueError("Shape or color at source location does not match the provided shapes list"))

def _clear_cell_shapes(board, x, y, undo_list):
    for shape, color, layer in undo_list:
        board[layer, 0, x, y] = "0"
        board[layer, 1, x, y] = "0"

        if shape == "bridge-h":
            board[layer, 0, x, y + 1] = "0"
            board[layer, 1, x, y + 1] = "0"
        elif shape == "bridge-v":
            board[layer, 0, x + 1, y] = "0"
            board[layer, 1, x + 1, y] = "0"
    return



def move(board, x1, y1, x2, y2, shapes_list=None):

    if x1 < 0 or x1 >= board.shape[2] or y1 < 0 or y1 >= board.shape[3]:
        raise (DimensionsMismatchError("Source location out of bounds"))
    if x2 < 0 or x2 >= board.shape[2] or y2 < 0 or y2 >= board.shape[3]:
        raise (DimensionsMismatchError("Destination location out of bounds"))
    
    if x1 == x2 and y1 == y2:
        raise (ValueError("Source and destination locations are the same"))
    
    if shapes_list is not None and len(shapes_list) == 0:
        raise (ValueError("Shapes list cannot be empty"))

    if shapes_list is not None:
        new_layer_len = len(shapes_list)
        cur_max_top_layer = get_total_occupied_layers(board, x1, y1)
        if cur_max_top_layer < new_layer_len:
            raise (ValueError("Not enough shapes at source location to move"))
        start_range = cur_max_top_layer - new_layer_len
        end_range = cur_max_top_layer
        _validate_shapes(board, x1, y1, shapes_list, start_range, end_range)
    else:
        cur_max_top_layer = get_total_occupied_layers(board, x1, y1)
        new_layer_len = 1
        if cur_max_top_layer < new_layer_len:
            raise (ValueError("Not enough shapes at source location to move"))

        start_range = cur_max_top_layer-1
        end_range = start_range+1

    new_location_top_layer = get_total_occupied_layers(board, x2, y2)
    #print(f"new_layer_len: {new_layer_len}, cur_max_top_layer: {cur_max_top_layer}, new_location_top_layer: {new_location_top_layer}")
    
    if new_location_top_layer+new_layer_len > board.shape[0]:
        raise (ValueError(f"Not enough space at destination location, number of new layer to move {new_layer_len} current top layer at destination {new_location_top_layer} max height {board.shape[0]}"))

    
    move_shapes_list = []

    for layer in range(start_range, end_range):
        shape = short_to_long[board[layer, 0, x1, y1]]
        color = board[layer, 1, x1, y1]
        move_shapes_list.append((shape, color, layer))

    source_list = []
    dest_list = []
    dest_layer = new_location_top_layer

    for shape, color, layer in move_shapes_list:

        try:
            put(board, shape, color, x2, y2)
            # Tracking shape from the source and destination locations for later clearing
            source_list.append((shape, color, layer))
            dest_list.append((shape, color, dest_layer))
            dest_layer += 1

        except Exception as e:
            # If placement fails, clear the objects at the destination location
            _clear_cell_shapes(board, x2, y2, dest_list[::-1])
            raise e
    # If all placements are successful, clear the objects at the source location
    _clear_cell_shapes(board, x1, y1, source_list)
    return board

def clear(board):
    board[:, :, :, :] = "0"
    return board


def remove(board, x, y, shape, color):
    top_layer = get_top_layer(board, x, y)
    if top_layer == 0:
        raise (ValueError("No shapes to remove at the specified location"))

    board_shape = board[top_layer - 1, 0, x, y]
    board_color = board[top_layer - 1, 1, x, y]

    if board_shape in ["R", "B"]:
        raise (ValueError("Non-anchor token found at source location"))

    if board_shape == "0" or board_shape not in short_to_long:
        raise (ValueError(f"Unknown shape at source location; board_shape: {board_shape}, board_color: {board_color}"))

    if color.lower() not in long_to_short_color:
        raise (ValueError(f"Unknown color at source location; board_shape: {board_shape}, board_color: {board_color}"))

    color_formatted = long_to_short_color[color.lower()]

    if short_to_long[board_shape] != shape or board_color != color_formatted:
        raise (ValueError("Shape or color at source location does not match the provided shape and color"))

    if shape == "bridge-h":
        top_layer_next_col = get_top_layer(board, x, y + 1)
        if top_layer != top_layer_next_col:
            raise (ValueError("Bridge shape incomplete at source location"))
        board[top_layer - 1, 0, x, y + 1] = "0"
        board[top_layer - 1, 1, x, y + 1] = "0"
    elif shape == "bridge-v":
        top_layer_next_row = get_top_layer(board, x + 1, y)
        if top_layer != top_layer_next_row:
            raise (ValueError("Bridge shape incomplete at source location"))
        board[top_layer - 1, 0, x + 1, y] = "0"
        board[top_layer - 1, 1, x + 1, y] = "0"

    board[top_layer - 1, 0, x, y] = "0"
    board[top_layer - 1, 1, x, y] = "0"


    return board