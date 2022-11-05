# %%
from utils import *

# %%
if __name__ == '__main__':
    confluence = Confluence()
    for fn in findAllFile(sync_folder):
        print(fn)
        if confluence.read(fn):
            # print(confluence.content)
            res = confluence.update_page()
            print("sync: ", res)

        print("=" * 30, "\n")
