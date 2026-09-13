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