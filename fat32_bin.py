import utility as ut

class FAT32:     
    
    def __init__(self, bootsector):
        self.n_sector_per_cluster = ut.read_dec_offset(bootsector, 0x0D, 1)  
        self.n_sector_bootsector = ut.read_dec_offset(bootsector, 0x0E, 2)  
        self.n_fat_table = ut.read_dec_offset(bootsector, 0x10, 1)  
        self.volume_size = ut.read_dec_offset(bootsector, 0x20, 4)  
        self.fat_table_size = ut.read_dec_offset(bootsector, 0x24, 4)  
        #self.rdet_begin = ut.read_dec_offset(bootsector, 0x2C, 4)  
        self.sub_sector = ut.read_dec_offset(bootsector, 0x30, 2)  
        self.sector_store_bootsector = ut.read_dec_offset(bootsector, 0x32, 2)  
        self.fat_table = ""
        #FAT 32:
        #SECTORS IN BOOT SECTOR -> RESERVERD -> FAT TABLE -> ROOT DIRECTORY -> DATA AREA    
        self.rdet_sector_begin = self.n_sector_bootsector + self.n_fat_table * self.fat_table_size
        self.data_sector_begin = self.rdet_sector_begin
    def print_bootsector(self):
        print("BOOT SECTOR INFORMATION")
        print("Sectors/cluster: ", self.n_sector_per_cluster)
        print("Sectors/boot sector: ", self.n_sector_bootsector)
        print("FAT Table: ", self.n_fat_table)
        print("Sectors in disk: ", self.volume_size)
        print("Sectors in FAT table ", self.fat_table_size)
        #print("RDET Cluster Begin: ", self.rdet_begin)
        print("RDET Sector Begin: ", self.rdet_sector_begin)
        print("Subsector: ", self.sub_sector)
        print("Sector Store Boot sector: ", self.sector_store_bootsector)
    def read_txt(self, buffer):
        data = ""
        return data
    def read_entry(self, buffer):
        name = 0
        data = self.read_txt(buffer)
        size = 0
        return name, data, size
    def read_rdet(self, buffer):
        entries = []
        for i in range(0, len(buffer), 32):
            entry = self.read_entry(buffer[i:i+32])
            entries.append(entry)
        return entries
    
file_fat32 = "/Users/pianokill/Documents/HCMUS-5th/Operating Systems/drive_fat.bin"
bootsector_fat32 = ut.read_sector(file_fat32, 0, 1)
volume_fat32 = FAT32(bootsector_fat32)     
#volume_fat32.print_bootsector()

RDET = ut.read_sector(file_fat32, volume_fat32.rdet_sector_begin, 1)
print(RDET)

#