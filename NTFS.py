import utility as ut
import re
from enum import Flag, auto
from datetime import datetime
import os

class NTFSAttribute(Flag):
    READ_ONLY = auto()
    HIDDEN = auto()
    SYSTEM = auto()
    VOLLABLE = auto()
    DIRECTORY = auto()
    ARCHIVE = auto()
    DEVICE = auto()
    NORMAL = auto()
    TEMPOARY = auto()
    SPARSE_FILE = auto()
    REPARSE_POINT = auto()
    COMPRESSED = auto()
    OFFLINE = auto()
    NOT_INDEXED = auto()
    ENCRYPTED = auto()
def as_datetime(timestamp):
     return datetime.fromtimestamp((timestamp - 116444736000000000) / 10000000)

class MFT_FILE:
    def __init__(self, data):
        self.data = data
        self.fileID = ut.read_bin_offset(self.data, 0x00, 4)
        self.standard_info_offset = ut.read_dec_offset(self.data, 0x14, 2)
        self.standard_info_size = ut.read_dec_offset(self.data, 0x3C, 4)
        self.file_name_offset = self.standard_info_offset + self.standard_info_size
        self.file_name_size = ut.read_dec_offset(self.data, 0x9C, 4)
        self.data_offset = self.file_name_offset + self.file_name_size
        self.data_size = ut.read_dec_offset(self.data, 0x104, 4)
        self.num_sector = (ut.read_dec_offset(self.data, 0x118, 2) + 1) * 8 #xem lại
        del self.data
