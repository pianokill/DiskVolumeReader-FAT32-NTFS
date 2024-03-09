from VolumeFAT32 import FAT32
from VolumeNTFS import NTFS
import os 
import utility as ut

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
def main_screen():
    print("FAT32 AND NTFS EXPLORER PROJECT --  FIT HCMUS  --  22CLC07 \n")
    print("----------------------------------------------------------")
    print(" 22127222 - Nguyễn Thanh Tuấn Kiệt")
    print(" 22127    - Nguyễn Minh Sơn")
    print(" 22127068 - Trần Nguyễn Hoàng Diễn")
    print("----------------------------------------------------------")
    logical_disks = ut.list_logical_disks()
    for disk in logical_disks:
        print(f"Mountpoint: {disk['mountpoint']}, Filesystem Type: {disk['filesystem_type']}")
    path = input("Please provide your drive name: ")
    type = ""
    found_disk = False
    for disk in logical_disks:
        if path.upper() == disk['mountpoint'][0]:
            type = disk['filesystem_type']
            found_disk = True
            break
    if found_disk == False:
        print(f"No disk found for path: {path}")
        return
    path = r'\\.\\'+path+":"
    if type == "FAT32":
        drive = FAT32(path)
    else:
        drive = NTFS(path)
    clear_screen() 
    while True:
        print("---------------------------------------------WORKING WITH DRIVE",path.upper(), "(", type,")---------------------------------------------\n")
        print("                                                 MENU\n") 
        print("                                        1. Print bootsector of ", path)
        print("                                        2. Draw a tree of a particular directory('rdet' if FAT32/'5' if NTFS/path of a directory)")
        print("                                        3. Display the content of a file/a directory.")
        print("                                        4. Quit") 
        choice = input("Please input your choice: ")
        if choice == '1':
            clear_screen()
            drive.bootsector()
        elif choice == '2':
            directory = input("Please enter a directory path: ")
            drive.draw_tree(directory)
        elif choice == '3':
            path_to_file = input("Please enter a path: ")
            #drive.read_path(path_to_file.strip())
        elif choice == '4':
            print("GOODBYE!")
            break
        else:
            print("Invalid choice, please choose again!")

main_screen()
