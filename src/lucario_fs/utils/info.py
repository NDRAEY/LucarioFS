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

        data_size, seclist_size = fs.get_used_space_bytes_additional()

        print("Disk name: ", kwargs['disk'])
        print("LucarioFS version: {}.{}.{}".format(
            *fs.version
        ))
        print("Disk size: ", fs.get_disk_size(), "bytes")
        print("Used space:", fs.get_used_space_bytes(), "bytes")
        print("  |- Sector lists:", seclist_size, "bytes")
        print("  |- File data:", data_size, "bytes")
        print("Free space:", fs.get_free_space_bytes(), "bytes")

        print("File count:", fs.get_file_count())

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
