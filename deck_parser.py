"""deck_parser.py

Utilities to read and write Cockatrice .cod deck files.
"""
from dataclasses import dataclass, field
from typing import List
from lxml import etree

@dataclass
class CardEntry:
    number: int
    name: str
    setShortName: str | None = None
    collectorNumber: str | None = None
    uuid: str | None = None

@dataclass
class CockatriceDeck:
    deckname: str
    zone_main: List[CardEntry] = field(default_factory=list)
    zone_side: List[CardEntry] = field(default_factory=list)


def parse_cod(path: str) -> CockatriceDeck:
    """Parse a .cod (Cockatrice deck) file into a CockatriceDeck object."""
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(path, parser)
    root = tree.getroot()

    deckname_el = root.find('deckname')
    deckname = deckname_el.text if deckname_el is not None else 'Unnamed'

    deck = CockatriceDeck(deckname=deckname)

    for zone in root.findall('zone'):
        zone_name = zone.get('name')
        target_list = deck.zone_main if zone_name == 'main' else deck.zone_side
        for card in zone.findall('card'):
            number = int(card.get('number', '1'))
            name = card.get('name') or (card.text or '').strip()
            setShortName = card.get('setShortName')
            collectorNumber = card.get('collectorNumber')
            uuid = card.get('uuid')
            entry = CardEntry(number=number, name=name, setShortName=setShortName, collectorNumber=collectorNumber, uuid=uuid)
            target_list.append(entry)

    return deck


def write_cod(deck: CockatriceDeck, path: str) -> None:
    """Write a CockatriceDeck object to a .cod XML file at path."""
    root = etree.Element('cockatrice_deck', version='1')
    last = etree.SubElement(root, 'lastLoadedTimestamp')
    from datetime import datetime
    last.text = datetime.now().strftime('%a %b %d %H:%M:%S %Y')
    dn = etree.SubElement(root, 'deckname')
    dn.text = deck.deckname

    comments = etree.SubElement(root, 'comments')
    tags = etree.SubElement(root, 'tags')

    def make_zone(name, entries):
        zone = etree.SubElement(root, 'zone', name=name)
        for c in entries:
            attrs = {'number': str(c.number), 'name': c.name}
            if c.setShortName:
                attrs['setShortName'] = c.setShortName
            if c.collectorNumber:
                attrs['collectorNumber'] = c.collectorNumber
            if c.uuid:
                attrs['uuid'] = c.uuid
            etree.SubElement(zone, 'card', **attrs)

    make_zone('main', deck.zone_main)
    make_zone('side', deck.zone_side)

    xml_bytes = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    with open(path, 'wb') as f:
        f.write(xml_bytes)
