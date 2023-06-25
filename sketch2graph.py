from PIL import Image
import numpy as np
import argparse
import os

def load_image(path):
    """
    Loads an image as a 3D numpy array.
    :param path: Path to the image file
    :return: A 3D numpy array
    """
    return np.array(Image.open(path)).astype(float)


def index_mat(y, x):
    """
    Creates a matrix with the same dimensions as the image, where each row contains its index + 1.
    :param y: Height of the image
    :param x: Width of the image
    :return: A 2D numpy array with the same dimensions as the image
    """
    return np.array([np.array([j for _ in range(x)]) for j in range(y)][::-1])


def get_graph(img, graph_color, top):
    """
    Extracts the graph from a 3D numpy array.
    :param img: The image as a 3D numpy array
    :param graph_color: Color of the graph in hex or RGB format (e.g. #ffffff or (255,255,255))
    :param top: Defines whether the top or bottom of the graph is used, if the line is thicker than one pixel
    :return: A 1D numpy array containing the graph, with arbitrary values
    """
    if graph_color[0] != '#' and len(graph_color) == 3:
        graph_color = np.array(graph_color)
    elif graph_color[0] == '#' and len(graph_color) == 7:
        graph_color = np.array([int(graph_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)])
    else:
        raise ValueError("Invalid color format. Please use hex or RGB values.")
    img[img == graph_color] = 1 # graph becomes 1s
    img[img != 1] = np.nan # background becomes nan

    new = np.array([list(map(lambda x: x[0], img[i])) for i in range(img.shape[0])])
    
    img = new * index_mat(*new.shape)
    img = img.T

    sig = []
    for col in img:
        col = [i for i in col if str(i) != 'nan'] # please ignore this dirty code
        if len(col) == 0:
            sig.append(np.nan)
        else:
            if not top:
                sig.append(min(col))
            else:
                sig.append(max(col))
    
    return sig


def change_values(sig, y_min, y_max):
    """
    Changes the values of the graph to fit the given y-range.
    :param sig: The graph
    :param y_min: Value of the lowest point of the y-axis
    :param y_max: Value of the highest point of the y-axis
    :return: The graph with the new values
    """
    clean = [i for i in sig if str(i) != 'nan']
    ma, mi = max(clean), min(clean)
    for i, val in enumerate(sig):
        if str(val) != 'nan':
            sig[i] = ((val - mi) / (ma - mi)) * (y_max - y_min) + y_min
    
    return sig


def s2g(path, graph_color="#000000", y_min=0, y_max=1, top=True):
    """
    Converts a sketch of a graph into a graph.
    :param path: Path to the image file
    :param graph_color: Color of the graph in hex or RGB format (e.g. #ffffff or (255,255,255)). Defaults to #000000
    :param y_min: Value of the lowest point of the y-axis. Defaults to 0
    :param y_max: Value of the highest point of the y-axis. Defaults to 1
    :param top: Defines whether the top or bottom of the graph is used, if the line is thicker than one pixel. Defaults to top.
    :return: A numpy array containing the graph
    """
    img = load_image(path)
    sig = get_graph(img, graph_color, top)
    if len(set([i for i in sig if str(i) != 'nan'])) > 1: # if there is only one value, there will be a division by zero error in the next step
        sig = change_values(sig, y_min, y_max)
    return sig


def main():
    """
    Main function called when the script in command line mode is executed.
    """
    parser = argparse.ArgumentParser(description='Sketch2Graph: A simple tool to convert a sketch of a graph into a graph.')
    parser.add_argument('-p', '--path', type=str, help='Path to the image file')
    parser.add_argument('-c', '--color', type=str, help='Color of the graph in hex or RGB format (e.g. #ffffff or 255,255,255). Defaults to #000000')
    parser.add_argument('-y', '--yrange', type=str, help='Range of the y-axis in the format min,max (e.g. -2.75,12.6). Defaults to 0,1')
    parser.add_argument('-o', '--output', type=str, help='Path to the output numpy file. Defaults to the same path as the input file.')
    parser.add_argument('--top', action='store_true', help='Defines whether the top or bottom of the graph is used, if the line is thicker than one pixel. Defaults to top.')
    
    args = parser.parse_args()

    if args.path is None:
        parser.print_help()
        print("\nERROR: Please specify a path to the image file.")
        return
    if args.color is None:
        args.color = "#000000"
    if args.yrange is None:
        args.yrange = "0,1"
    if args.output is None:
        args.output = ".".join(os.path.basename(args.path).split(".")[:-1])
        
    args.output += ".npy" if not args.output.endswith(".npy") else ""
    dir = os.path.dirname(args.output)
    if not os.path.exists(dir) and dir != "":
        os.makedirs(dir)

    try:
        y_min, y_max = args.yrange.split(",")
        y_min, y_max = float(y_min), float(y_max)
    except:
        parser.print_help()
        print("\nERROR: Invalid y-range format. Please use min,max (e.g. -2.75,12.6).")
        return

    try:
        if args.color[0] != '#':
            args.color = np.array(args.color.split(",")).astype(int)
    except:
        parser.print_help()
        print("\nERROR: Invalid color format. Please use hex or RGB. In case of RGB, please use R,G,B (e.g. 255,0,211).")
        return
    
    sig = s2g(args.path, graph_color=args.color, y_min=y_min, y_max=y_max, top=args.top)
    np.save(args.output, sig)
    print("Saved graph as numpy array to", os.path.abspath(args.output))


if __name__ == "__main__":
    main()