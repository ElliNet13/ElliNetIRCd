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
As of v1.2.0 there is now support for other languages then python!
Check the test plugins for example plugins.

### Supported plugin types
These are all supported plugins, if it is checked then it has been fully added, if its not checked it is still in dev.
- [x] Language support plugins (LANGUAGE) [As of v1.2.0]
- [x] Command plugins (COMMAND) [As of v1.1.0]

### Supported plugin languages
These are all supported plugins languages, if it is checked then it has been fully added, if its not checked it is still in dev.
- [x] Python [As of v1.1.0]
- [x] Lua [As of v1.2.0]

### Plugin search paths
- ./plugins
- ellinetircd.core_plugins
- ellinetircd.test_plugins (if logging is set to debug)
