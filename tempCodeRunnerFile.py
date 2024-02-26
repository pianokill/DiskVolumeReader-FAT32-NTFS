rdet_entry = ['rdet', 0x10, drive.rdet_cluster_begin, 1]
entries_rdet = drive.read_directory(rdet_entry)
drive.print_directory(entries_rdet)