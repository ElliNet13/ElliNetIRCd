ElliNetIRCd
=======

A python asynchronous IRC server based on aioirc.

### Installation and Usage

Download and install the latest stable version using pip.
```bash
python -m pip install ellinetircd
```

Then run the server:
```bash
HOST=0.0.0.0 LOGLEVEL=INFO python -m ellinetircd
```
If you are using powershell you can use the following command:
```powershell
$env:HOST="0.0.0.0"
$env:LOGLEVEL="INFO"
python -m ellinetircd
```

For other env vars check `python -m ellinetircd --help`.

## Plugins
As of v1.1.0 there is now support for plugins!
Check the test plugins for example plugins.

### Supported plugin types
These are all supported plugins, if it is checked then it has been fully added, if its not checked it is still in dev.
- [ ] Language support plugins (LANGUAGE)
- [x] Command plugins (COMMAND)
