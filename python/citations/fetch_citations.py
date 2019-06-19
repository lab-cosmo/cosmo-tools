#!/usr/bin/python3

import scholarly
import json
import sys
import argparse

def fetch_citations(author):
    print("Looking up "+author[0])
    search=scholarly.search_author(author[0])    
    author=next(search).fill()
    publications = []

    for i, pub in enumerate(author.publications):
        pubyear = pub.bib["year"]  # often this gets messed up upon .fill()
        pub = pub.fill()
        pub.bib["year"] = pubyear
        print("Fetching: "+str(i)+"/"+str(len(author.publications))+": "+pub.bib["title"]+" ("+str(pub.bib["year"])+")")
        pub.bib.pop("abstract", None)
    #cites = []
    #for c in pub.get_citedby():
    #    c.fill()
    #    c.bib.pop("abstract",None)
    #    cites.append(c.__dict__)
    #    print("   Cited by ", c.bib["title"])
        dpub = pub.__dict__
    #dpub["citing"] = cites
        publications.append(dpub)
    print(json.dumps(publications))


description="""
Usage: 
    python fetch_citations.py "author name" > data.json
    
    Looks up citation data for the selected author on Google Scholar,
    returning a JSON string on stdout containing all of the info. 
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("author", type=str, nargs=1,
                        help="Name of the author to look up.")
    args = parser.parse_args()
    fetch_citations(args.author)

