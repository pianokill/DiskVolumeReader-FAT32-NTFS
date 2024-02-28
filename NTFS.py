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

    def getStandardInfo(self, start):
        opening_sig = ut.read_dec_offset(self.data, start, 4)
        if(opening_sig != 16): #00 00 00 10
            raise Exception("Unknown")
        offset = ut.read_dec_offset(self.data, start + 20, 1)
        begin = start + offset
        self.standard_created_time = ut.read_dec_offset(self.data, begin, 8) #add as_datetime()
        

class MFT_Entry:
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
        self.mft_begin = self.sc * ut.read_dec_offset(pbs_sector, 0x30, 8)
        self.mft_mir = self.sc * ut.read_dec_offset(pbs_sector, 0x38, 8)
        self.mft_table = ut.read_sector(self.file_object, self.mft_begin, 1, self.sector_size)

        self.mft_entry = MFT_Entry(self.mft_table)
        self.mft = MFT_Record(self.mft_table)

    def pbs_sector(self):
        print("VOLUMN INFORMATION")
        print("Bytes/sector: ", self.sector_size)
        print("Sectors/cluster (Sc): ", self.sc)
        print("Reserved sectors (Sb): ", self.sb)
        print("Sectors in disk (Nv): ", self.volumn_size)
        print("MFT begin sector: ", self.mft_begin)
        print("MFT Mirror begin sector: ", self.mft_mir)
        print("\n")

    


path = r'\\.\F:'
file = "drive_ntfs.bin"
drive = NTFS(file)     
drive.pbs_sector()

