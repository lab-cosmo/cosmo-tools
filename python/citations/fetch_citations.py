#!/usr/bin/python3

import scholarly
import json
import sys
import argparse

def fetch_citations(author, filesave="citations.json"):
    print("Looking up "+author)
    search=scholarly.search_author(author)    
    author=next(search).fill()
    publications = []

    for i, pub in enumerate(author.publications):
        if "year" in pub.bib:
            pubyear = pub.bib["year"]  # often this gets messed up upon .fill()
            pub = pub.fill()
            pub.bib["year"] = pubyear
        else:
            pub = pub.fill()
            if not "year" in pub.bib: 
                # skip publications that really don't have a year, 
                # they probably are crap that was picked up by the search robot
                continue
        print("Fetching: "+str(i)+"/"+str(len(author.publications))+": "+pub.bib["title"]+" ("+str(pub.bib["year"])+")")
        pub.bib.pop("abstract", None)
        dpub = pub.__dict__
    #cites = []
    #for c in pub.get_citedby():
    #    c.fill()
    #    c.bib.pop("abstract",None)
    #    cites.append(c.__dict__)
    #    print("   Cited by ", c.bib["title"])
    #dpub["citing"] = cites
        publications.append(dpub)
    f = open(filesave,"w")
    f.write(json.dumps(publications))
    f.close()


description="""
Usage: 
    python fetch_citations.py "author name" > data.json
    
    Looks up citation data for the selected author on Google Scholar,
    returning a JSON string on stdout containing all of the info. 
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("author", type=str, help="Name of the author to look up.")
    parser.add_argument("-o", "--output", type=str, default="citations.json", help="Filename to store the citation JSON.")
    args = parser.parse_args()
    fetch_citations(args.author, args.output )

