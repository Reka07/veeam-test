import os
import shutil
import threading
from threading import Thread
import itertools
import logging
import argparse
import time


def remove_prefix(text, prefix):
    """
    :param text: Text to search in
    :param prefix: Prefix to remove
    :return: Return the text after removal
    """
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def get_files(root: str):
    """
    :param root: Path to the folder
    :return: Return a list with folders and files in the given path
    """
    paths = []
    for path, dirs, files in os.walk(root):
        for file, directory in itertools.zip_longest(files, dirs):
            rel_dir = os.path.relpath(path, root)
            if file is not None:
                paths.append(os.path.join(rel_dir, file))
            if directory is not None:
                paths.append(os.path.join(rel_dir, directory))
    return paths


def copy(source: str, replica: str):
    """
    :param source: Path to source folder
    :param replica: Path to replica folder
    :return: Nothing to return
    """
    for item in os.listdir(source):
        s_path = os.path.join(source, item)
        r_path = os.path.join(replica, item)
        if os.path.isdir(s_path):
            if not os.path.exists(r_path):
                os.makedirs(r_path)
                logging.info('Made directory: %s', r_path)
            copy(s_path, r_path)
        else:
            if not os.path.exists(r_path) or os.stat(s_path).st_mtime - os.stat(r_path).st_mtime > 1:
                shutil.copy2(s_path, r_path)
                logging.info("Copied file from %s to %s:", s_path, r_path)


def delete(s_data: list, r_data: list, replica: str):
    """
    :param s_data: List of folders and files in source folder
    :param r_data: List of folders and files in replica folder
    :param replica: Path to replica folder
    :return: Nothing to return
    """
    if len(r_data) > len(s_data):
        for file in r_data:
            if file not in s_data:
                file = remove_prefix(file, '.\\')
                path = os.path.join(replica, file)
                if os.path.exists(path) and os.path.isfile(path):
                    os.remove(path)
                    logging.info('Deleted file: %s', path)
                elif os.path.exists(path) and os.path.isdir(path):
                    shutil.rmtree(path)
                    logging.info('Deleted directory and all files and subdirectories in it: %s', path)


def sync(source: str, replica: str):
    """
    :param source: path to the source directory
    :param replica: path to the replica directory
    :return: nothing to return
    """
    print("Synchronization started : {}".format(time.ctime()))
    source_files = get_files(source)
    replica_files = get_files(replica)
    threads = [
        Thread(target=copy, args=(source, replica)),
        Thread(target=delete, args=(source_files, replica_files, replica)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, required=True)
    parser.add_argument('--replica', type=str, required=True)
    parser.add_argument('--interval', type=int, required=True)
    parser.add_argument('--log', type=str, required=True)
    args = parser.parse_args()

    if os.path.exists(args.source) and os.path.exists(args.replica) and args.log != "":
        sourcefile = args.source
        replicafile = args.replica
        logfile = args.log
    else:
        raise FileNotFoundError(
                "{0} or {1} or {2} folder/file does not exist!".format(
                        args.source, args.replica, args.log)
        )

    logging.basicConfig(
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(logfile)
            ],
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
    )
    sync(sourcefile, replicafile)
    seconds = args.interval
    ticker = threading.Event()
    while not ticker.wait(seconds):
        sync(sourcefile, replicafile)


if __name__ == "__main__":
    main()
