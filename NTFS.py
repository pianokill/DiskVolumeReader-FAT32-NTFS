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
        Sector_Size = self.sector_size
        record_offset = MFT_Begin_Sector
        self.read_all_entry(record_offset, MFT_Record_Size, Sector_Size)

    def read_all_entry(self, record_offset, MFT_Record_Size, Sector_Size):
        for _ in range(2, self.mft_file.num_sector, 2):
            data = ut.read_sector(self.file_object, record_offset, 1, self.sector_size)
            index = 0
            size = 0
            while (Sector_Size >= 0):
                if(MFT_Record_Size > self.sector_size):
                    data += ut.read_sector(self.file_object, record_offset + 1, 1, self.sector_size)
                    Sector_Size += self.sector_size
                    if(data[:4] == b"FILE"):
                        try:
                            record = self.read_MFTRecord(data)
                        except Exception as e:
                            pass
                    print("NAME: ", record["File_Name"], record["MFT_ID"], record["Parent_ID"])
                    record_offset += 1
                    break
                else:
                    size += MFT_Record_Size
                    raw_record = data[index:size]
                    index += MFT_Record_Size
                    Sector_Size -= MFT_Record_Size
                if(raw_record[:4] == b"FILE"):
                    try:
                        record = self.read_MFTRecord(raw_record)
                    except Exception as e:
                        pass
                    print("NAME: ", record["File_Name"], record["MFT_ID"], record["Parent_ID"])

            record_offset += 1
            Sector_Size = self.sector_size

    def pbs_sector(self):
        print("VOLUMN INFORMATION")
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
        #file_body = self.data[fileName_start + offset:fileName_start + offset + file_len]

        entry["Parent_ID"] = ut.read_dec_offset(data, file_body_offset, 6)
        fileName_length = ut.read_dec_offset(data, file_body_offset + 64, 1)
        entry["File_Name"] = ut.read_bin_offset(data, file_body_offset + 66, fileName_length * 2).decode('utf-16le')
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
            entry["Standard_Flag"] |= NTFSAttribute.DIRECTORY
            entry["Data_Length"] = 0
            entry["Data_Resident"] = True
     #-----------------------------------------------------------------------------------------------------------------#
        return entry

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


            


path = r'\\.\F:'
file = "drive_ntfs.bin"
drive = NTFS(file)     
#drive.pbs_sector()


        # for _ in range(2, self.mft_file.num_sector, 2):
        #     data = ut.read_sector(self.file_object, data_sector, 1, self.sector_size)
        #     data1 = data[:1024]
        #     data2 = data[-1024:]
        #     if(data1[:4] == b"FILE" and data[:4] == b"FILE"):
        #         try:
        #             record1 = self.read_MFTRecord(data1)
        #             record2 = self.read_MFTRecord(data2)
        #             print("NAME: ", record1["File_Name"], record1["MFT_ID"], record1["Parent_ID"])
        #             print("NAME: ", record2["File_Name"], record2["MFT_ID"], record2["Parent_ID"])
        #         except Exception as e:
        #             pass
        #     data_sector += 1


        # data_sector = self.mft_begin_cluster * self.sc + 22 #19 20 22 23
        # data = ut.read_sector(self.file_object, data_sector, 1, self.sector_size)
        # record = self.read_MFTRecord(data[:1024])
        # print(record["File_Name"])
        # #ut.print_xxd(record["Data_Content"])
        # print(record["Data_Content"].decode("utf-8"))

