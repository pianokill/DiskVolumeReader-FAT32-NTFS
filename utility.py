import os

def dec(hex: str) -> int: 
    return int(hex, 16)
def read_sector(file, sector_begin=0, n_sector=1, bps=512):
    sec = None
    with open(file, mode='rb') as fp:
        fp.seek(bps*sector_begin)
        sec = fp.read(bps*n_sector)
    return sec
def read_bin_offset(buffer, offset, size):
    begin = buffer[offset:offset + size]
    return begin
def read_dec_offset(buffer, offset, size):
    begin = buffer[offset:offset + size]
    return dec(begin[::-1].hex())
def read_hex_offset(buffer, offset, size):
    begin = buffer[offset:offset + size]
    return begin.hex()
def describe_attr(attr):
        #tất cả thuộc tính
        attributes = {
            0x10: 'D',
            0x20: 'A',
            0x01: 'R', 
            0x02: 'H',
            0x04: 'S',
        }
        des = ''
        for attribute in attributes:
            if attr & attribute == attribute:
                des += attributes[attribute]
        
        return des 
def process_fat_lfnentries(subentries: list):
        """
        Hàm join các entry phụ lại thành tên dài
        """
        name = b''
        for subentry in subentries:
            name += read_bin_offset(subentry, 1, 10)
            name += read_bin_offset(subentry, 0xE, 12)
            name += read_bin_offset(subentry, 0x1C, 4)
        name = name.decode('utf-16le', errors='ignore')

        if name.find('\x00') > 0:
            name = name[:name.find('\x00')]
        return name