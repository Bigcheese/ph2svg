import asyncio
import aiohttp
import collections
import json
import re
from fuzzywuzzy import process

url = 'http://ponycard.twilightparadox.com/mlpapi1/cards?query=rev:live&oguids=true'

class CardsDB:
  def __init__(self, **kwargs):
    self.cards = []
    # GUID
    self.cardsByID = dict()
    # Set, type{None, 'f', 'P'}, number
    self.cardsByAllIDS = dict()
    self.future = None
    self.namesBySet = collections.defaultdict(list)
    self.allNames = []
    self.nameToCard = {}

  def start(self):
    self.future = self.load()
    return self.future

  @asyncio.coroutine
  def load(self):
    response = yield from aiohttp.request('GET', url)
    response = yield from response.read_and_close(decode=True)
    self.cards = response['data']
    for card in self.cards:
      self.cardsByID[card['card_guid']] = card
      self.namesBySet[card['set']].append(card['fullname'])
      self.allNames.append(card['fullname'])
      self.nameToCard[card['fullname']] = card
      for id in card['allids']:
        self.cardsByAllIDS[id] = card

  def decodeName(self, card):
    if card['set'] == 'Full Sets':
      return None
    name = card['desc']
    if card['set'] == 'Promos':
      if name.find('Baltimare') != -1 or name.find('SDCC') != -1:
        return None
      if name.find('Pre-Release') != -1:
        return None
      if name.startswith('Lady Justice Volunteer Promo'):
        return {'name': 'Lady Justice, Judge & Jury', 'id': 'pf16PR'}
    set = card['set']

    # Try to find the card ID. Should always be the last number.
    id = None
    try:
      id = re.findall('[FPfp]?[^ \t\n#0-9]?[0-9]{1,3}', name)[-1]
      name = name.replace(id, '')
      name = name.strip()
      if name[-1] == '-':
        name = name[:-1]
        name = name.strip()
    except:
      pass
    score = -1
    # Find the closest matching name. Things may be misspelled ;/
    fullname = None
    if set not in self.namesBySet:
      extract = process.extractOne(name, self.allNames)
      score = extract[1]
    else:
      extract = process.extractOne(name, self.namesBySet[set])
      score = extract[1]
    fullname = extract[0]
    return {'name': fullname, 'id': id}

@asyncio.coroutine
def printCards():
  c = CardsDB()
  yield from c.load()
  print(c.cardsByID)

def main():
  loop = asyncio.get_event_loop()
  loop.run_until_complete(asyncio.wait([printCards()]))

if __name__ == '__main__':
  main()
