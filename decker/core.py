import json
import csv
import operator as o
from PIL import Image
import itertools as it
from collections import defaultdict


# Some editions are reserved keywords in windows
EDDEX = {"con": "con_"}


def read_deck(deck_file):
    """
    reads a csv deck file and returns a list of (edition, name, count) tuples
    """
    acc = []
    with open(deck_file, "r") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            row["count"] = int(row["count"])
            acc.append(row)
    return acc


def deck_editions(deck):
    """
    given a deck, returns a set of editions that it uses
    """
    return set([deckline["edition"] for deckline in deck])


def read_pngdex(path, editions):
    """
    loads a list of editions into an index of {(edition, name): [pngid]}
    """
    acc = {}
    for edition in editions:
        acc[edition] = defaultdict(list)
        edfile = EDDEX[edition] if edition in EDDEX else edition
        with open("{}/{}.json".format(path, edfile), "r") as fp:
            for line in fp.readlines():
                data = json.loads(line)
                offset = data["collector_number"] - 1
                page = offset // 100
                row = (offset % 100) // 10
                column = offset % 10
                acc[edition][data["name"]].append((edition, page, row, column))
    return acc


def check_deck(pngdex, deck):
    """
    returns a list of missing card names, if none are missing
    returns an empty list
    """
    acc = []
    for deckline in deck:
        if deckline["edition"] not in pngdex or\
           deckline["name"] not in pngdex[deckline["edition"]]:
            acc.append(deckline)
    return acc


def deck_to_pngids(pngdex, deck):
    """
    Returns a list of sheet coordinates for the passed deck.

    If multiple copies of a card are needed, and multiple versions of that card
    exist, cycle through the different versions
    """
    acc = []
    for deckline in deck:
        name_pngids = pngdex[deckline["edition"]][deckline["name"]]
        deckline_pngids = it.islice(it.cycle(name_pngids), deckline["count"])
        acc.extend(deckline_pngids)
    return acc


def render_pngids(path, pngids):
    """
    returns a list of Images corresponding to the passed pngids
    """
    acc = {}
    for ((edition, page), grouped) in it.groupby(set(pngids), o.itemgetter(0, 1)):
        edfile = EDDEX[edition] if edition in EDDEX else edition
        sheet = Image.open("{}/{}_{:03d}.png".format(path, edfile, page))
        for pngid in grouped:
            width = sheet.size[0]/10
            height = sheet.size[1]/10
            row = height * pngid[2]
            column = width * pngid[3]
            box = (column, row, column+width, row+height)
            acc[pngid] = sheet.crop(box)

    return [acc[pngid] for pngid in pngids]


def read_codex(codex_file):
    """
    reads a csv codex file and returns a list of codex
    tuples sorted newest to oldest
    """
    acc = []
    with open(codex_file, "r") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            acc.append(row)
    return acc


def _read_editions(codex, newest, oldest, ignore):
    """
    helper function for `read_cardex`
    returns a list of relevant editions given constraints
    """
    newest_flag = newest is None
    oldest_flag = False

    acc = []
    for row in codex:
        edition = row["edition"]

        if newest == edition:
            newest_flag = True

        if newest_flag and\
           not oldest_flag and\
           row["edition"] not in ignore:
            acc.append(edition)

        if oldest == edition:
            oldest_flag = True

    return acc


def read_cardex(path, codex, newest=None, oldest=None, ignore=set()):
    """
    Using a codex, returns a map of {name: editions} where
    editions is sorted from newest to oldest

    path: the sets path
    codex: a sorted list of downloaded sets
    newest: the newest set to consider
    oldest: the oldest set to consider
    ignore: a set of editions to ignore
    """
    acc = {}
    for edition in _read_editions(codex, newest, oldest, ignore):
        edfile = EDDEX[edition] if edition in EDDEX else edition
        with open(f"{path}/{edfile}.json", "r") as fp:
            reader = csv.DictReader(fp)
            for line in fp.readlines():
                row = json.loads(line)
                editions = acc.get(row["name"], [])
                editions.append(edition)
                acc[row["name"]] = editions
    return acc
