"""Scrapes interesting things from champion.gg"""

import re

import requests
from anytree import Node
from bs4 import BeautifulSoup


def champion_gg_scraper(champion: str, role: str, matchup: str, verbose: bool) -> Node:
    """Scrapes a build from champion.gg."""
    if role.startswith("m"):
        role = "Middle"

    soup = get_soup(champion, role, matchup)
    role = soup.find("input", class_="sc-gPEVay bYMvhD")["value"]

    if matchup != "":
        title = f"{champion.title()} {role.title()} vs {matchup.title()} from Champion.gg"
    else:
        title = f"{champion.title()} {role.title()} from Champion.gg"

    root = Node(title)

    # Parse the webpage
    # Divide webpage into relevant pieces
    if matchup != "":
        relevant_tags = soup.find_all(class_="Inner-sc-7vmxjm-0 cpZSJT")
        items = relevant_tags[2].contents[0].contents[0]
        runes_webpage = relevant_tags[2].contents[0].contents[1]
    else:
        relevant_tags = soup.find_all(class_="Inner-sc-7vmxjm-0 cpZSJT")
        items = relevant_tags[1].contents[0].contents[0]
        runes_webpage = relevant_tags[1].contents[0].contents[1]

    # Runes and shards
    tree_runes = Node("Runes", root)
    if verbose:
        tree_shards = Node("Shards", root)
    runes = runes_webpage.find_all(champion_gg_runes)
    for entry in runes[:6]:
        Node(entry.contents[0], tree_runes)
    for entry in runes[6:]:
        if verbose:
            Node(entry.contents[0], tree_shards)
        else:
            Node(entry.contents[0], tree_runes)

    # get the build
    build = Node("Build", root)
    if verbose:
        starters = Node("Starter Items", build)
        core = Node("Build Path", build)
        final = Node("Final Build", build)

        # Starting items
        for entry in items.contents[0].find_all("img"):
            if entry.attrs["alt"] != "":
                Node(entry.attrs["alt"], starters)
        # Core build path
        for entry in items.contents[1].find_all("img"):
            Node(entry.attrs["alt"], core)

    # Final build
    for entry in items.contents[2].find_all("img"):
        if verbose:
            Node(entry.attrs["alt"], final)
        else:
            Node(entry.attrs["alt"], build)

    # get skills
    skills = Node("Skill Priority", parent=root)
    selector = "typography__Caption-sc-1mpsx83-11 typography__CaptionBold-sc-1mpsx83-12 dwtPBh"
    # the first is 'Passive' and the rest are redundant
    results = soup.find_all("p", class_=selector)[1:4]
    for entry in results:
        Node(entry.text, parent=skills)

    # Summoner Spells
    summoners = Node("Summoner Spells", parent=root)
    spells = list(set(re.findall(r"Summoner(.*).png", str(items.find_all(class_="sc-fONwsr bsxfkk")))))
    for cycle, entry in enumerate(spells):
        # Ignite is referred to as Dot
        if entry == "Dot":
            Node("Ignite", summoners)
            spells[cycle] = "Ignite"
        else:
            Node(entry, summoners)

    return root


def champion_gg_runes(tag):
    """Filter function that returns true for tags with the names of Runes in Champion.gg"""
    if "class" in tag.attrs:
        match = "ChampionRuneSmallCHGG__RuneName-sc-1vubct9-5"
        if match in tag.attrs["class"] and not re.compile("sc-").search(tag.attrs["class"][1]):
            return tag


def get_soup(champion: str, role: str, matchup: str) -> BeautifulSoup:
    """Returns a BeautifulSoup of Champion.gg HTML for the passed args."""
    if matchup != "":
        url = f"https://champion.gg/champion/{champion}/{role}/overview/{matchup}"
    else:
        url = f"https://champion.gg/champion/{champion}/{role}/"
    page = requests.get(url)
    return BeautifulSoup(page.content, "html.parser")
