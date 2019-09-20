import os
import sys
import shutil

def main(argv):
    dataset_path = os.path.abspath(argv[1])
    output_path = os.path.abspath(argv[2])

    for root, dirs, files in os.walk(dataset_path):
        for filename in files:
            source = os.path.join(root, filename)
            destination = os.path.join(output_path, filename)
            shutil.move(source, destination)


if __name__ == "__main__":
    main(sys.argv)