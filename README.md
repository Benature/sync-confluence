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
- [ ] support local images
- [x] only sync files with specific tag
- [x] auto create new page
- [x] check whether the page is modified before update, if not, jump this page.


## More

Install [terminal-notifier](https://github.com/julienXX/terminal-notifier)

```shell
brew install terminal-notifier
```

To specific the icon, refer to <https://github.com/julienXX/terminal-notifier/issues/131#issuecomment-213752559>.