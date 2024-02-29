import utility as ut
import re
from enum import Flag, auto
from datetime import datetime


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

def getPath(self, path):
    dirs = re.sub(r"[/\\]+", r"\\". path).strip("\\").split("\\")
    return dirs

class MFT_Record:
    def __init__(self, data):
        self.data = data
        self.MFT_ID = ut.read_dec_offset(self.data, 0x2C, 4)
        self.flag = ut.read_dec_offset(self.data, 0x16, 2)
        if(self.flag == 2 or self.flag == 0):
            raise Exception("Skip this record")
        standard_info_start = ut.read_dec_offset(self.data, 0x14, 2)
        standard_info_size = ut.read_dec_offset(self.data, standard_info_start + 4, 4)

        self.getStandardInfo(standard_info_start)

        file_name_start = standard_info_size + standard_info_start
        file_name_size = ut.read_dec_offset(self.data, file_name_start + 4, 4)

        self.getFileNameInfo(file_name_start)

        data_start = file_name_start + file_name_size
        data_sig = ut.read_dec_offset(self.data, data_start, 4)

        if(data_sig == 64): 
            data_start += ut.read_dec_offset(self.data, data_start + 4, 4) #Skip $OJECT_ID
            data_sig = ut.read_dec_offset(self.data, data_start + 4, 4)
        

        if(data_sig == 128):
            self.getData(data_start)
        elif(data_sig == 144):
            self.standard_flag |= NTFSAttribute.DIRECTORY
            self.data_len = 0
            self.data_resident = True
        self.childs: list[MFT_Record] = []

        del self.data



    def getStandardInfo(self, standard_start):
        opening_sig = ut.read_dec_offset(self.data, standard_start, 4)
        if(opening_sig != 16): #00 00 00 10
            raise Exception("Unknown")
        offset = ut.read_dec_offset(self.data, standard_start + 20, 2)
        begin = standard_start + offset
        self.standard_created_time = ut.read_dec_offset(self.data, begin, 8) #add as_datetime()
        self.standard_last_modified_time = ut.read_dec_offset(self.data, begin + 8, 8) # add as_datetime()
        self.standard_flag = NTFSAttribute(ut.read_dec_offset(self.data, begin + 32, 4) & 0xFFFF)

    def getFileNameInfo(self, fileName_start):   
        opening_sig = ut.read_dec_offset(self.data, fileName_start, 4)
        if(opening_sig != 48): #00 00 00 30
            raise Exception("Unknown")
        file_len = ut.read_dec_offset(self.data, fileName_start + 16, 4)
        offset = ut.read_dec_offset(self.data, fileName_start + 20, 2)
        
        file_body_offset = fileName_start + offset
        #file_body = self.data[fileName_start + offset:fileName_start + offset + file_len]

        self.file_parent_record_num = ut.read_dec_offset(self.data, file_body_offset, 6)
        fileName_length = ut.read_dec_offset(self.data, file_body_offset + 64, 1)
        self.long_fileName = ut.read_bin_offset(self.data, file_body_offset + 66, fileName_length * 2).decode('utf-16le')

    def getData(self, data_start):
        self.data_resident = not bool(self.data[data_start + 128])
        if (self.data_resident):
            offset = ut.read_dec_offset(self.data, data_start + 20, 2)
            self.data_len = ut.read_dec_offset(self.data, data_start + 16, 4)
            self.data_content = self.data[data_start + offset:data_start + offset + self.data_len]
        else: #data runs
            cluster_chain = self.data[data_start + 64]
            offset = (cluster_chain & 0xF0) >> 4
            size = cluster_chain & 0x0F
            self.data_len = ut.read_dec_offset(self.data, data_start + 48, 8)
            self.cluster_size = ut.read_dec_offset(self.data, data_start + 65, size)
            self.cluster_offset = ut.read_dec_offset(self.data, data_start + 65, size)

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
    root_directory = None
    size = None
    volumn_label = None
    file_object = None

    def __init__ (self, path):
        self.file_object = path
        
        pbs_sector = ut.read_sector(path, 0, 1)
        self.sector_size = ut.read_dec_offset(pbs_sector, 0x0B, 2)
        self.sc = ut.read_dec_offset(pbs_sector, 0x0D, 1)
        self.sb = ut.read_dec_offset(pbs_sector, 0x0E, 2)
        self.volumn_size = ut.read_dec_offset(pbs_sector, 0x28, 8)
        self.mft_begin_cluster = ut.read_dec_offset(pbs_sector, 0x30, 8)
        self.mft_mir_cluster =  ut.read_dec_offset(pbs_sector, 0x38, 8)
        self.cluster_per_file_record = int.from_bytes(pbs_sector[0x40:0x41],'little', signed = True)
        self.mft_record_size = 2 ** abs(self.cluster_per_file_record)


        self.record_size = self.mft_record_size
        self.mft_offset = self.mft_begin_cluster
        
        self.mft_file = MFT_FILE(ut.read_sector(self.file_object, self.mft_begin_cluster * self.sc, 2, self.sector_size))
        self.mft_record:list[MFT_Record] = []
        data_sector = self.mft_begin_cluster * self.sc + 2
        for _ in range(2, self.mft_file.num_sector, 2):
            data = ut.read_sector(self.file_object, data_sector , 2, self.sector_size)
            if(data[:4] == b"FILE" or data[:4] == b"BAAD"):
                try:
                    self.mft_record.append(MFT_Record(data))
                except Exception as e:
                    pass
            data_sector += 2
    
    def print_record(self):
        for i in self.mft_record:
            print("Name: ", i.long_fileName)
            print("\n")


    def pbs_sector(self):
        print("VOLUMN INFORMATION")
        print("Bytes/sector: ", self.sector_size)
        print("Sectors/cluster (Sc): ", self.sc)
        print("Reserved sectors (Sb): ", self.sb)
        print("Sectors in disk (Nv): ", self.volumn_size)
        print("MFT begin sector: ", self.mft_begin_cluster * self.sc)
        print("MFT Mirror begin sector: ", self.mft_mir_cluster)
        print("\n")

    


path = r'\\.\F:'
file = "drive_ntfs.bin"
drive = NTFS(file)     
#drive.pbs_sector()
drive.print_record()
