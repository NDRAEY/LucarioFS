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

        max_entries, entries = fs.get_file_table()

        print("Contents of", kwargs['disk'], "\n")

        for i in entries:
            print(f"- {i.name:32} [{i.real_size} bytes]")

        fs.close()

        fd.close()

def premain():
    import argparse

    argparser = argparse.ArgumentParser(prog='mkfs.lucario')
    argparser.add_argument("disk", help="Disk image to format")

    args = argparser.parse_args()

    main(**args.__dict__)

if __name__=="__main__":
    premain()
