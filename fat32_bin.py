import os

def dec(hex: str) -> int: 
    """
    Hàm đổi số hex ra số hệ thập phân (tham số nhận vào là chuỗi)
    Vd:
    >>> dec('0B')
    >>> dec('0C')
    """
    return int(hex, 16)

def read_sector(file, sector_begin=0, n_sector=1, bps=512):
    sec = None
    with open(file, mode='rb') as fp:
        fp.seek(bps*sector_begin)
        sec = fp.read(bps*n_sector)
    return sec
def read_offset(buffer, offset, size):
    begin = buffer[offset:offset + size]
    return dec(begin[::-1].hex())
    
bootsector_buffer = read_sector("drive_fat.bin", 0, 1)    
#print(bootsector_buffer[0x10:0x1A])
print(read_offset(bootsector_buffer, 0x010, 1))

#Hoan thien doc het BootSector
#Disk -> functions: bootsector, rdet, 
#FAT32 and NTFS
#Dien Kiet Son
