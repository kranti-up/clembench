import os
import json


def checknumreconstructpairs(filepath):
    files_list = os.listdir(filepath)
    print(f"Found {len(files_list)} files")


def checknuminstances(filepath):
    with open(filepath, "r") as f:
        data = json.load(f)

    total_files = 0
    combo_counts = {}
    for board_type, objs_type in data.items():
        for boardobj, num_shapes in objs_type.items():
            for total_shapes, combo_names in num_shapes.items():
                combo_counts[total_shapes] = {}
                num_shape_instances = 0
                for combo_name in num_shapes[total_shapes]:
                    num_shape_instances += len(num_shapes[total_shapes][combo_name])
                    if combo_name not in combo_counts[total_shapes]:
                        combo_counts[total_shapes][combo_name] = 0
                    combo_counts[total_shapes][combo_name] += len(num_shapes[total_shapes][combo_name])
                combo_counts[total_shapes]["total"] = num_shape_instances
                print(f"{board_type} {boardobj} Total Shapes: {total_shapes} -> {num_shape_instances}")
                total_files += num_shape_instances
    combo_counts = dict(sorted(combo_counts.items()))
    print(f"Total files: {total_files}, Combo counts: {combo_counts}")

def checknumversionsforcombo(filepath):
    files_list = os.listdir(filepath)
    combo_counts = {}
    for fname in files_list:
        combo_name = fname.split("_")[2].strip()
        total_shapes = len(combo_name)
        if total_shapes not in combo_counts:
            combo_counts[total_shapes] = {}
        if combo_name not in combo_counts[total_shapes]:
            combo_counts[total_shapes][combo_name] = 0
        combo_counts[total_shapes][combo_name] += 1
    
    for total_shapes in combo_counts:
        total = 0
        for combo_name in combo_counts[total_shapes]:
            total += combo_counts[total_shapes][combo_name]
        combo_counts[total_shapes]["total"] = total
    combo_counts = dict(sorted(combo_counts.items()))
    print(f"Combo counts: {combo_counts}")

#checknumreconstructpairs("reconstruct-data-pairs")
#checknuminstances("resources/data/en/sb_so_test.json")
checknumversionsforcombo("reconstruct-data-pairs")