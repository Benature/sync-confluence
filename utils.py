import platform
import requests
import os
import re
import json
from bs4 import BeautifulSoup as BS
from bs4.element import NavigableString

root_path = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(os.path.join(root_path, 'config.py')):
    import shutil
    shutil.copyfile(os.path.join(root_path, 'config_sample.py'),
                    os.path.join(root_path, 'config.py'))
if True:
    from config import *

replace_items = {
    "<": "&lt;",
    ">": "&gt;",
    "\n": "  \n",
}

headers = {'Cookie': cookie, 'Content-Type': 'application/json'}


def find_all_files(base):
    for root, ds, fs in os.walk(base):
        for f in fs:
            if f.lower().endswith('.md'):
                fullname = os.path.join(root, f)
                yield fullname


def find_all_files_with_tag(base, tag):
    tag = tag.lstrip("#")
    for root, ds, fs in os.walk(base):
        for f in fs:
            if f.lower().endswith('.md'):
                fullname = os.path.join(root, f)
                with open(fullname, "r") as f:
                    content = f.read()
                if len(
                        re.findall(r"tags:.*[\s:,]{0}|\s#{0}".format(tag),
                                   content)) > 0:
                    yield fullname


def wiki2link(m):
    title = m.group(1)
    alias = title
    heading = ""

    if "|" in title:
        title, alias = title.split("|")
        title = title.rstrip("\\")

    if "#" in title:
        title, heading = title.split("#")

    link = f"[{alias}]({BASE_URL}/display/~{USER}/{title})"

    if heading != "":
        link = link[:-1] + f"#{heading})"
    return link


def md_meta(m):
    meta = m.group(1)
    return meta.replace("\n", "\n> ") + "\n"


def upper_content(m):
    '''^[upper content]'''

    def func(match):
        return "^^" + match.group(0)[2:-1] + "^^"

    content = m.group(0)
    content = re.sub(
        r"\^\[(?:[^\[]*?\[[^\[\]]+?\]\(.*?\).*?)*?\]|(?!\^)\^\[.*?\]", func,
        content)
    return content


def get_page_id(string, force=False):
    try:
        return re.findall(r"[?&]pageId=(\d+)", string)[0]
    except IndexError:
        if force:
            response = requests.get(f"{BASE_URL}/display/~wbenature/" +
                                    string.split('/')[-1],
                                    headers=headers)
            soup = BS(response.text, "lxml")
            return get_page_id(soup.select("#editPageLink")[0]['href'])
        else:
            return None


class Tree():

    def __init__(self):
        self.tree = []
        self.pages = {}

        self.base_id = self._get_base_id()

    def _get_base_id(self):
        json_path = os.path.join(root_path, f"cache/{USER}.json")
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            base_id = data['base_page_id']
        except:
            responce = requests.get(
                f"{BASE_URL}/spaces/viewspace.action?key=~{USER}",
                headers=headers)
            soup = BS(responce.text, "lxml")
            soup.select('.name')[0].next_element
            base_id = get_page_id(soup.select('.name')[0].next_element['href'],
                                  force=True)
        return base_id

    def _get_children(self):
        depth = 99
        naturalchildren_url = f"{BASE_URL}/plugins/pagetree/naturalchildren.action?&sort=position&reverse=false&disableLinks=false&expandCurrent=true&placement=sidebar&hasRoot=true&pageId={self.base_id}&treeId=0&startDepth={depth}"
        responce = requests.get(naturalchildren_url, headers=headers)
        soup = BS(responce.text, "lxml")
        return soup

    def spider(self, sub_tree=None, pointer=None, prefix=[]):
        if sub_tree is None:
            sub_tree = self.tree
        if pointer is None:
            soup = self._get_children()
            pointer = soup.body.ul.li

        while pointer is not None:
            has_children = len(
                pointer.select('.plugin_pagetree_childtoggle_container')
                [0].select(".no-children")) == 0
            a = pointer.select('.plugin_pagetree_children_span')[0].select(
                'a')[0]
            title = a.text
            page_id = get_page_id(a['href'], force=False)
            sub_tree.append(dict(title=title, children=[]))
            self.pages[title] = dict(page_id=page_id, prefix=prefix)
            if has_children:
                self.spider(sub_tree[-1]['children'],
                            pointer=pointer.ul.li,
                            prefix=prefix + [title])
            # break
            while True:
                pointer = pointer.next_sibling
                if not isinstance(pointer, NavigableString):
                    break

    def save(self):
        cache_folder = os.path.join(root_path, "cache")
        if not os.path.exists(cache_folder):
            os.mkdir(cache_folder)
        with open(os.path.join(cache_folder, f"{USER}.json"), "w") as f:
            json.dump(dict(
                base_page_id=self.base_id,
                pages=self.pages,
                tree=self.tree,
            ),
                      f,
                      ensure_ascii=False)


def notify(
        title,
        message,
        subtitle='',
        sound='Hero',
        open='https://flomoapp.com/',
        method='',
        activate='',
        icon='https://i.loli.net/2020/12/06/inPGAIkvbyK7SNJ.png',
        contentImage='https://raw.githubusercontent.com/Benature/WordReview/ben/WordReview/static/media/muyi.png',
        sender='com.apple.automator.Confluence',
        terminal_notifier_path='terminal-notifier'):
    sysstr = platform.system()

    if sysstr == 'Darwin':  # macOS
        # print('macOS notification')
        if method == 'terminal-notifier':
            '''https://github.com/julienXX/terminal-notifier'''

            t = f'-title "{title}"'
            m = f'-message "{message}"'

            s = f'-subtitle "{subtitle}"'
            icon = f'-appIcon "{icon}"'
            sound = f'-sound "{sound}"'
            sender = f'-sender "{sender}"'
            contentImage = f'-contentImage "{contentImage}"'

            activate = '' if activate == '' else f'-activate "{activate}"'
            open = '' if open == '' else f'-open "{open}"'

            cmd = '{} {} '.format(
                terminal_notifier_path, ' '.join([
                    m, t, s, icon, activate, open, sound, sender, contentImage
                ]))
            os.system(cmd)
        else:
            os.system(
                f"""osascript -e 'display notification "{message}" with title "{title}"'"""
            )
    elif sysstr == "Windows":
        print('TODO: windows notification')
    elif sysstr == "Linux":
        print('TODO: Linux notification')
