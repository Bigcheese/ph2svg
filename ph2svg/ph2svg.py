from urlparse import urlparse
import sys
import re
import json
from xml.sax.saxutils import escape
import wsgiref
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
import traceback

def fullName(card):
  return ', '.join([card['title'], card.get('subtitle', '')]).rstrip(', ')
  
def text(x, y, size, t, rot = False):
  return '<text transform="matrix({} {} {})" font-family="Calibri" font-size="{}">{}</text>'.format('0 -1 1 0' if rot else '1 0 0 1', x, y, size, escape(unicode(t).encode('UTF-8')))

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

cardDb = json.load(open('cards.json'))
cardIndex = {x['id']:x for x in cardDb}
data = open('MLPCCGDecklist.svg').read()
noquery = open('noquery.html').read()

def gen(url):
  o = urlparse(url)
  d = {v.split("=")[0]:v.split("=")[1] for v in o.query.split("&")}
  code = d.get("v1code")
  if not code:
    return
  cards = [re.search('(\w+)(\d+)x(\d+)', x).groups() for x in code.split("-")]
  mane = None
  drawDeck = []
  problemDeck = []
  for x in cards:
    card = cardIndex[(x[0] + x[1]).lower()]
    count = x[2]
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
    status = '200 OK'
    headers = [('Content-type', 'image/svg+xml')]
    start_response(status, headers)  
    return [data, ret, '</svg>']
  except:
    traceback.print_exc(20, env['wsgi.errors'])
    start_response('400 Bad Request', [('Content-type', 'text/plain')])
    return ['Invalid request.']
  
def main():
  httpd = make_server('', 8000, ph2svg)
  print "Serving on port 8000..."
  httpd.serve_forever()

if __name__ == "__main__":
  main()
