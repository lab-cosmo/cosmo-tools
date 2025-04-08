#!/usr/bin/env python3
 
"""
Example usage:
    python biblio_overview.py --file names.txt --num-pubs 5

Where `names.txt` contains one researcher name per line.

Requires:
    pip install scholarly
"""

import sys
import datetime
import argparse
from scholarly import scholarly

def parse_args():
    parser = argparse.ArgumentParser(description="Query Google Scholar for a list of researchers.")
    parser.add_argument(
        '-f', '--file',
        type=str,
        required=True,
        help="Path to the file containing researcher names (one name per line)."
    )
    parser.add_argument(
        '-n', '--num-pubs',
        type=int,
        default=3,
        help="Number of top publications to fetch and print."
    )
    return parser.parse_args()

def disambiguate_author(name):
    """
    Search for authors by name. If multiple are found, print them to stderr and
    ask the user to pick one. Return the chosen author (as a dictionary) or None
    if no valid choice or no authors are found.
    """
    # Get an iterator of author results
    search_results = scholarly.search_author(name)
    
    # Gather up to, say, 10 possible matches (to avoid infinite loops if many matches)
    # You can adjust this limit as needed.
    possible_authors = []
    for _ in range(25):
        try:
            author = next(search_results)
            possible_authors.append(author)
        except StopIteration:
            break

    # If no authors found, return None
    if not possible_authors:
        return None

    # If exactly one author found, just return that
    if len(possible_authors) == 1:
        print(f"\nI found one author for the name '{name}'\n", file=sys.stderr)
        return possible_authors[0]

    # Otherwise, we have multiple authors -> disambiguate
    print(f"\nI found {len(possible_authors)} authors for the name '{name}':\n", file=sys.stderr)
    
    # Print the options to stderr
    for idx, author in enumerate(possible_authors, start=1):
        # Partially fill the author to get affiliation, citations, and interests
        # 'basics' -> name, affiliation, interests
        # 'indices' -> h-index, total citations, i10-index, etc.
        partial_filled = scholarly.fill(author, sections=["basics", "indices"])
        
        auth_name = partial_filled.get("name", "Unknown Name")
        affiliation = partial_filled.get("affiliation", "No Affiliation")
        citations = partial_filled.get("citedby", 0)
        interests = partial_filled.get("interests", [])
        if interests:
            interests_str = ", ".join(interests)
        else:
            interests_str = "No listed interests"
        
        print(
            f"{idx}. {auth_name}, {affiliation}, "
            f"Interests: {interests_str}, Citations: {citations}",
            file=sys.stderr
        )

    # Ask the user to choose
    while True:
        try:
            print(f"\nChoose one (1-{len(possible_authors)}), or 0 to skip: ", file=sys.stderr, end="")
            choice_str = input("")
            choice = int(choice_str)
        except ValueError:
            choice = -1  # invalid integer

        if choice == 0:
            # user wants to skip
            return None
        if 1 <= choice <= len(possible_authors):
            # valid choice
            return possible_authors[choice - 1]
        else:
            print("Invalid choice, please try again.", file=sys.stderr)

def get_researcher_data(name, max_publications=3):
    """
    Given a researcher's name, interactively disambiguate if needed, then returns a dict with:
      - 'name': Researcher name
      - 'affiliation': Their listed affiliation
      - 'total_citations': Overall citation count
      - 'h_index': h-index from Google Scholar
      - 'citations_last_5_years': a dict of year->cites for the last 5 years
      - 'publications': A list of the top publications (by citation count).
        Each publication is itself a dict with:
            - 'title'
            - 'authors'
            - 'journal'
            - 'year'
            - 'num_citations'
    If no author is found or the user skips, returns None.
    """
    chosen_author = disambiguate_author(name)
    if chosen_author is None:
        return None
    
    # Fill in the details for the chosen author
    author_full = scholarly.fill(chosen_author, sections=["basics", "indices", "publications", "counts"])
    
    # Basic metadata
    author_name = author_full.get('name', 'Unknown')
    affiliation = author_full.get('affiliation', 'Unknown')
    
    # Citation metrics
    total_citations = author_full.get('citedby', 0)
    h_index = author_full.get('hindex', 0)
    
    # Citations over the last 5 years
    cites_per_year = author_full.get('cites_per_year', {})
    current_year = datetime.datetime.now().year
    last_5_years = range(current_year - 4, current_year + 1)  # e.g. 2021..2025 if current_year=2025
    citations_last_5 = {y: cites_per_year.get(y, 0) for y in last_5_years}

    # Retrieve (already present in author_full['publications'])
    # Each pub is a dict with keys like 'num_citations', 'bib' (title, author, venue, pub_year, etc.)
    pubs_filled = []
    for pub in author_full.get('publications', []):
        filled_pub = scholarly.fill(pub)  # get full bibliographic data
        bib = filled_pub.get('bib', {})
        
        title = bib.get('title', 'No title')
        authors = bib.get('author', 'No authors')
        # 'venue' vs 'journal' in `scholarly`
        # Some older versions of scholarly used 'venue'. 
        # Some references might store it in 'journal' or 'venue'.
        journal = bib.get('journal', bib.get('venue', 'No journal'))
        year = bib.get('pub_year', 'No year')
        num_citations = filled_pub.get('num_citations', 0)
        
        pubs_filled.append({
            'title': title,
            'authors': authors,
            'journal': journal,
            'year': year,
            'num_citations': num_citations
        })

        # If we already have enough, we can consider breaking early
        # But note that we still sort later. Alternatively, remove if you rely purely on sorting:
        if len(pubs_filled) > max_publications + 4:
            # Just a buffer so we can do some sorting
            break
    
    # Sort publications by citation count, descending
    pubs_sorted = sorted(pubs_filled, key=lambda x: x['num_citations'], reverse=True)
    
    # Take the top N
    top_publications = pubs_sorted[:max_publications]
    
    return {
        'name': author_name,
        'affiliation': affiliation,
        'total_citations': total_citations,
        'h_index': h_index,
        'citations_last_5_years': citations_last_5,
        'publications': top_publications
    }

if __name__ == "__main__":
    args = parse_args()

    # Read researcher names from the specified file
    try:
        with open(args.file, 'r', encoding='utf-8') as infile:
            names = [line.strip() for line in infile if line.strip()]
    except FileNotFoundError:
        print(f"Error: Could not find file '{args.file}'", file=sys.stderr)
        sys.exit(1)

    for name in names:
        result = get_researcher_data(name, max_publications=args.num_pubs)
        if not result:
            print(f"No valid Google Scholar profile selected for '{name}'.\n")
            continue

        # Print the data in Markdown style
        print(f"""\
Researcher: {result['name']}
=====================================
- **Affiliation:** {result['affiliation']}
- **Total Cites:** {result['total_citations']}
- **h-index:** {result['h_index']}
- **5-year Cites:** {result['citations_last_5_years']}

Top {args.num_pubs} Publications by Citation Count
------------------------------------
""")

        for i, pub in enumerate(result['publications'], start=1):
            print(f"""\
{i}. **Title:** {pub['title']}
   - **Authors:** {pub['authors']}
   - **Journal/Venue:** {pub['journal']}
   - **Year:** {pub['year']}
   - **Citations:** {pub['num_citations']}

""")

        print("---\n")

