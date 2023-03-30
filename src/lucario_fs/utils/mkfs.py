#!/usr/bin/env python

import sys

sys.path.insert(0, "..")

import lucario_fs

def main(**kwargs):
    with open(kwargs['file'], "r+b") as fd:
        fs = lucario_fs.LucarioFS(fd)

        fs.format()

        fs.close()

        fd.close()

def premain():
    import argparse

    argparser = argparse.ArgumentParser(prog='mkfs.lucario')
    argparser.add_argument("file", help="Disk image to format")

    args = argparser.parse_args()

    main(**args.__dict__)

if __name__=="__main__":
    premain()
