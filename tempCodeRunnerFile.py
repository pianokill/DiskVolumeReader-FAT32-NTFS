    def draw_tree(self, path, indent = '', is_last=True):
        if path != 'rdet':
            entry_begin = self.travel_to(path)
        else:
            entry_begin = ['rdet', 0x10, self.rdet_cluster_begin, '1']
        if ut.describe_attr(entry_begin[1]) != 'D' or entry_begin[3] == -1:
            print(path, ": is invalid!")
            return
        print(indent, end='')
        if is_last:
            print("└── ", end='')
            indent += "    "
        else:
            print("├── ", end='')
            indent += "│   "
        print(entry_begin[0])
        entries = self.read_directory(entry_begin)
        i = 0
        for entry in (entries):
            is_last = (i == len(entries) - 1)
            
            if ut.describe_attr(entry[1]) == 'D':
                if(path != 'rdet'):
                    item_path = path + "\\" + entry[0]
                else:
                    item_path = entry[0]
                self.draw_tree(item_path, indent, is_last)
            else:
                print(indent, end='')
                if is_last:
                    print("└── ", end='')
                else:
                    print("├── ", end='')
                print(entry[0])
            i+=1
