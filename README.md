aioircd
=======

A python asynchronous IRC server built on top of
[Trio](https://github.com/python-trio/trio).

### Installation and Usage

Download and install the latest stable version using pip.
Windows users might replace `python3` by `py`.
```bash
python3 -m pip install aioircd
```

Then run the server:
```bash
HOST=0.0.0.0 LOGLEVEL=INFO python3 -m aioircd
```
If you are using powershell you can use the following command:
```powershell
$env:HOST="0.0.0.0"
$env:LOGLEVEL="INFO"
python -m aioircd
```

The configuration is done via environment variables, see `--help`:

    optional arguments:
      -h, --help     show this help message and exit
      -V, --version  show program's version number and exit

    environment variables:
      HOST           public domain name (default: julien-UX410UAR)
      ADDR           ip address to bind (default: 127.0.1.1)
      PORT           port to bind (default: 6667)
      PASS           server password (default: )
      TIMEOUT        kick inactive users after x seconds (default: 60)
      PING_TIMEOUT   PING inactive users x seconds before timeout (default: 5)
      LOGLEVEL       logging verbosity (default: WARNING)
