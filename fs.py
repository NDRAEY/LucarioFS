import structures
# import struct

ALIGN = lambda value, align: value + (-value & (align - 1))

class LucarioFS:
    def __init__(self, fd):
        self.file = fd

        self.header = "LUCARIO"
        self.header_bytes = tuple([ord(i) for i in self.header])

        self.file_table = []

        self.max_entries = structures.FT_SIZE(self.get_disk_size())

        self.data_start = ALIGN(512 + 4 + (self.max_entries * structures.FT_ENTRY.size), 512)

        self.get_file_table()

    def check_header(self):
        self.file.seek(0)
        
        header = structures.HEADER.unpack_from(self.file.read(4))
        return self.header_bytes == header

    def get_file_table(self):
        self.file.seek(512 + 4)

        entry_count = self.max_entries

        entries = []

        for i in range(entry_count):
            typ, *name, p1, p2, sector_list_size, rsize = structures.FT_ENTRY.unpack_from(
                self.file.read(
                    structures.FT_ENTRY.size
                )
            )

            if typ == structures.EntryType.NONE.value:
                continue

            name = b''.join(name).decode("utf-8")
            name = name[:name.index("\x00")]

            entries.append(structures.Entry(
                typ, name, p1, p2, sector_list_size, rsize
            ))

        self.file_table = entries

        return (entry_count, entries)

    def get_disk_size(self):
        _ = self.file.tell()
        __ = self.file.seek(0, 2)
        
        self.file.seek(_)

        return __

    def find_file_entry_raw(self, name, folder_id=0):
        for n, i in enumerate(self.file_table):
            if i.name == name and i.folder_id == folder_id:
                return n

    def find_free_entry_idx(self):
        self.file.seek(512 + 4)  # After header and size

        for i in range(self.max_entries):
            typ, *entry_data = self.file.read(structures.FT_ENTRY.size)

            if typ == structures.EntryType.NONE.value:
                return i

        return 0

    def entry_idx_to_seek(self, idx):
        return 512 + 4 + (idx * structures.FT_ENTRY.size)

    def to_name(self, name):
        return [i.to_bytes(1, 'little') for i in name.encode("utf-8") + b''.join([b'\x00'] * (256 - len(name)))]

    def write_entry(self, idx, typ, name, folder_id, sector_list_lba, sector_list_size, real_size):
        self.file.seek(self.entry_idx_to_seek(idx))

        tmp = structures.FT_ENTRY.pack(
            typ, *self.to_name(name), folder_id, sector_list_lba, sector_list_size, real_size
        )

        self.file.write(tmp)

    def add_entry(self, typ, name, folder_id, sector_list_lba, sector_list_size, real_size):
        en = self.find_free_entry_idx()

        self.write_entry(en, typ, name, folder_id, sector_list_lba, sector_list_size, real_size)

    def erase_entry(self, idx):
        pos = self.entry_idx_to_seek(idx)

        self.file.seek(pos)
        self.file.write(b'\0' * structures.FT_ENTRY.size)

    def get_sectors_from_file_entry(self, fentry):
        self.file.seek(fentry.sector_list_pos * 512)

        sectors = []

        for i in range(fentry.sector_list_size):
            sectors.append(structures.SECTOR_LIST.unpack(
                self.file.read(structures.SECTOR_LIST.size)
            )[0])

        return sectors

    def get_free_sector(self):
        start_sec = self.data_start // 512
        used_sectors = []

        for i in self.get_file_table()[1]:
            # print("=>", i)
            used_sectors.append(i.sector_list_pos)
            used_sectors.extend(self.get_sectors_from_file_entry(i))

        # print("Data starts at:", start_sec)

        # print("Used sectors:", used_sectors)

        sec = start_sec

        while True:
            if sec not in used_sectors:
                break
            sec += 1

        return sec

    def create_file(self, name, folder_id = 0):
        self.add_entry(structures.EntryType.FILE, name, folder_id, 0, 0, 0)

    def file_exists(self, name, folder_id = 0):
        return self.find_file_entry_raw(name, folder_id) is not None

    def write_file(self, name, data, folder_id = 0):
        sector_list_pos = self.get_free_sector()

        datasize = ALIGN(len(data), 512)

        sectors = []

        if (datasize // 512) > 512:
            print("File too big!!!", "Max is", (512 // 4) * 512)
            return

        # print("Free sectors: ", sectors)

        fileidx = self.find_file_entry_raw(name, folder_id)

        if fileidx is not None:
            self.erase_entry(fileidx)
            
        self.add_entry(structures.EntryType.FILE.value, name, folder_id, sector_list_pos, datasize // 512, len(data))

        for i in range(datasize // 512):
            sectors.append(self.get_free_sector())

            self.file.seek((sector_list_pos * 512) + i * structures.SECTOR_LIST.size)

            self.file.write(
                structures.SECTOR_LIST.pack(
                    sectors[i]
                )
            )

        """
        self.file.seek(sector_list_pos * 512)

        for i in sectors:
            self.file.write(
                structures.SECTOR_LIST.pack(
                    i
                )
            )
        """

        for n, i in enumerate(sectors):
            self.file.seek(i * 512)
            self.file.write(data[n * 512 : (n + 1) * 512])

    def read_sectors(self, sectors):
        data = []

        for i in sectors:
            self.file.seek(i * 512)
            data.append(self.file.read(512))

        return data

    def read_file(self, name, folder_id=0):
        file_idx = self.find_file_entry_raw(name, folder_id)

        entry = self.get_file_table()[1][file_idx]

        sector_list = self.get_sectors_from_file_entry(entry)

        datas = b''.join(self.read_sectors(sector_list))

        return datas[:entry.real_size]
    
    def format(self):
        self.file.seek(0)
        self.file.write(b'\x00' * (
            512 + 4 + (structures.FT_ENTRY.size * self.max_entries)
        ))

        self.file.seek(0)
        self.file.write(self.header.encode("utf-8"))

    def flush(self):
        self.file.flush()

    def close(self):
        self.file.flush()
        self.file.close()

if __name__ == "__main__":
    fs = LucarioFS(open("disk.img", "r+b"))
    # fs.format()
    # fs.check_header()

    for i in fs.get_file_table()[1]:
        print(i.name + ": ")
        print("\tSector list at:", i.sector_list_pos)
        
        for n in fs.get_sectors_from_file_entry(i):
            print("\t=>", n)
        
        print("\tContents: ", end='')
        
        data = fs.read_file(i.name)
        print(data)

        print()

    fs.close()
