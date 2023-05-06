import re, os
import getpass
import json

USER = "ben"

sync_folders = [""]

cookie_cache_fn = 'cache/cookies.json'
if os.path.exists(cookie_cache_fn):
    print("use cache")
    with open(cookie_cache_fn, 'r') as f:
        cookie_dict = json.load(f)
        cookie = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
else:
    cookie = ''

BASE_URL = ""

TRY_MAX = 3

# Get Cookies (cookies.py+-)
cookies_path = f"/Users/{getpass.getuser()}/Library/Application Support/Microsoft Edge/Default/Cookies"
host_key = re.sub(r'https?://', '', BASE_URL)