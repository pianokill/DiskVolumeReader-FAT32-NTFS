import os

def little_endian(data):
    return data[::-1]
def raw_to_dec(data):
    data_reversed = little_endian(data)
    hex_values = data_reversed.hex()
    return int(hex_values, 16)
def read_sector(path, sector_begin=0, n_sector=1, bps=512):
    sec = None
    with open(path, mode='rb') as fp:
        fp.seek(bps*sector_begin)
        sec = fp.read(bps*n_sector)
    return sec
def read_bin_offset(buffer, offset, size):
    begin = buffer[offset:offset + size]
    return begin
def read_dec_offset(buffer, offset, size):
    data = buffer[offset:offset + size]
    return raw_to_dec(data)
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
def print_xxd(data):
    offset = 0
    while offset < len(data):
        chunk = data[offset:offset+16]
        hex_chunk = ' '.join([f'{byte:02X}' for byte in chunk])
        ascii_chunk = ''.join([chr(byte) if 32 <= byte <= 126 else '.' for byte in chunk])
        print(f'{offset:08X}: {hex_chunk.ljust(48)}  {ascii_chunk}')
        offset += 16