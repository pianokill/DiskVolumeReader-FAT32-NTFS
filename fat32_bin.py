import utility as ut

class FAT32:     
    def __init__(self, bootsector):
        self.n_sector_per_cluster = ut.read_dec_offset(bootsector, 0x0D, 1)  
        self.n_sector_bootsector = ut.read_dec_offset(bootsector, 0x0E, 2)  
        self.n_fat_table = ut.read_dec_offset(bootsector, 0x10, 1)  
        self.volume_size = ut.read_dec_offset(bootsector, 0x20, 4)  
        self.fat_table_size = ut.read_dec_offset(bootsector, 0x24, 4)  
        self.rdet_begin = ut.read_dec_offset(bootsector, 0x2C, 4)  
        self.sub_sector = ut.read_dec_offset(bootsector, 0x30, 2)  
        self.sector_store_bootsector = ut.read_dec_offset(bootsector, 0x32, 2)  
    def print_bootsector(self):
        print("BOOT SECTOR INFORMATION")
        print("Sectors/cluster: ", self.n_sector_per_cluster)
        print("Sectors/boot sector: ", self.n_sector_bootsector)
        print("FAT Table: ", self.n_fat_table)
        print("Volume Size: ", self.volume_size)
        print("FAT Table Size: ", self.fat_table_size)
        print("RDET Begin: ", self.rdet_begin)
        print("Subsector: ", self.sub_sector)
        print("Sector Store Boot sector: ", self.sector_store_bootsector)

file_fat32 = "/Users/pianokill/Documents/HCMUS-5th/Operating Systems/drive_fat.bin"

bootsector_fat32 = ut.read_sector(file_fat32, 0, 1)
volume_fat32 = FAT32(bootsector_fat32)     
volume_fat32.print_bootsector()
