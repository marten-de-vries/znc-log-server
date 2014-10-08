#!/usr/bin/env python3
#
#	Copyright 2014, Marten de Vries
#
#	Permission to use, copy, modify, and/or distribute this software for
#	any purpose with or without fee is hereby granted, provided that the
#	above copyright notice and this permission notice appear in all
#	copies.
#
#	THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
#	WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
#	WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
#	AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
#	DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA
#	OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
#	TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
#	PERFORMANCE OF THIS SOFTWARE.

import flask
import os
import re
import datetime
import jinja2
import collections
import colorsys
import random
import codecs

#Python 3 compatibility
try:
	unicode
except NameError:
	unicode = str

app = flask.Flask(__name__)
app.config.from_object('config')

channelsRE = '|'.join(re.escape(c) for c in app.config['CHANNELS'])
fileRE = re.compile(r'[^_]*_[^_]*_(?P<channel>' + channelsRE + r')_(?P<date>[^\.]*)')

time = r'\[\d\d:\d\d:\d\d\]'
timeRE = re.compile(time)

normalNickRE = re.compile('(?P<prefix>' + time + r' &lt;)(?P<nick>[^&]*)(?P<suffix>&gt;)')
slashMeNickRE = re.compile('(?P<prefix>' + time + r' \* )(?P<nick>[^ ]*)(?P<suffix> )')

nonChat = time + r' \*\*\* '
nonChatRE = re.compile(nonChat)

filterRE = re.compile(nonChat + r'(?:Quits|Joins|Parts)\:')

nickChangeRE = re.compile(nonChat + r'(?P<from>[^ ]*) is now known as (?P<to>.*)')

def files():
	result = {channel: {} for channel in app.config['CHANNELS']}
	for f in os.listdir(app.config['LOG_PATH']):
		m = fileRE.match(f)
		if m:
			date = m.group('date')
			date = date[:4] + "-" + date[4:6] + "-" + date[6:]
			result[m.group('channel')][date] = f
	return result

@app.route('/')
def index():
	return flask.render_template('index.html', channels=app.config['CHANNELS'])

@app.route('/<channel>/')
def channel(**data):
	try:
		data['dates'] = files()[data['channel']]
	except KeyError:
		flask.abort(404)
	return flask.render_template('channel.html', **data)

def modifyLine(line, nickColors):
	if filterRE.match(line):
		return ""
	line = unicode(jinja2.escape(line))

	#highlighting
	def wrapNick(match):
		nick = match.group('nick')
		color = nickColors[nick]
		middle = "<span style='color: " + color + ";'>" + nick + "</span>"
		return match.group('prefix') + middle + match.group('suffix')
	line = normalNickRE.sub(wrapNick, line)
	line = slashMeNickRE.sub(wrapNick, line)
	#keep nickColors up-to-date if necessary
	match = nickChangeRE.match(line)
	if match and match.group('from') in nickColors:
		nickColors[match.group('to')] = nickColors.pop(match.group('from'))

	def wrapTime(match):
		time = match.group(0)[1:-1]
		return u"<a class='time' id='" + time + "' href='#" + time + "'>[" + time + "]</a>"
	if nonChatRE.match(line):
		line = "<span class='non-chat'>" + line + "</span>"
	line = timeRE.sub(wrapTime, line)

	#pretty printing
	line = line.replace('\n', '<br />\n')
	return line

@app.route('/<channel>/<date>')
def log(**data):
	try:
		filename = files()[data['channel']][data['date']]
	except KeyError:
		flask.abort(404)
	nickColors = collections.defaultdict(nextColor)
	log = []
	path = os.path.join(app.config['LOG_PATH'], filename)
	with codecs.open(path, encoding='UTF-8', errors='replace') as f:
		for line in f:
			log.append(modifyLine(line, nickColors))
	data['log'] = u"".join(log)
	return flask.render_template('log.html', **data)

GOLDEN_RATIO_CONJUGATE = 0.618033988749895
currentHue = random.random()

def nextColor():
	global currentHue
	#calculates a new color, as distinctive from the others as possible
	#credits: http://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
	currentHue = (currentHue + GOLDEN_RATIO_CONJUGATE) % 1
	r, g, b = colorsys.hsv_to_rgb(currentHue, 1, 0.5)
	r, g, b = r * 255, g * 255, b * 255
	return '#%02x%02x%02x' % (r, g, b)

if __name__ == '__main__':
	app.run()
