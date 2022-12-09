import re
import getpass

USER = "ben"

sync_folders = [""]

cookie = ""

BASE_URL = ""

TRY_MAX = 3

# Get Cookies (cookies.py+-)
cookies_path = f"/Users/{getpass.getuser()}/Library/Application Support/Microsoft Edge/Default/Cookies"
host_key = re.sub(r'https?://', '', BASE_URL)