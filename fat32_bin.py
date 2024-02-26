import utility as ut

class FAT32:     
    def __init__(self, path):
        self.path = path
        bootsector = ut.read_sector(path, 0, 1)
        self.n_sectors_cluster = ut.read_dec_offset(bootsector, 0x0D, 1)  
        self.n_sectors_bootsector = ut.read_dec_offset(bootsector, 0x0E, 2)  
        self.n_fat_tables = ut.read_dec_offset(bootsector, 0x10, 1)  
        self.volume_size = ut.read_dec_offset(bootsector, 0x20, 4)  
        self.n_sectors_fat_table = ut.read_dec_offset(bootsector, 0x24, 4)  
        self.rdet_cluster_begin = ut.read_dec_offset(bootsector, 0x2C, 4)  
        self.sub_sector = ut.read_dec_offset(bootsector, 0x30, 2)  
        self.n_sectors_store_bootsector = ut.read_dec_offset(bootsector, 0x32, 2)  
        #FAT 32:
        #SECTORS IN BOOT SECTOR -> RESERVERD -> FAT TABLE -> ROOT DIRECTORY -> DATA AREA    
        self.rdet_sector_begin = self.n_sectors_bootsector + self.n_fat_tables * self.n_sectors_fat_table
        self.data_sector_begin = self.rdet_sector_begin
    def bootsector(self):
        print("BOOT SECTOR INFORMATION OF ", self.path)
        print("Sectors/cluster: ", self.n_sectors_cluster)
        print("Sectors/boot sector: ", self.n_sectors_bootsector)
        print("FAT Table: ", self.n_fat_tables)
        print("Sectors in disk: ", self.volume_size)
        print("Sectors in FAT table: ", self.n_sectors_fat_table)
        print("RDET Cluster Begin: ", self.rdet_cluster_begin)
        print("RDET Sector Begin: ", self.rdet_sector_begin)
        print("Subsector: ", self.sub_sector)
        print("Sector Store Boot sector: ", self.n_sectors_store_bootsector)
    def cluster_to_sectors(self, cluster_n):
        sector_begin = self.n_sectors_bootsector + self.n_fat_tables*self.n_sectors_fat_table + (cluster_n - 2)*self.n_sectors_cluster
        sectors = [sector_begin]
        for i in range(self.n_sectors_cluster - 1):
            sectors.append(sectors[-1] + 1)
        return sectors
    def sectors_chain(self, cluster_begin):
        fat_data = ut.read_sector(self.path, self.n_sectors_bootsector, self.n_sectors_fat_table)
        cluster_n = cluster_begin
        sectors_chain = []
        eof = [0x00000000, 0xFFFFFF0, 0xFFFFFFF, 0XFFFFFF7, 0xFFFFFF8, 0xFFFFFFF0]
        cluster_data = fat_data[8 + cluster_n*4:8 + cluster_n*4 + 4]
        cluster_data = ut.raw_to_dec(cluster_data)
        sectors_chain += (self.cluster_to_sectors(cluster_n))
        if cluster_data not in eof:
            for i in range(cluster_data - cluster_n - 1):
                cluster_n += 1
                cluster_data = fat_data[8 + cluster_n*4:8 + cluster_n*4 + 4]
                cluster_data = ut.raw_to_dec(cluster_data)
                sectors_chain += (self.cluster_to_sectors(cluster_n))
        return sectors_chain
    def read_data(self, cluster_begin):
        sectors = self.sectors_chain(cluster_begin)
        data = b''
        for sector in sectors:
            data.append(ut.read_sector(self.path, sector, 1))
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
    def read_directory(self, entry):
        sectors = self.sectors_chain(entry[2])
        buffer = ut.read_list_sectors(self.path,sectors)
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
    def travel_to(self, path):
        directories = path.split('/')
        entry = ['rdet', 'D', self.rdet_cluster_begin, 0]
        
        #Scan first directory in rdet
        for k in range(0, len(directories)):
            entries = self.read_directory(entry)
            for i in range (0, len(entries)):
                if directories[k] in entries[i][0]:
                    entry[2] = entries[i][2]
                    entry[0] = entries[i][0]
                    entry[1] = entries[i][1]
                    entry[3] = entries[i][3]
                    #self.print_directory(self.read_directory(entry))
                    #print(ut.describe_attr(entry[1]))
                    break
                else: 
                    entry[3] = -1
                
        return entry 
    def read_text_file(self,path, entry):
        sectors = self.sectors_chain(entry[2])
        
        # đọc sector và decode utf8
        content_txt_file = ut.read_list_sectors(path, sectors)
        print(content_txt_file.decode('utf-8'))
    def read_path(self, path):
        entry = self.travel_to(path)
        #print(self.cluster_to_sectors(entry[2]))
        print(entry[3])
        if ut.describe_attr(entry[1]) == 'D':
            self.read_directory(entry)
            print("D")
        elif ut.describe_attr(entry[1]) == "A" and entry[3] != -1:
            path = r'\\.\E:'
            self.read_text_file(path,entry)
            
            print("A")
        else:
            print("ERROR")
        
        
            
    
    

           

        

            
    def print_directory(self,buffer):
        print("FILE - DIRECTORY INFORMATION")
        for i in range (0, len(buffer)):
            if(buffer[i][1] ==0):
                break
            print("---")
            print("Name: ", buffer[i][0])
            print("Attribute: ", ut.describe_attr(buffer[i][1]))
            print("Cluster begin: ", buffer[i][2])
            print("Size: ", buffer[i][3])
           
path = r'\\.\E:'
drive = FAT32(path)     

#drive.bootsector()
#ut.print_xxd(bootsector)
#print(drive.cluster_to_sectors(133))
#drive.print_directory(entries)
#entries = drive.travel_to("Hoàng Diễn/con của Hoàng Diễn/phuonganhdao.txt")
drive.read_path("Hoàng Diễn/con của Hoàng Diễn/phuonganhdao.txt")
#drive.read_text_file(entry)
#print(drive.cluster_to_sectors(drive.rdet_cluster_begin))
# RDET = ut.read_sector(path, drive.data_sector_begin, 1)
# RDET = RDET[32*4:]
# entries = drive.read_rdet(RDET)
# drive.print_RDET(entries)

