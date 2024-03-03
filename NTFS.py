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

        self.mft_file = MFT_FILE(ut.read_sector(self.file_object, self.mft_begin_cluster * self.sc, 2, self.sector_size))

        data_sector = self.mft_begin_cluster * self.sc + 19 #19 20 22
        data = ut.read_sector(self.file_object, data_sector, 1, self.sector_size)
        data1 = data[-1024:]
        record = self.read_MFTRecord(data1)
        print(record["Data_Content"])

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
            entry["Data_Content"] = data[data_start + offset:]
            entry["Data_Offset"] = ut.read_dec_offset(data, data_start + 20, 2)
     #-----------------------------------------------------------------------------------------------------------------#
        return entry

    def get_subdirectory_entry(self, file_name):
        # Assuming 'entries' is a list of directory entries with names and corresponding entry objects
        # You need to replace this with the actual data structure and logic used in your code
        entries = [
            {"File_Name": "Subdirectory1", "Entry_Object": {...}},  # Replace {...} with the actual entry object
            {"File_Name": "Subdirectory2", "Entry_Object": {...}},  # Replace {...} with the actual entry object
            # Add more entries as needed
        ]

        # Search for the subdirectory entry by comparing file names
        for entry in entries:
            if entry["File_Name"] == file_name:
                return entry["Entry_Object"]  # Return the entry object for the subdirectory

        # Return None if the subdirectory entry is not found
        return None

    def read_directory(self, entry):
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
        if entry["Standard_Flag"] == NTFSAttribute.DIRECTORY:
            directory_content = entry["Data_Content"]
            file_names = directory_content.split(b'\x00')
            file_names = [name.decode('utf-16le') for name in file_names if name]

        print("Directory Content:")
        for file_name in file_names:
            print(file_name)
        else:
            print("Not a directory or no content available")

    def parse_mft_data(self, raw_data):
        # This function parses a simplified MFT record structure. 
        # You might need to adjust it based on the actual MFT record format.

        # Extract basic information
        record_size = int.from_bytes(raw_data[:4], byteorder='little')
        file_reference = int.from_bytes(raw_data[4:8], byteorder='little')
        record_attributes = int.from_bytes(raw_data[8:12], byteorder='little')

        # Print basic information
        print(f"Record Size: {record_size}")
        print(f"File Reference: {file_reference}")
        print(f"Record Attributes: {record_attributes}")

        # Check if directory flag is set
        if record_attributes & 0x00000010:
            print("Folder Attributes:")
            # Might need to parse additional data for timestamps etc. depending on MFT format
            offset = 12 # Adjust offset based on actual data structure
            while offset < 20:
            # Extract file/subdirectory information (assuming fixed size entries)
                entry_size = int.from_bytes(raw_data[offset:offset+4], byteorder='little')
                filename_offset = int.from_bytes(raw_data[offset+4:offset+8], byteorder='little')
                file_reference = int.from_bytes(raw_data[offset+8:offset+12], byteorder='little')

            # Print filename (assuming entry starts with filename)
            filename = raw_data[offset+filename_offset:].decode('utf-16')
            print(f"\t- {filename} (File Reference: {file_reference})")

            # Update offset for next entry
            offset += 1

        else:
            print("This is not a folder record.")

    def get_data_content(self, cluster):
        return



            

    


path = r'\\.\F:'
file = "drive_ntfs.bin"
drive = NTFS(path)     
#drive.pbs_sector()

 #while(data_sector < self.volumn_size):
            #data = ut.read_sector(self.file_object, data_sector, 1, self.sector_size)
            #data1 = data[:1024]
            #data2 = data[-1024:]
            #if(data1[:4] == b"FILE" and data[:4] == b"FILE"):
                #try:
                    #record1 = MFT_Entry(data1)
                    #record2 = MFT_Entry(data2)
                    #print("NAME: ", record1.long_fileName)
                    #print("NAME: ", record2.long_fileName)
                #except Exception as e:
                    #pass
            #data_sector += 1


        #self.record_size = self.mft_record_size
        #self.mft_offset = self.mft_begin_cluster

