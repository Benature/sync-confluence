from utils import *


class Confluence():
    def __init__(self):
        self.version = 1
        self.cache = self.load_cache()

    def load_cache(self):
        self.cache_path = os.path.join(root_path, f"cache/{USER}.json")
        print("Preparing cache (page tree) ...")
        T = Tree()
        T.spider()
        T.save()

        with open(self.cache_path, "r") as f:
            return json.load(f)

    def reset(self):
        self.try_num = 0

    def gen_content(self, markdown):
        self.reset()
        markdown = re.sub(r"^---(\n.*?)\n---", md_meta,
                          markdown, count=1, flags=re.S)  # meta data
        markdown = re.sub(r"\[\[([^\[\]\s]+)\]\]",
                          wiki2link, markdown)  # wiki link

        # ^[upper content]
        markdown = re.sub(r"\n.*?\^\[.+?\].*?\n", upper_content, markdown)

        # tx table in Obsidian plugin
        markdown = re.sub(r"\n-tx-\n", "\n", markdown)
        markdown = re.sub(r"\| *?\^\^ *?\|",
                          lambda m: m.group(0).replace("^^", "\\^\\^"), markdown)

        # ad code box in Obsidian plugin
        markdown = re.sub(r"```ad-[a-z]+(.*?)```",
                          lambda m: m.group(1), markdown, flags=re.S)

        for k, v in replace_items.items():
            markdown = markdown.replace(k, v)
        content = f"<p class=\"auto-cursor-target\"><br /></p><table class=\"wysiwyg-macro\" style=\"background-image: url('{BASE_URL}/plugins/servlet/confluence/placeholder/macro-heading?definition=e25vdGV9&amp;locale=en_US&amp;version=2'); background-repeat: no-repeat;\" data-macro-name=\"note\" data-macro-schema-version=\"1\" data-macro-body-type=\"RICH_TEXT\" data-macro-id=\"aa1f3166-0644-4546-b0e3-0cf62607bcdb\"><tbody><tr><td class=\"wysiwyg-macro-body\"><p><span style=\"color: #a5adba;\"><em>本页面为脚本自动上传，额外修改将有被覆盖风险。</em></span></p></td></tr></tbody></table><p class=\"auto-cursor-target\"><br /></p><table class=\"wysiwyg-macro\" style=\"background-image: url('{BASE_URL}/plugins/servlet/confluence/placeholder/macro-heading?definition=e21hcmtkb3dufQ&amp;locale=en_US&amp;version=2'); background-repeat: no-repeat;\" data-macro-name=\"markdown\" data-macro-schema-version=\"1\" data-macro-body-type=\"PLAIN_TEXT\" data-macro-id=\"29063946-553e-4373-a400-b4dae28334b7\"><tbody><tr><td class=\"wysiwyg-macro-body\"><pre>{markdown}</pre></td></tr></tbody></table><p class=\"auto-cursor-target\"><br /></p>"
        self.markdown = markdown
        return content

    def get_page_id(self, title):
        page_id = self.cache['pages'][title]['page_id']
        if page_id is None:
            page_id = get_page_id(title, force=True)
            self.cache['pages'][title]['page_id'] = page_id
            with open(self.cache_path, "w") as f:
                json.dump(self.cache, f, ensure_ascii=False)
        return page_id

    def read(self, fn, empty=False, parent_title=None):
        if empty:
            markdown = ""
            assert fn != "" and "/" not in fn
            self.title = fn
            self.parent_title = ""
        else:
            with open(fn, "r") as f:
                markdown = f.read()
            self.title = fn.split("/")[-1].replace(".md", "")
            if parent_title is None:
                self.parent_title = os.path.dirname(fn).split("/")[-1]
            else:
                self.parent_title = parent_title
            print("title       :", self.title)
            print("parent title:", self.parent_title)

        try:
            self.content = self.gen_content(markdown)
            self.page_id = re.findall(
                "confluence:[ ]*(\d+)", markdown)[0]
            if not self.is_modified():
                print("⏭  No modified, jumping this page...")
                return False
        except IndexError:
            print("No confluence page id is recorded in the markdown file.")
            if self.title in self.cache['pages']:
                self.page_id = self.get_page_id(self.title)
                print(
                    f"Find the page id in the pages tree, the id is {self.page_id}")
            else:
                print("No confluence page id found, creating a new page for it...")
                self.page_id = self.create_page()
            print("Adding confluence page id to markdown metadata...")
            if not empty:
                markdown = re.sub(r"^---\n.*?\n---", lambda m: m.group(0).rstrip('-') +
                                  f"confluence: {self.page_id}\n---", markdown, flags=re.S)
                with open(fn, "w") as f:
                    f.write(markdown)
                self.content = self.gen_content(markdown)

        return True

    def gen_payload(self):
        payload = {
            "status": "current",
            "title": self.title,
            "space": {"key": f"~{USER}"},
            "body": {
                "editor": {
                    "value": self.content,
                    "representation": "editor",
                    "content": {"id": self.page_id}
                }
            },
            "id": self.page_id,
            "type": "page",
            "version": {
                "number": self.version,
                "message": "",
                "minorEdit": False,
            },
        }

        if self.parent_title in self.cache['pages']:
            parent_page_id = self.get_page_id(self.parent_title)
            # parent_cache = self.cache['pages'][self.parent_title]
            # parent_page_id = parent_cache['page_id']
            # if parent_page_id is None:
            #     parent_page_id = get_page_id(self.parent_title, force=True)
            #     self.cache['pages'][self.parent_title]['page_id'] = parent_page_id
            #     with open(self.cache_path, "w") as f:
            #         json.dump(self.cache, f, ensure_ascii=False)

            payload.update(
                {"ancestors": [{"id": parent_page_id, "type": "page"}]})
        return payload

    def update_page(self):
        response = requests.put(
            f"{BASE_URL}/rest/api/content/{self.page_id}",
            headers=headers,
            json=self.gen_payload()
        )
        if response.status_code == 200:
            print(
                f"http://wiki.dds-sysu.tech/pages/viewpage.action?pageId={self.page_id}")
            return True
        elif response.status_code == 409:
            try:
                current_version = re.findall(
                    r'Current version is: (\d+)', json.loads(response.text)['message'])[0]
                print("current version:", current_version)
                self.version = int(current_version) + 1
                self.try_num += 1
                if self.try_num < TRY_MAX:
                    return self.update_page()
                else:
                    print("fail too many times, exit.")
                    return False
            except Exception as e:
                print(e)
                print(json.loads(response.text))
                return False
        print(response.status_code)
        print(response.text)
        return False

    def create_page(self):
        self.version = 1
        response = requests.get(
            f"{BASE_URL}/pages/createpage.action?spaceKey=~wbenature&fromPageId={self.cache['base_page_id']}&src=quick-create", headers=headers)
        soup = BS(response.text, "lxml")
        page_id = soup.select('meta[name="ajs-content-id"]')[0]['content']
        return page_id

    def is_modified(self):
        response = requests.get(
            f"{BASE_URL}/pages/resumedraft.action?draftId={self.page_id}", headers=headers)
        soup = BS(response.text, "lxml")
        soup_md = BS(soup.select("#wysiwygTextarea")[0].next_element, 'lxml')

        local = self.markdown.replace(
            "&lt;", "<").replace("&gt;", ">").strip(" \n")
        remote = soup_md.select("pre")[0].next_element.strip(" \n")

        if local != remote:  # markdown file content is modified
            print("markdown file content is modified.")
            return True

        if self.title not in self.cache['pages']:  # markdown title is modified
            print("markdown title is modified.")
            return True

        prefix = self.cache['pages'][self.title]['prefix']
        if len(prefix) > 0:
            if self.parent_title != prefix[-1]:
                print(
                    f"markdown file is moved. (from {prefix[-1]} to {self.parent_title})")
                return True

        return False
