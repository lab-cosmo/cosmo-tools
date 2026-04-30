#!/usr/bin/env python3
"""
A command-line utility and mini-library, based on scholarly, to get bibliometric data from an author 
on Google Scholar, and to process them to extract indices and/or coauthor data.

Author: Michele Ceriotti 2019
License: LGPL
"""

from scholarly import scholarly, ProxyGenerator
import json
import logging
import os
import random
import re
import shutil
import time
from datetime import datetime
import numpy as np
import sys
import argparse

scholarly.set_logger(True)

# Without a handler attached, scholarly's INFO logs vanish — which makes the
# script look hung when it's actually retrying through 429s. Send them to
# stderr so the user sees progress.
_root = logging.getLogger()
if not _root.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s",
                                      datefmt="%H:%M:%S"))
    _root.addHandler(_h)
    _root.setLevel(logging.INFO)
# httpx is very chatty; mute its per-request log line.
logging.getLogger("httpx").setLevel(logging.WARNING)


def _patch_scholarly_socks_bug():
    """scholarly's ProxyGenerator._use_proxy unconditionally prepends 'http://'
    to any proxy URL that doesn't begin with 'http', mangling
    'socks5://127.0.0.1:9050' into 'http://socks5://127.0.0.1:9050'. httpx then
    tries to DNS-resolve a host literally called 'socks5' and we get
    'Temporary failure in name resolution' on every request. Replace the
    method with one that respects existing schemes. Idempotent.
    """
    import requests
    from scholarly._proxy_generator import ProxyGenerator, ProxyMode
    if getattr(ProxyGenerator, "_socks_scheme_patched", False):
        return

    def fixed_use_proxy(self, http, https=None):
        if http and "://" not in http:
            http = "http://" + http
        if https is None:
            https = http
        elif https and "://" not in https:
            https = "https://" + https

        proxies = {'http://': http, 'https://': https}
        if self.proxy_mode == ProxyMode.SCRAPERAPI:
            r = requests.get("http://api.scraperapi.com/account",
                             params={'api_key': self._API_KEY}).json()
            if "error" in r:
                self.logger.warning(r["error"])
                self._proxy_works = False
            else:
                self._proxy_works = r["requestCount"] < int(r["requestLimit"])
        else:
            self._proxy_works = self._check_proxy(proxies)

        if self._proxy_works:
            self._proxies = proxies
            self._new_session(proxies=proxies)
        return self._proxy_works

    ProxyGenerator._use_proxy = fixed_use_proxy
    ProxyGenerator._socks_scheme_patched = True


def _setup_tor(tor_cmd):
    """Configure scholarly to route all Scholar traffic through a private Tor
    instance. Returns True on success, False (with a printed reason) otherwise.
    """
    missing = []
    try:
        import stem  # noqa: F401
    except ImportError:
        missing.append("stem")
    try:
        import socksio  # noqa: F401
    except ImportError:
        missing.append("socksio")
    if missing:
        print("Tor requires extra Python packages that are not installed: "
              + ", ".join(missing))
        print(f"  Install with: pip install {' '.join(missing)}"
              + ("  # or: pip install httpx[socks] stem" if "socksio" in missing else ""))
        return False
    if not shutil.which(tor_cmd):
        print(f"Cannot find the 'tor' binary (looked for {tor_cmd!r}). "
              "Install it (e.g. apt install tor) or pass --tor-cmd /path/to/tor.")
        return False
    _patch_scholarly_socks_bug()
    resolved = shutil.which(tor_cmd) or tor_cmd
    print(f"Starting Tor via {resolved} (this takes ~5-30 s) ...")
    try:
        pg = ProxyGenerator()
        info = pg.Tor_Internal(tor_cmd=resolved)
    except Exception as e:
        print(f"Tor setup failed: {type(e).__name__}: {e}")
        return False
    if not info.get("proxy_works"):
        print(f"Tor proxy did not come up cleanly: {info}")
        return False
    print(f"Tor up: socks={info['tor_sock_port']} control={info['tor_control_port']} "
          f"refresh={'yes' if info.get('refresh_works') else 'no'}")
    # Use Tor for BOTH primary and secondary proxy slots, otherwise scholarly
    # falls back to FreeProxies for /citations URLs (which Google blocks
    # anyway), defeating the point.
    scholarly.use_proxy(pg, pg)
    return True


