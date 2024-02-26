import os

import os

def draw_directory_tree(root_dir, indent='', is_last=True):
    """
    Draw the directory tree structure starting from the given root directory.
    
    Args:
    - root_dir (str): The root directory to start traversing.
    - indent (str): The indentation string used for drawing the tree.
    - is_last (bool): True if the directory is the last one among its siblings, False otherwise.
    """
    if not os.path.isdir(root_dir):
        print(f"{root_dir} is not a valid directory.")
        return

    print(indent, end='')
    if is_last:
        print("└── ", end='')
        indent += "    "
    else:
        print("├── ", end='')
        indent += "│   "

    print(os.path.basename(root_dir) + "/")

    try:
        items = sorted(os.listdir(root_dir))
        for i, item in enumerate(items):
            item_path = os.path.join(root_dir, item)
            is_last = (i == len(items) - 1)
            if os.path.isdir(item_path):
                draw_directory_tree(item_path, indent, is_last)
            else:
                print(indent, end='')
                if is_last:
                    print("└── ", end='')
                else:
                    print("├── ", end='')
                print(item)
    except PermissionError:
        print(indent + "Permission Denied")



# Example usage:
draw_directory_tree('F:')
