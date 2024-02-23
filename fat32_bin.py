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
        # thông tin entry : tên, phần mở rộng, tập tin or thư mục, kích thước, ? cluster bắt đầu ?
        #tên
        name = ut.read_bin_offset(buffer,0,8).decode('utf-8', errors='ignore').strip()
        
        #trạng thái
        attr = ut.read_dec_offset(buffer,0xB,1)
        

        #attr = ut.describe_attr(attr)
            

        #cluster bắt đầu
        cluster_begin = ut.read_dec_offset(buffer,0x1A,2)

        #size
        size = ut.read_dec_offset(buffer,0x1C,4)
        return name, attr, cluster_begin, size
    def read_rdet(self, buffer):
        entries = []
        sub_entries = []
        buffer_subentry = ()
        sub_name = ''
        for i in range(0, len(buffer), 32):
    
            entry = self.read_entry(buffer[i:i+32])
            entry += buffer_subentry
            # chưa kết thúc tập tin
            if(entry[1] != 15):
       
                buffer_subentry = ()
            # có entry phụ trong tập tin
                if(len(entry) > 4):
                    # nối tên các entry phụ
                    entry = list(entry)  
                    entry[0] =""
                    entry[0] += sub_name  
                    entry = tuple(entry) 
                    sub_name = '' 
            
                entries.append(entry)
                sub_entries.clear()
            else:
                buffer_subentry += entry
                sub_entries.append(buffer[i:i+32])
                sub_entries.reverse()
                sub_name += ut.process_fat_lfnentries(sub_entries)
        return entries
    def print_RDET(self,buffer):
        print("FILE - DIRECTORY INFORMATION")
        for i in range (0, len(buffer)):
            if(buffer[i][1] ==0):
                break
            print("Name: ", buffer[i][0])
            print("Attribute: ", ut.describe_attr(buffer[i][1]))
            print("Cluster begin: ", buffer[i][2])
            print("Size: ", buffer[i][3])
    

file_fat32 = "drive_fat.bin"

bootsector_fat32 = ut.read_sector(file_fat32, 0, 1)
volume_fat32 = FAT32(bootsector_fat32)     
volume_fat32.print_bootsector()
RDET = ut.read_sector(file_fat32, volume_fat32.rdet_sector_begin, 1)
entries = volume_fat32.read_rdet( RDET)
volume_fat32.print_RDET(entries)



