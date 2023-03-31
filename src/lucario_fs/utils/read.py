#!/usr/bin/env python

import sys

sys.path.insert(0, "..")

import lucario_fs

def main(**kwargs):
    with open(kwargs['disk'], "r+b") as fd:
        fs = lucario_fs.LucarioFS(fd)

        if not fs.check_header():
            print("Not a LucarioFS disk!")
            return

        if not fs.file_exists(kwargs['file']):
            print("File not found!!!")
            return

        print(fs.read_file(kwargs['file']).decode("utf-8"), end='')

        fs.close()

        fd.close()


def premain():
    import argparse

    argparser = argparse.ArgumentParser(prog='mkfs.lucario')
    argparser.add_argument("disk", help="Disk image to format")
    argparser.add_argument("file", help="File to reaf from disk")

    args = argparser.parse_args()

    main(**args.__dict__)

if __name__=="__main__":
    premain()
