from enum import Enum
from dataclasses import dataclass
import struct

# FS

# - HEADER
# - File table size
# - FILE TABLE


# HEADER

# - LCFS magic

HEADER = struct.Struct(b"<7B")


# FILE TABLE SIZE (in entries)

FT_SIZE = lambda size: size // 8192


# FILE TABLE HEADER

FT_HEADER = struct.Struct(b"<I")


# FILE TABLE ENTRY

# - TYPE
# - NAME (256 symbols)
# - FOLDER_ID
# - SECTOR LIST LBA
# - SECTOR LIST SIZE
# - REAL FILE SIZE

FT_ENTRY = struct.Struct(b"<B256cIIIII")


# SECTOR LIST IS AN ARRAY OF UINT32_T ENTRIES

SECTOR_LIST = struct.Struct(b"<I")


# NOTE: FOLDER_ID is an ID of folder, root folder is 0

# ENTRY TYPE IN "FILE TABLE ENTRY"

class EntryType(Enum):
    NONE = 0
    FOLDER = 0xF0
    FILE = 0xF1

@dataclass
class Entry:
    type: int
    name: str
    folder_target_id: int
    folder_id: int
    sector_list_pos: int
    sector_list_size: int
    real_size: int
