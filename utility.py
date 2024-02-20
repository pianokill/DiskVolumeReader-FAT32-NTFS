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