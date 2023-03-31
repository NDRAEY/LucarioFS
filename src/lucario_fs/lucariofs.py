# LucarioFS by NDRAEY.

# Lucario (as character) belongs to Creatures Inc. (The Pokémon Company)

try:
    import structures
    from version import __version__
except:
    from . import structures
    from .version import __version__

# import struct

# Align function
ALIGN = lambda value, align: value + (-value & (align - 1))

class LucarioFS:
    def __init__(self, fd):
        self.file = fd

        # Original and converted magics
        self.header = "LUCARIO"
        self.header_bytes = tuple([ord(i) for i in self.header])

        self.file_table = []

        # Number of files and directories for disk.
        self.max_entries = structures.FT_SIZE(self.get_disk_size())

        # Start of data section
        self.data_start = ALIGN(512 + (self.max_entries * structures.FT_ENTRY.size), 512)

        # Read file table.
        self.get_file_table()

    def check_header(self):
        # Go to start of the disk
        self.file.seek(0)

        # Read bytes and unpack them
        header = structures.HEADER.unpack_from(
            self.file.read(
                structures.HEADER.size
            )
        )

        # Is they match?
        return self.header_bytes == header

    def get_file_table(self):
        # Skip 512 bytes (boot sector) and 4 bytes of maxiaml length of table
        self.file.seek(512)

        # Entry buffer
        entries = []

        # Iterate over ALL entries
        # for i in range(entry_count):
        for i in range(self.max_entries):
            # Eztract data (make sure name is limited by 256 charaacters.)
            typ, *name, folder_id, sector_list_pos, sector_list_size, rsize = structures.FT_ENTRY.unpack_from(
                self.file.read(
                    structures.FT_ENTRY.size
                )
            )

            # Is it empty entry?
            if typ == structures.EntryType.NONE.value:
                # Scan next entry
                continue

            # Convert name to human-readable format
            name = b''.join(name).decode("utf-8")
            name = name[:name.index("\x00")]

            # Add entry to.list of entries
            entries.append(structures.Entry(
                typ, name, folder_id, sector_list_pos, sector_list_size, rsize
            ))

        # Make it.global
        self.file_table = entries

        # Return max length of table and entries itself.
        return (self.max_entries, entries)

    def get_disk_size(self):
        # Save position, Go to end, Memorize end position, Go back
        
        _ = self.file.tell()
        __ = self.file.seek(0, 2)
        
        self.file.seek(_)

        return __

    def find_file_entry_raw(self, name, folder_id=0):
        # Find matching entry by name and folder_id
        for n, i in enumerate(self.file_table):
            if i.name == name and i.folder_id == folder_id:
                return n

    def find_free_entry_idx(self):
        # Search for free entry in the file entry table
        self.file.seek(512)  # After header and size

        for i in range(self.max_entries):
            typ, *entry_data = self.file.read(structures.FT_ENTRY.size)

            # Is free entry?
            if typ == structures.EntryType.NONE.value:
                return i

    def entry_idx_to_seek(self, idx):
        # Find position on disk, where file entry index is located
        return 512 + (idx * structures.FT_ENTRY.size)

    def to_name(self, name):
        # Convert string to struct-readable array
        return [i.to_bytes(1, 'little') for i in name.encode("utf-8") + b''.join([b'\x00'] * (256 - len(name)))]

    def write_entry(self, idx, typ, name, folder_id, sector_list_lba, sector_list_size, real_size):
        # Write data to file entry.

        # Go to needed index.
        self.file.seek(self.entry_idx_to_seek(idx))

        # Build data
        tmp = structures.FT_ENTRY.pack(
            typ, *self.to_name(name), folder_id, sector_list_lba, sector_list_size, real_size
        )

        # Write data
        self.file.write(tmp)

    def add_entry(self, typ, name, folder_id, sector_list_lba, sector_list_size, real_size):
        # Find free entry and occupy it.
        en = self.find_free_entry_idx()

        self.write_entry(en, typ, name, folder_id, sector_list_lba, sector_list_size, real_size)

    def erase_entry(self, idx):
        # Erase entry, (to delete a file)
        pos = self.entry_idx_to_seek(idx)

        # Go to needed position
        self.file.seek(pos)

        # Zero It!
        self.file.write(b'\0' * structures.FT_ENTRY.size)

    def get_sectors_from_file_entry(self, fentry):
        # Read sector list where file is located

        # Go to needed sector
        self.file.seek(fentry.sector_list_pos * 512)

        sectors = []

        # Scan sectors
        for i in range(fentry.sector_list_size):
            sectors.append(structures.SECTOR_LIST.unpack(
                self.file.read(structures.SECTOR_LIST.size)
            )[0])

        return sectors

    def get_free_sector(self):
        # Get free sector in DATA area.

        # Convert positon to sector at data start.
        start_sec = self.data_start // 512

        # Buffer for used sectors (needed for filtering)
        used_sectors = []

        # Read entries
        for i in self.get_file_table()[1]:
            # Preserve special sector_list sector.
            used_sectors.append(i.sector_list_pos)

            # Preserve additional sectors for big files.
            for j in range(i.sector_list_size // 512):
                for w in range(1, 8):
                    used_sectors.append(i.sector_list_pos + j + w)

            # And sector where data is stored.
            used_sectors.extend(self.get_sectors_from_file_entry(i))

        # Start filtering
        sec = start_sec

        while True:
            # If sector not used, break the loop.
            if sec not in used_sectors:
                break
            sec += 1

        # print("Found free sector:", sec)
        # print("Used sectors:", used_sectors)

        return sec

    def create_file(self, name, folder_id = 0):
        # Just create a file with no sectors, size and data
        self.add_entry(structures.EntryType.FILE, name, folder_id, 0, 0, 0)

    def file_exists(self, name, folder_id = 0):
        # Check for file existance
        return self.find_file_entry_raw(name, folder_id) is not None

    def write_file(self, name, data, folder_id = 0):
        # Hardest thing is write to file.

        # Align data size to fit it to 1 sector if needed.
        datasize = ALIGN(len(data), 512)

        # Get free sector to store sectors that file have.
        sector_list_pos = self.get_free_sector()

        # Create a sector list to be written, based on the data length
        """
        sector_lists = list(range(
            sector_list_pos,
            sector_list_pos + ((datasize // (512 * 512)) + 1) * 4
        )) or [sector_list_pos]
        """

        # print("Need", datasize // (512*512), "sectors")
        # print("Sectors:", sector_lists)

        # Sector list.
        sectors = []

        # Get index of entry by name and folder id
        fileidx = self.find_file_entry_raw(name, folder_id)

        # If file exists, erase it.
        if fileidx is not None:
            self.erase_entry(fileidx)

        # Then add new file description.
        self.add_entry(structures.EntryType.FILE.value, name, folder_id, sector_list_pos, datasize // 512, len(data))

        # And write sector data
        # print("Write", datasize // 512, "sectors")
        for i in range(datasize // 512):
            # Get free sector and append it
            sectors.append(self.get_free_sector())

            # Seek to needed position in-place to get next free sector.
            self.file.seek((sector_list_pos * 512) + i * structures.SECTOR_LIST.size)

            # Write sector info
            self.file.write(
                structures.SECTOR_LIST.pack(
                    sectors[i]
                )
            )

        # print(sectors)

        # Split data by sectors and store.
        for n, i in enumerate(sectors):
            self.file.seek(i * 512)
            self.file.write(data[n * 512 : (n + 1) * 512])

    def read_sectors(self, sectors):
        # Read 512 bytes of every sector we got.
        data = []

        for i in sectors:
            self.file.seek(i * 512)
            data.append(self.file.read(512))

        return data

    def read_file(self, name, folder_id=0):
        # Read file.

        # Get entry index
        file_idx = self.find_file_entry_raw(name, folder_id)

        # Get entry
        entry = self.get_file_table()[1][file_idx]

        # Get it's sector list
        sector_list = self.get_sectors_from_file_entry(entry)

        # Read sectors, join them and select needed range of data.
        datas = b''.join(self.read_sectors(sector_list))

        return datas[:entry.real_size]
    
    def format(self, full = False, version = __version__):
        # Erase file descriptions (not data)
        
        self.file.seek(0)
        self.file.write(b'\x00' * (
            512 + (structures.FT_ENTRY.size * self.max_entries)
        ))

        if full:
            self.file.seek(0)
            self.file.write(b'\x00' * self.get_disk_size())

        # Write magic
        self.file.seek(0)
        self.file.write(self.header.encode("utf-8"))

        # Write version
        for i in version:
            self.file.write(i.to_bytes(1, 'little'))

    # Special functions
    
    def flush(self):
        self.file.flush()

    def close(self):
        self.file.flush()
        self.file.close()

def test():
    from pprint import pprint
    
    fs = LucarioFS(open("disk.img", "r+b"))
    fs.format()
    # fs.check_header()

    fs.write_file("Lucario.txt", b'\nLucario (Japanese: rukario) is a dual-type Fighting/Steel Pokemon introduced in Generation IV.\n\nIt evolves from Riolu when leveled up with high friendship during the day.\n\nLucario can Mega Evolve into Mega Lucario using the Lucarionite.\n')
    fs.write_file("Pikachu.txt", b"Piiiiiikkaaaaaaaa... CHUUUUUUUUUUU!!!")
    fs.write_file("Nikita.txt",  b"Nikita the SayoriOS developer")
    fs.write_file("Andrey.txt",  b"Andrey (Drew) the SayoriOS developer too")

    for i in fs.get_file_table()[1]:
        print(i.name + ": ")
        print("\tSector list at:", i.sector_list_pos)
        
        for n in fs.get_sectors_from_file_entry(i):
            print("\t=>", n)
        
        print("\tContents: ", end='')
        
        data = fs.read_file(i.name)
        print(data.decode("utf-8"))

        print()

    pprint(fs.get_file_table())

    fs.close()

if __name__=="__main__":
    test()
