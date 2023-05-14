#!/usr/bin/env python

import sys
import time

sys.path.insert(0, "..")

import lucario_fs

def main(**kwargs):
    with open(kwargs['disk'], "r+b") as fd:
        fs = lucario_fs.LucarioFS(fd)

        if not fs.check_header():
            print("Not a LucarioFS disk!")
            return

        file = open(kwargs['file'], "rb")

        fs.write_file(kwargs['file'].split("/")[-1], file.read())

        file.close()
        
        fs.close()

        fd.close()

def premain():
    import argparse

    argparser = argparse.ArgumentParser(prog='mkfs.lucario')
    argparser.add_argument("disk", help="Disk image to format")
    argparser.add_argument("file", help="File to write to disk")

    args = argparser.parse_args()

    starttime = time.time()
    
    main(**args.__dict__)

    endtime = time.time()

    elapsed = endtime - starttime

    print(f"[OK] Wrote {args.file} in {round(elapsed, 2)} seconds.")

if __name__=="__main__":
    premain()
