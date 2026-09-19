ElliNetIRCd
=======

A python asynchronous IRC server based on aioirc.

### Installation and Usage

This is a shortened version of the [a page from the Wiki](https://github.com/ElliNet13/ElliNetIRCd/wiki/setup-first-server). Please see the Wiki if this is your first time installing this server.

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

## More info
Check out the [wiki](https://github.com/ElliNet13/ellinetircd/wiki)

## Start testing server

### Powershell
```powershell
$env:HOST="0.0.0.0"
$env:LOGLEVEL="DEBUG"
python -m ellinetircd
```

### Bash
```bash
export HOST="0.0.0.0"
export LOGLEVEL="DEBUG"
python -m ellinetircd
```