class NTFS:
    def __init__ (self, path):
        self.file_object = path
        pbs_sector = ut.read_sector(path, 0, 1)
        self.sector_size = ut.read_dec_offset(pbs_sector, 0x0B, 2)
        self.sc = ut.read_dec_offset(pbs_sector, 0x0D, 1)
        self.sb = ut.read_dec_offset(pbs_sector, 0x0E, 2)
        self.volumn_size = ut.read_dec_offset(pbs_sector, 0x28, 8)
        self.mft_begin_cluster = ut.read_dec_offset(pbs_sector, 0x30, 8)
        self.mft_mir_cluster =  ut.read_dec_offset(pbs_sector, 0x38, 8)
        self.mft_file = MFT_FILE(ut.read_sector(self.file_object, self.mft_begin_cluster * self.sc, 2, self.sector_size))
        self.cluster_per_record = int.from_bytes(pbs_sector[0x40:0x41], byteorder='little', signed=True)
        MFT_Begin_Sector = self.mft_begin_cluster * self.sc
        MFT_Record_Size = 2**abs(self.cluster_per_record)
        record_offset = MFT_Begin_Sector
        self.records = self.read_all_records(record_offset, MFT_Record_Size) #Storing in dynamic memory -> saving reading time after this
    def pbs_sector(self):
        print("VOLUME INFORMATION")
        print("Bytes/sector: ", self.sector_size)
        print("Sectors/cluster (Sc): ", self.sc)
        print("Reserved sectors (Sb): ", self.sb)
        print("Sectors in disk (Nv): ", self.volumn_size)
        print("MFT begin sector: ", self.mft_begin_cluster * self.sc)
        print("MFT Mirror begin sector: ", self.mft_mir_cluster)
        print("\n")    
    def read_MFTRecord(self, data):
        entry = {}
        entry["MFT_ID"] = ut.read_dec_offset(data, 0x2C, 4)
        entry["MFT_Flag"] = ut.read_dec_offset(data, 0x16, 2)
        if(entry["MFT_Flag"] == 2 or entry["MFT_Flag"] == 0):
            raise Exception("Skip this record")
        standard_info_start = ut.read_dec_offset(data, 0x14, 2)
        standard_info_size = ut.read_dec_offset(data, standard_info_start + 4, 4)
    #------------------------------STANDARD INFO ATTRIBUTE-------------------------------------#
        opening_sig = ut.read_dec_offset(data, standard_info_start, 4)
        if(opening_sig != 16): #00 00 00 10
            raise Exception("Unknown")
        offset = ut.read_dec_offset(data, standard_info_start + 20, 2)
        begin = standard_info_start + offset
        entry["Created_time"] = ut.read_dec_offset(data, begin, 8) #add as_datetime()
        entry["Last_modified_time"] = ut.read_dec_offset(data, begin + 8, 8) # add as_datetime()
        entry["Standard_Flag"] = NTFSAttribute(ut.read_dec_offset(data, begin + 32, 4) & 0xFFFF)
    #-------------------------------------------------------------------------------------------#
        file_name_start = standard_info_size + standard_info_start
        file_name_size = ut.read_dec_offset(data, file_name_start + 4, 4)
    #-----------------------------------------------FILE NAME ATTRIBUTE-----------------------------------------------#
        opening_sig = ut.read_dec_offset(data, file_name_start, 4)
        if(opening_sig != 48): #00 00 00 30
            raise Exception("Unknown")
        file_len = ut.read_dec_offset(data, file_name_start + 16, 4)
        offset = ut.read_dec_offset(data, file_name_start + 20, 2)
        
        file_body_offset = file_name_start + offset
        file_body = data[file_name_start + offset:file_name_start + offset + file_len]

        entry["Parent_ID"] = ut.read_dec_offset(data, file_body_offset, 6)
        fileName_length = file_body[64]
        entry["File_Name"] = file_body[66:66 + fileName_length * 2]
    #-----------------------------------------------------------------------------------------------------------------#
        data_start = file_name_start + file_name_size
        data_sig = data[data_start:data_start + 4]


        if(data_sig[0] == 64): 
            data_start += ut.read_dec_offset(data, data_start + 4, 4) #Skip $OJECT_ID

        data_sig = data[data_start:data_start + 4]
     #-------------------------------------------------DATA ATTRIBUTE-----------------------------------------------#
        if(data_sig[0] == 128):
            entry["Data_Resident"] = not bool(data[data_start + 8])
            if ( entry["Data_Resident"]):
                offset = ut.read_dec_offset(data, data_start + 20, 2)
                entry["Data_Length"] = ut.read_dec_offset(data, data_start + 16, 4)
                entry["Data_Content"] = data[data_start + offset:data_start + offset + entry["Data_Length"]]
                entry["Cluster_Size"] = None
                entry["Cluster_Offset"] = None
            else: #data runs
                cluster_chain = data[data_start + 64]
                offset = (cluster_chain & 0xF0) >> 4
                size = cluster_chain & 0x0F
                entry["Data_Length"] = ut.read_dec_offset(data, data_start + 48, 8)
                entry["Cluster_Size"] = ut.read_dec_offset(data, data_start + 65, size)
                entry["Cluster_Offset"] = ut.read_dec_offset(data, data_start + 65 + size, size + offset)

        elif(data_sig[0] == 144):
            entry["Standard_Flag"] = "Directory"
            entry["Data_Length"] = 0
            entry["Data_Resident"] = True
     #-----------------------------------------------------------------------------------------------------------------#
        return entry
    def read_all_records(self, record_offset, MFT_Record_Size):
        records = []
        if(self.sector_size == 512):
            for _ in range(2, self.mft_file.num_sector, 2):
                data = ut.read_sector(self.file_object, record_offset, 2, self.sector_size)
                if(data[:4] == b"FILE"):
                    try:
                        record = self.read_MFTRecord(data)
                        record["File_Name"] = record["File_Name"].decode("utf-16le")
                        if(record["File_Name"].startswith("$")):
                            pass
                        else:
                            records.append(record)
                    except Exception as e:
                        pass
                record_offset += 2
        else:    
            for _ in range(2, self.mft_file.num_sector, 2):
                data = ut.read_sector(self.file_object, record_offset, 1, self.sector_size)
                index = 0
                size = 0
                n = self.sector_size
                while (n >= 0):
                    size += MFT_Record_Size
                    raw_record = data[index:size]
                    index += MFT_Record_Size
                    n -= MFT_Record_Size
                    if(raw_record[:4] == b"FILE"):
                        try:
                            record = self.read_MFTRecord(raw_record)
                            record["File_Name"] = record["File_Name"].decode("utf-16le")
                            if(record["File_Name"].startswith("$")):
                                continue
                            else:
                                records.append(record)
                        except Exception as e:
                            continue
                record_offset += 1
        return records
    def record_Filename(self, id):
        for record in self.records:
            if record["MFT_ID"] == id:
                return record["File_Name"]
        return -1
    def record_Type(self, id):
        for record in self.records:
            if record["MFT_ID"] == id:
                print(record["Standard_Flag"])
                return record["Standard_Flag"]
        return -1
    def read_directory(self, id):
        sub_ids = []
        for record in self.records:
            if record["Parent_ID"] == id:
                sub_ids.append(record["MFT_ID"])
        return sub_ids
    def travel_to(self, path):
        #Tailieu1\Tailieu2\file.txt
        directories = path.split('\\')
        id_current = 5
        for k in range(0, len(directories)):
            found = False
            sub_ids = self.read_directory(id_current)
            for id in sub_ids:
                filename = self.record_Filename(id)
                if filename == directories[k]:
                    found = True
                    id_current = id
                    break
            if found == False:
                raise Exception("NOT FOUND")
        return id_current 
    def draw_tree(self, path, indent = '', is_last=True):
        if path != 5:
            id_current = self.travel_to(path)
            if self.record_Type(id_current) != "Directory":
                print("Not a directory!")
                return
        else: 
            id_current = 5

        print(indent, end='')
        if is_last:
            print("└── ", end='')
            indent += "    "
        else:
            print("├── ", end='')
            indent += "│   "
        print(self.record_Filename(id_current))
        sub_ids = self.read_directory(id_current)
        i = 0
        for id in (sub_ids):
            is_last = (i == len(sub_ids) - 1)
            
            if (self.record_Type(id)) == "Directory":
                if(path != 5):
                    item_path = path + "\\" + self.record_Filename(id)
                else:
                    item_path = self.record_Filename(id)
                self.draw_tree(item_path, indent, is_last)
            else:
                print(indent, end='')
                if is_last:
                    print("└── ", end='')
                else:
                    print("├── ", end='')
                print(self.record_Filename(id))
            i+=1

    def parse_data(self, record):
        if (record == None):
            raise Exception ("Emty MFT entry, can not parse data")
        if(record["Data_Resident"]):
            return record["Data_Content"]
        else:
            data_content = b""
            size_left = record["Data_Length"]
            sector_offset = record["Cluster_Offset"] * self.sc
            cluster_num = record["Cluster_Size"]

            for _ in range(cluster_num):
                if size_left <= 0:
                    break
                raw_data = ut.read_sector(self.file_object, sector_offset, 1, self.sector_size)
                size_left -= self.sc * self.sector_size
                sector_offset += 1
                try:
                    data_content += raw_data
                except Exception as e:
                    raise Exception("Something wrong")
            return data_content

logical_disks = ut.list_logical_disks()
for disk in logical_disks:
    print(f"Mountpoint: {disk['mountpoint']}, Filesystem Type: {disk['filesystem_type']}")
path = input("Please provide your drive name: ")
path = r'\\.\\'+path+":"
drive = NTFS(path)    
#drive.draw_tree(5)



#drive.pbs_sector()


