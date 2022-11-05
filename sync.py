# %%
from confluence import *

# %%
if __name__ == '__main__':
    confluence = Confluence()
    for folder in sync_folders:
        print("Folder:", folder)
        for fn in findAllFile(folder):
            dir_title = os.path.dirname(fn).split("/")[-1]
            if dir_title not in confluence.cache['pages']:
                print("Creating empty page in the root page:", dir_title)
                confluence.read(dir_title, empty=True)
                confluence.update_page()
            print(fn)
            if confluence.read(fn):
                # print(confluence.content)
                # break
                res = confluence.update_page()
                print("sync: ", "✅" if res else "❌")

            print("=" * 40, "\n")
