from confluence import *

sync_files = []


def update(fn, **kwargs):
    print(fn)
    if confluence.read(fn, **kwargs):
        res = confluence.update_page()
        print("sync: ", "✅" if res else "❌")
        if res:
            sync_files.append(os.path.splitext(os.path.split(fn)[1])[0])
    print("=" * 40, "\n")


if __name__ == '__main__':

    confluence = Confluence()

    for folder in sync_folders:

        if isinstance(folder, str):
            print("Folder:", folder)
            for fn in find_all_files(folder):
                dir_title = os.path.dirname(fn).split("/")[-1]
                if dir_title not in confluence.cache['pages']:
                    print("Creating empty page in the root page:", dir_title)
                    confluence.read(dir_title, empty=True)
                    confluence.update_page()
                update(fn)
        elif isinstance(folder, dict):
            parent_title = folder['parent_title']
            for fn in find_all_files_with_tag(folder['path'], folder['tag'].lstrip("#")):
                if parent_title not in confluence.cache['pages']:
                    raise ValueError(f"Unknown page {parent_title}")
                update(fn, parent_title=parent_title)

        else:
            raise TypeError(f"Unable to process type {type(folder)}. 🥲")

    notify("Sync Confluence",
           subtitle=f"{len(sync_files)} modified files", message=", ".join(sync_files), method="terminal-notifier")
