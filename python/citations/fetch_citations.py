#!/usr/bin/env python3
"""
A command-line utility and mini-library, based on scholarly, to get bibliometric data from an author 
on Google Scholar, and to process them to extract indices and/or coauthor data.

Author: Michele Ceriotti 2019
License: LGPL
"""

from scholarly import scholarly
import json
import re
import time
from datetime import datetime
import numpy as np
import sys
import argparse

scholarly.set_logger(True)

def fetch_citations(author, filesave="citations.json", search_by_id=False, 
                    proxy="",  proxy_list="", delay=0.0, restart=""):
    """ Fetch citations from google scholar using scholarly """

    if proxy != "":
        print("Setting up proxy ", proxy)
        scholarly.use_proxy(scholarly.SingleProxy(http=proxy, https=proxy))
    if proxy_list != "":
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

    if restart == "":
        if search_by_id:
            try:
                search =  scholarly.search_author_id(author)
            except AttributeError:
                raise ValueError(f"Could not find author ID {author}")
            author = scholarly.fill(search)
        else:
            print("Looking up "+author)
            search = scholarly.search_author(author)    
            author = scholarly.fill(next(search))
        source_publications = author['publications'];
    else:
        with open(restart, 'r') as file:
            source_publications = json.load(file)

        
    publications = []

    for i, pub in enumerate(source_publications):
        cites = pub['num_citations']       # often this gets messed up upon .fill()
        if not pub['filled']:
            try:
                if "pub_year" in pub['bib']:
                    pubyear = pub['bib']["pub_year"]  # also this gets messed up upon .fill()
                    pub = scholarly.fill(pub)
                    pub['bib']["pub_year"] = pubyear
                else:
                    pub = scholarly.fill(pub)
            except:
                print(f"Failed to download extended data for publication {pub['bib']['title']}")

        pub['num_citations'] = cites
        if not "pub_year" in pub['bib']: 
            # skip publications that really don't have a year, 
            # they probably are crap that was picked up by the search robot
            continue
                    
        print("Fetched: "+str(i+1)+"/"+str(len(source_publications))+": "+pub['bib']["title"]+" ("+str(pub['bib']["pub_year"])+")")
        pub['bib'].pop("abstract", None)
        publications.append(pub)
        
        time.sleep(delay)
        
    f = open(filesave,"w")
    f.write(json.dumps(publications))
    f.close()

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
    parser.add_argument("--delay", type=float, default=0.0, help="Add the specified delay, in seconds, between publication reads, to reduce chance of ban.")
    parser.add_argument("--proxy", type=str, default="", help="Address of a proxy.")
    parser.add_argument("--restart", type=str, default="", help="Restart filling a json file.")
    parser.add_argument("--proxy-list", type=str, default="", help="Filename containing a list of proxy, one item per line, with format url (including port, e.g. 127.0.0.1:80)")    
    args = parser.parse_args()
    fetch_citations(args.author, args.output, args.id, args.proxy, args.proxy_list, args.delay, args.restart )