def _atomic_save_json(path, data):
    """Write JSON via temp+rename so a crash mid-write can't corrupt the file."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def fetch_citations(author, filesave="citations.json", search_by_id=False,
                    proxy="",  proxy_list="", delay=5.0,
                    use_tor=False, tor_cmd="tor"):
    """ Fetch citations from google scholar using scholarly.

    The output file (``filesave``) doubles as the resume point: if it already
    exists, the publication list is loaded from it and any entries already
    marked ``filled`` are skipped. Each successful fill is written back to
    the same file, so a crash or Ctrl-C never loses more than the paper
    currently in flight. Delete the file to start a fresh run.
    """

    if use_tor:
        if not _setup_tor(tor_cmd):
            raise RuntimeError("Could not initialise Tor. Aborting.")
    elif proxy != "":
        print("Setting up proxy ", proxy)
        scholarly.use_proxy(scholarly.SingleProxy(http=proxy, https=proxy))
    elif proxy_list != "":
        lproxies = open(proxy_list, 'r').readlines()
        def proxy_gen():
            if proxy_gen.counter >= len(lproxies):
                raise IndexError("We ran out of proxies...")
            proxy = lproxies[proxy_gen.counter]
            if not proxy.startswith("http"):
                proxy = "http://"+proxy
            proxy_gen.counter += 1
            return proxy
        proxy_gen.counter = 0
        scholarly.use_proxy(proxy_gen)

    # Give the navigator a larger per-request budget. With Tor, each inner
    # retry refreshes the circuit, so allow more attempts per request.
    scholarly.set_retries(20 if use_tor else 10)

    if os.path.exists(filesave):
        print(f"WARNING: '{filesave}' already exists; resuming from it. "
              f"Delete the file to start a fresh run.")
        with open(filesave, 'r') as f:
            source_publications = json.load(f)
    else:
        if search_by_id:
            try:
                search = scholarly.search_author_id(author)
            except AttributeError:
                raise ValueError(f"Could not find author ID {author}")
            author = scholarly.fill(search)
        else:
            print("Looking up "+author)
            search = scholarly.search_author(author)
            author = scholarly.fill(next(search))
        source_publications = author['publications']

    for i, pub in enumerate(source_publications):
        cites = pub['num_citations']       # often this gets messed up upon .fill()
        if not pub['filled']:
            pubyear = pub['bib'].get("pub_year")  # also this gets messed up upon .fill()
            ok = False
            for attempt in (1, 2):
                try:
                    pub = scholarly.fill(pub)
                    ok = True
                    break
                except Exception as e:
                    title = pub['bib'].get('title', '<untitled>')
                    print(f"  ! attempt {attempt}/2 failed for {title!r}: "
                          f"{type(e).__name__}: {str(e)[:120]}")
            if ok and pubyear is not None:
                pub['bib']["pub_year"] = pubyear
            source_publications[i] = pub
            if not ok:
                # Leave filled=False; a future run can retry this paper.
                continue
            time.sleep(delay * random.uniform(0.7, 1.3))

        pub['num_citations'] = cites
        if "pub_year" not in pub['bib']:
            continue

        print("Fetched: "+str(i+1)+"/"+str(len(source_publications))+": "
              + pub['bib']["title"]+" ("+str(pub['bib']["pub_year"])+")")
        pub['bib'].pop("abstract", None)
        _atomic_save_json(filesave, source_publications)

    # Final flush, in case the run was a no-op (everything already filled).
    _atomic_save_json(filesave, source_publications)

def pubs_clean(pubs, start_year=1900, has_journal=True, has_title=True, 
               journal_blacklist=["arxiv", "chemrxiv", "biorxiv", "bulletin"], 
               no_cites_grace=3, highly_cited_grace=20, clean_citation_record=True
              ):
    """ Cleans up a citation record to remove preprints, ancient publications,
        or miscellaneous probable parsing errors.
    """
    clean = []
    now_year = datetime.now().year
    for v in pubs:
        v["bib"]["pub_year"] = int(v["bib"]["pub_year"])        
        if v["bib"]["pub_year"]<start_year:
            continue
        # make sure we don't drop a decently cited article only because
        # of some formatting quirks
        if "num_citations" in v and v["num_citations"]>=highly_cited_grace:
            clean.append(v) 
            continue
        if has_journal and "journal" not in v["bib"]:
            continue
        if has_title and "title" not in v["bib"]:
            continue
        # drops if the journal name is blacklisted 
        # (e.g. preprints, which I love but are sadly usually not counted)
        if "journal" in v["bib"]:
            for j in journal_blacklist:
                if j in v["bib"]["journal"].lower():
                    continue
        # old articles that collected no citations are either useless or
        # crap picked up by the searchbot
        if (no_cites_grace>=0 and v["bib"]["pub_year"]+no_cites_grace <= now_year and
                len(v["cites_per_year"])==0):
            continue
        if clean_citation_record:
            # removes citations that allegedly appeared before the paper was published,
            # allowing for a 1-year margin to account for preprints
            for y in list(v["cites_per_year"].keys()):
                if int(y)<v["bib"]["pub_year"]-1:
                    v["cites_per_year"].pop(y)
        clean.append(v)
    return clean

def get_authors(pubs, cutoff=-1):
    authors=set()
    for pub in pubs:
        if pub["bib"]["pub_year"]<cutoff:
            continue
        authors.update(set(re.split(r" and |,", pub["bib"]["author"])) )
    authors = list(authors)
    authors.sort()
    return authors

# Performance indicators per year
def cites_per_year(pubs):
    """ Counts total number of citations per year. """
    citesy = {}
    for p in pubs:
        for k, nk in p["cites_per_year"].items():
            k = int(k)
            if k in citesy:
                citesy[k]+=nk
            else:
                citesy[k]=nk
    return citesy

def papers_per_year(pubs):
    """ Counts papers published per year. """
    papersy = {}
    for p in pubs:
        y=p["bib"]["pub_year"]
        if y in papersy:
            papersy[y] += 1
        else:
            papersy[y] = 1
    return papersy

# Performance indicators per paper
def papers_cites(pubs):
    """ Counts total citations per paper """
    pc = np.asarray([(p["num_citations"] if "num_citations" in p else 0) for p in pubs])
    pc[::-1].sort()
    return pc

def papers_cites_years_table(pubs):
    """ Makes a table with the numbers of citations per year
        for all the papers in the publication list. """

    years = []
    paperyc = []
    for p in pubs:
        pcitesy = {}
        for k, nk in p["cites_per_year"].items():
            k = int(k)
            if k in pcitesy:
                pcitesy[k]+=nk
            else:
                pcitesy[k]=nk
        years += list(pcitesy.keys())
        paperyc.append(pcitesy)
    years = list(set(years))
    years.sort()
    ypcites = np.zeros((len(pubs),len(years) ))
    for ip, p in enumerate(paperyc):
        for k,v in p.items():
            ik = years.index(k)
            ypcites[ip, ik] = v
    order = np.argsort(ypcites.sum(axis=1))
    return (np.asarray(years, int), ypcites[order[::-1]].copy(), [pubs[i] for i in order[::-1]])

def h_index(pubs):
    pc = papers_cites(pubs)
    h = 0
    while pc[h]>h:
        h+=1
    return h


description="""
Usage: 
    python fetch_citations.py "author name" -o data.json
    
    Looks up citation data for the selected author on Google Scholar,
    saving to the specified file a JSON string containing all of the info. 
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("author", type=str, help="Name of the author to look up.")
    parser.add_argument("-o", "--output", type=str, default="citations.json", help="Filename to store the citation JSON.")
    parser.add_argument("--id", action='store_true', help="Search for a specific author ID rather than the first matching author name")
    parser.add_argument("--delay", type=float, default=5.0, help="Mean delay, in seconds, between publication reads (jittered +/-30%%), to reduce chance of throttling.")
    parser.add_argument("--proxy", type=str, default="", help="Address of a proxy.")
    parser.add_argument("--proxy-list", type=str, default="", help="Filename containing a list of proxy, one item per line, with format url (including port, e.g. 127.0.0.1:80)")
    parser.add_argument("--tor", action="store_true", help="Route Scholar requests through a private Tor instance (refreshes circuit on each retry to dodge per-IP throttling). Requires the 'tor' binary and the 'stem' Python package -- see README for setup.")
    parser.add_argument("--tor-cmd", type=str, default="tor", help="Path to the tor binary (default: looked up on PATH).")
    args = parser.parse_args()
    fetch_citations(args.author, args.output, args.id, args.proxy, args.proxy_list,
                    args.delay,
                    use_tor=args.tor, tor_cmd=args.tor_cmd)

