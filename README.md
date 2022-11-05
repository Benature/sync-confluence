# sync-confluence

Sync local markdown files to Confluence (server).

Init config file:

```shell
cp config_sample.py config.py
```

Usage:

```shell
python sync.py
```

## TODO
- [x] auto create new page
- [x] check whether the page is modified before update, if not, jump this page.