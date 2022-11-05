import requests
import os
import re
import json
from config import *


replace_items = {
    "<": "&lt;",
    ">": "&gt;",
    "\n": "  \n",
}

headers = {
    'Cookie': cookie,
    'Content-Type': 'application/json'
}


def findAllFile(base):
    for root, ds, fs in os.walk(base):
        for f in fs:
            if f.lower().endswith('.md'):
                fullname = os.path.join(root, f)
                yield fullname


def wiki2link(m):
    title = m.group(1)
    return f"[{title}](http://wiki.dds-sysu.tech/display/~{USER}/{title})"


class Confluence():
    def __init__(self):
        self.version = 17
        self.try_num = 0

    def reset(self):
        self.try_num = 0

    def gen_content(self, markdown):
        self.reset()
        markdown = re.sub(r"^---.*?\n---", "", markdown, count=1, flags=re.S)
        markdown = re.sub(r"\[\[([^\[\]\s]+)\]\]", wiki2link, markdown)
        for k, v in replace_items.items():
            markdown = markdown.replace(k, v)
        content = f"<p class=\"auto-cursor-target\"><br /></p><table class=\"wysiwyg-macro\" style=\"background-image: url('http://wiki.dds-sysu.tech/plugins/servlet/confluence/placeholder/macro-heading?definition=e25vdGV9&amp;locale=en_US&amp;version=2'); background-repeat: no-repeat;\" data-macro-name=\"note\" data-macro-schema-version=\"1\" data-macro-body-type=\"RICH_TEXT\" data-macro-id=\"aa1f3166-0644-4546-b0e3-0cf62607bcdb\"><tbody><tr><td class=\"wysiwyg-macro-body\"><p>本页面为脚本自动上传，额外修改将有被覆盖风险。</p></td></tr></tbody></table><p class=\"auto-cursor-target\"><br /></p><table class=\"wysiwyg-macro\" style=\"background-image: url('http://wiki.dds-sysu.tech/plugins/servlet/confluence/placeholder/macro-heading?definition=e21hcmtkb3dufQ&amp;locale=en_US&amp;version=2'); background-repeat: no-repeat;\" data-macro-name=\"markdown\" data-macro-schema-version=\"1\" data-macro-body-type=\"PLAIN_TEXT\" data-macro-id=\"29063946-553e-4373-a400-b4dae28334b7\"><tbody><tr><td class=\"wysiwyg-macro-body\"><pre>{markdown}</pre></td></tr></tbody></table><p class=\"auto-cursor-target\"><br /></p>"
        return content

    def read(self, fn):
        # with open(os.path.join(sync_folder, fn), "r") as f:
        with open(fn, "r") as f:
            markdown = f.read()
        self.content = self.gen_content(markdown)
        page_id = re.findall("confluence:[ ]*(\d+)", markdown)
        if len(page_id) == 0:
            print("No confluence page id")
            return False
        self.current_page_id = page_id[0]
        self.title = fn.split("/")[-1].replace(".md", "")
        print(self.title)
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
                    "content": {"id": self.current_page_id}
                }
            },
            "id": self.current_page_id,
            "type": "page",
            "version": {
                "number": self.version,
                "message": "",
                "minorEdit": False,
            },
        }
        # print(payload)
        return payload

    def update_page(self):
        response = requests.put(
            f"http://wiki.dds-sysu.tech/rest/api/content/{self.current_page_id}",
            headers=headers,
            json=self.gen_payload()
        )
        if response.status_code == 200:
            return True
        elif response.status_code == 409:
            try:
                current_version = re.findall(
                    r'Current version is: (\d+)', json.loads(response.text)['message'])[0]
                # print("current version:", current_version)
                self.version = int(current_version) + 1
                self.try_num += 1
                if self.try_num < TRY_MAX:
                    # print("try again", self.version)
                    # time.sleep(15)
                    return self.update_page()
                else:
                    print("fail too many times, exit.")
                    return False
            except Exception as e:
                print(e)
                return False
        print(response.status_code)
        print(response.text)
        return False
