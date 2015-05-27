from . import cardsjson

import asyncio
from urllib.parse import urlparse
import sys
import re
import json
from xml.sax.saxutils import escape
import wsgiref
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
import traceback
import io
import qrcode
import base64

carddb = cardsjson.CardsDB()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait([carddb.load()]))

data = open('MLPCCGDecklist.svg', encoding='utf-8').read().encode('utf-8')
noquery = open('noquery.html', encoding='utf-8').read().encode('utf-8')

def fullName(card):
  return ', '.join([card['title'], card.get('subtitle', '')]).rstrip(', ')
  
def text(x, y, size, t, rot = False):
  return '<text transform="matrix({} {} {})" font-family="Calibri" font-size="{}">{}</text>'.format('0 -1 1 0' if rot else '1 0 0 1', x, y, size, escape(t))

def genDrawDeck(deck):
  cardX = 100.5
  countX = 70.5654
  startY = 158.5205
  Y = startY
  incY = 14.149384375
  
  count = 0
  ret = ''
  for card in deck:
    ret += text(countX, Y, 12, str(card[0]))
    ret += text(cardX, Y, 12, fullName(card[1]))
    Y += incY
    count += int(card[0])
  ret += text(countX, startY + (incY * 33), 12, str(count))
  return ret

def genProblemDeck(deck):
  countY = 596.9277
  cardY = 568.2988
  offset = 240.7695
  startX = 477.1826
  incX = 18.72485
  X = startX
  count = 0
  ret = ''
  for card in deck:
    if count == 5:
      X = startX
      countY -= offset
      cardY -= offset
    ret += text(X, countY, 14, str(card[0]), True)
    ret += text(X, cardY, 14, fullName(card[1]), True)
    X += incX
    count = count + 1
  return ret

class UnknownCardError(Exception):
  def __init__(self, card):
    self.card = card

def gen(url):
  o = urlparse(url)
  d = {v.split("=")[0]:v.split("=")[1] for v in o.query.split("&")}
  code = d.get("v1code")
  if not code:
    return
  cards = [list(re.search('([a-zA-Z]{2})(F|PF)?(n?\d+)x(\d+)', x).groups()) for x in code.split("-")]
  mane = None
  drawDeck = []
  problemDeck = []
  for x in cards:
    try:
      if x[2].startswith('n'):
        x[2] = '-' + x[2][1:]
      card = carddb.cardsByAllIDS[(x[1].lower() if x[1] else '') + x[2] + x[0].upper()]
    except:
      raise UnknownCardError(x[0] + x[1] + x[2])
    count = x[3]
    if (card['type'] == 'Mane'):
      mane = card
    elif (card['type'] == 'Problem'):
      problemDeck.append((count, card))
    else:
      drawDeck.append((count, card))

  ret = ''    
  
  ret += text(191.6245, 66.082, 14, d.get('date', ''))
  ret += text(191.6245, 82.1611, 14, d.get('location', ''))
  ret += text(334.625, 66.0815, 14, d.get('player', ''))
  ret += text(334.625, 82.1611, 14, d.get('event', ''))

  ret += text(334.625, 98.2417, 14, fullName(mane) if mane else '')
  ret += genDrawDeck(drawDeck)
  ret += genProblemDeck(problemDeck)
  
  return ret
 
def ph2svg(env, start_response):
  setup_testing_defaults(env)

  url = wsgiref.util.request_uri(env)
  if not urlparse(url).query:
    start_response('200 OK', [('Content-type', 'text/html')])
    return [noquery]
  
  try:
    ret = gen(url)
    img = qrcode.make('http://ponyhead.com/deckbuilder?' + urlparse(url).query, border=0)
    out = io.BytesIO()
    img.save(out)
    out.seek(0)
    b64 = base64.b64encode(out.read())
    status = '200 OK'
    headers = [('Content-type', 'image/svg+xml')]
    start_response(status, headers)
    return [data, ret.encode('utf-8'), b'<image transform="translate(450, 650)" width="130" height="130" xlink:href="data:image/png;base64,', b64, b'" />', b'</svg>']
  except:
    traceback.print_exc(20, env['wsgi.errors'])
    start_response('400 Bad Request', [('Content-type', 'text/plain')])
    return [b'Invalid request.']
  
def main():
  httpd = make_server('', 8000, ph2svg)
  print("Serving on port 8000...")
  httpd.serve_forever()

if __name__ == "__main__":
  main()
