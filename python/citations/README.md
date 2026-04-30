Citation analysis tools based on scholarly
==========================================

The package is composed of a script that uses scholarly to download citation
data from Google scholar, and of a Jupyer nb making plots from those.

Usage:
```
fetch_citations.py "Author Name" -o citation_data.json
```

The output file doubles as a resume file: rerunning with the same `-o`
continues from where the previous run left off (a warning is printed).
Delete the file to start fresh.

Routing through Tor (`--tor`)
-----------------------------

Google Scholar throttles aggressively per IP. Passing `--tor` makes
scholarly route every request through a private Tor instance, refreshing
the circuit on each retry so a single blocked exit doesn't stall the run:

```
fetch_citations.py "Author Name" -o citation_data.json --tor
```

Setup (one-time):

1. Install the `tor` daemon:
   ```
   sudo apt install tor          # Debian / Ubuntu
   sudo dnf install tor          # Fedora
   brew install tor              # macOS
   ```
   `tor` must be reachable on the `PATH`. Pass `--tor-cmd /path/to/tor`
   if it lives somewhere unusual.

2. Install the two Python dependencies that aren't part of vanilla
   `scholarly`:
   ```
   pip install stem 'httpx[socks]'
   ```
   `stem` lets the script drive Tor's control port (for circuit refresh);
   `httpx[socks]` pulls in `socksio` so HTTPS requests can actually go
   through Tor's SOCKS5 listener.

`fetch_citations.py` launches its own Tor process on a random port — no
need to run a system-wide tor service. Startup adds ~5–30 s while the
circuit bootstraps.

Note: a fraction of Tor exits are blocked by Google and return a sign-in
page that scholarly's parser can't read; the script logs these and moves
on. Re-running picks up any papers that didn't fill on the previous pass.
