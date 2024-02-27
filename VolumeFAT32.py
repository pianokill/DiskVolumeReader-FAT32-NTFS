import utility as ut
import os
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
        print("                         BOOT SECTOR INFORMATION OF", self.path)
        print("      - Sectors/cluster: ", self.n_sectors_cluster)
        print("      - Sectors/boot sector: ", self.n_sectors_bootsector)
        print("      - FAT Table: ", self.n_fat_tables)
        print("      - Sectors in disk: ", self.volume_size)
        print("      - Sectors in FAT table: ", self.n_sectors_fat_table)
        print("      - RDET Cluster Begin: ", self.rdet_cluster_begin)
        print("      - RDET Sector Begin: ", self.rdet_sector_begin)
        print("      - Subsector: ", self.sub_sector)
        print("      - Sector Store Boot sector: ", self.n_sectors_store_bootsector)
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
        eof_markers = {0x00000000, 0xFFFFFF0, 0xFFFFFFF, 0xFFFFFF7, 0xFFFFFF8, 0xFFFFFFF0}
        while cluster_n not in eof_markers:
            sectors_chain += self.cluster_to_sectors(cluster_n)
            fat_offset = cluster_n * 4
            fat_entry_bytes = fat_data[fat_offset:fat_offset + 4]
            cluster_n = ut.raw_to_dec(fat_entry_bytes)
        return sectors_chain
    def read_entry(self, buffer):
        # thông tin entry : tên, phần mở rộng, tập tin or thư mục, kích thước, ? cluster bắt đầu ?
        #tên
        name = ut.read_bin_offset(buffer,0,8).decode('utf-8', errors='ignore').strip()
        #trạng thái
        attr = ut.read_dec_offset(buffer,0xB,1)
        #cluster bắt đầu
        cluster_begin = ut.read_dec_offset(buffer,0x1A,2)
        #size
        size = ut.read_dec_offset(buffer,0x1C,4)
        #trạng thái
        
        e5 = ut.read_hex_offset(buffer, 0,1)
        return name, attr, cluster_begin, size ,e5 
    def read_directory(self, entry):
            sectors = self.sectors_chain(entry[2])
            buffer = ut.read_list_sectors(self.path,sectors)
            buffer = buffer[32*2:]
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
                    if( entry[4] !='00' and entry[4] != 'e5'  ):
                        entries.append(entry)
                    sub_entries.clear()
                else:
                    buffer_subentry += entry
                    sub_entries.append(buffer[i:i+32])
                    sub_entries.reverse()
                    sub_name += ut.process_fat_lfnentries(sub_entries)
            
            return entries
    def print_text_file(self,path, entry):
        sectors = self.sectors_chain(entry[2])
        # đọc sector và decode utf8
        content_txt_file = ut.read_list_sectors(path, sectors)
        content_txt_file = content_txt_file[:entry[3]]
        print(content_txt_file.decode('utf-8', errors='ignore'))
    def print_directory(self,buffer):
        print("DIRECTORY INFORMATION")
        for i in range (0, len(buffer)):
            print("---")
            print("Name: ", buffer[i][0])
            print("Attribute: ", ut.describe_attr(buffer[i][1]))
            print("Cluster begin: ", buffer[i][2])
            print("Size: ", buffer[i][3])       
    def travel_to(self, path):
        directories = path.split('\\')
        
        entry = ['rdet', 0, self.rdet_cluster_begin, 0]
        #Scan first directory in rdet
        for k in range(0, len(directories)):
            entries = self.read_directory(entry)
            
            for i in range (0, len(entries)):
                if directories[k] in entries[i][0]  :
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
    def read_path(self, path):
        entry = self.travel_to(path)
        print("PATH INFORMATION: ")
        print("NAME: ", entry[0])
        if(ut.describe_attr(entry[1]) == 'D'):
            print("ATTRIBUTE: Directory")
        elif(ut.describe_attr(entry[1]) == 'A'):
            print("ATTRIBUTE: File")
        print("CLUSTER BEGIN: ", entry[2])
        print("SIZE: ", entry[3])
        
        
        apps = {
        'pptx': 'PowerPoint',
        'csv': 'Spreadsheet Software',
        'json': 'Text Editor or JSON Viewer',
        'pdf': 'PDF Reader',
        'jpg': 'Image Viewer',
        'mp3': 'Audio Player',
        'mp4': 'Video Player',
        'png': 'Photos'
        # Thêm các định dạng file khác theo cần thiết
        }
        
        if ut.describe_attr(entry[1]) == 'D':
            self.draw_tree(path)
        elif ut.describe_attr(entry[1]) == "A" and entry[3] != -1 :
            self.print_text_file(self.path, entry)
        else:
            file_extension = path.split('.')[-1].lower()
           
            suggested_application = apps.get(file_extension, 'Unknown app')
            print("We currently do not support the functionality of reading this file. If you want to view the contents inside, you can use the following application: "+suggested_application )
    def draw_tree(self, path, indent = '', is_last=True):
        if path != 'rdet':
            entry_begin = self.travel_to(path)
            
        else:
            entry_begin = ['rdet', 0x10, self.rdet_cluster_begin, '1']
        if ut.describe_attr(entry_begin[1]) != 'D':
            print(path, ": is not a directory!")
            return
        
        print(indent, end='')
        if is_last:
            print("└── ", end='')
            indent += "    "
        else:
            print("├── ", end='')
            indent += "│   "
        print(entry_begin[0] + "/")
        entries = self.read_directory(entry_begin)
        i = 0
        for entry in (entries):
            is_last = (i == len(entries) - 1)
            if ut.describe_attr(entry[1]) == 'D':
                item_path = path + "/" + entry[0]
                self.draw_tree(item_path, indent, is_last)
            else:
                print(indent, end='')
                if is_last:
                    print("└── ", end='')
                else:
                    print("├── ", end='')
                print(entry[0])
            i+=1
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
def main_screen():
    
    print("FAT32 AND NTFS EXPLORER PROJECT --  FIT HCMUS  --  22CLC07 \n")
    print("----------------------------------------------------------")
    print(" 22127222 - Nguyễn Thanh Tuấn Kiệt")
    print(" 22127    - Nguyễn Minh Sơn")
    print(" 22127068 - Trần Nguyễn Hoàng Diễn")
    print("----------------------------------------------------------")
    #path = input("Please provide your drive name: ")
    path = "E"
    path = r'\\.\\'+path+":"
    drive = FAT32(path)
    clear_screen() 
    while True:
        print("---------------------------------------------WORKING WITH DRIVE",path,"---------------------------------------------\n")
        print("                                                 MENU\n") 
        print("                                        1. Read bootsector")
        print("                                        2. Print tree of directory")
        print("                                        3. Display the content of a file.")
        print("                                        4. Quit") 
        choice = input("Please input your choice: ")
        if choice == '1':
            clear_screen()
            drive.bootsector()
        elif choice == '2':
            directory = input("Please enter directory name: ")
            drive.read_path(directory)
            drive.draw_tree(directory)
        elif choice == '3':
            path_to_file = input("Please enter path to file: ")
            drive.read_path(path_to_file.strip())
        elif choice == '4':
            print("GOODBYE!")
            break
        else:
            print("Chọn không hợp lệ. Hãy chọn lại.")

#drive.bootsector()    
main_screen()

# rdet_entry = ['rdet', 0x10, drive.rdet_cluster_begin, 1]
# entries_rdet = drive.read_directory(rdet_entry)
# drive.print_directory(entries_rdet)
#path = r'\\.\E:'
#path = r'\\.\\'+path+":"
##drive = FAT32(path)
#drive.read_path("Hoàng Diễn")
#drive.draw_tree('Hoàng Diễn')
