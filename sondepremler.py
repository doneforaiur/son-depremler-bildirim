#!/usr/bin/env python3
import requests
import json
import datetime
import locale
import os
import operator

locale.setlocale(locale.LC_ALL, 'tr_TR.utf8')

temp_file = '{}/.cache/son-depremler.json'.format(os.getenv("HOME"))

req = requests.get('http://kandilli-son-depremler-api.herokuapp.com/')
req = req.json()
range = slice(10)
req = req[range]

last_quakes = []
magnitudes  = []

for quake in req:
	last_quakes.append({
		'zaman': datetime
			.datetime
			.strptime(quake['timestamp'], '%Y.%m.%d %H:%M:%S')
			.strftime('%d %B %Y %A, %H:%M'),
		'yer': quake['address'],
		'buyukluk_mw': float(quake['mw'] or 0),
		'buyukluk_md': float(quake['md'] or 0),
		'buyukluk_ml': float(quake['ml'] or 0)
	})

	mags = {
		'ml': float(quake['ml'] or 0), 'mw': float(quake['mw'] or 0), 'md': float(quake['md'] or 0)
	}

	biggest = max(mags.items(), key=operator.itemgetter(1))[0]
	magnitudes.append(quake[biggest])

	recent_quake = last_quakes[ len(last_quakes) - 1 ]

	format_string = "{4} tarihinde\n{0} bölgesinde büyüklükleri:\nML: {1} \nMW: {2} \nMD: {3} olan bir deprem gerçekleşti."
	format_data = (str(recent_quake['yer']) ,str(recent_quake['buyukluk_ml']), str(recent_quake['buyukluk_mw']), str(recent_quake['buyukluk_md']), str(recent_quake['zaman']))
	recent_quake['bildirim'] = format_string.format(*format_data)
	last_quakes[ len(last_quakes) - 1 ] = recent_quake

biggest_index = magnitudes.index(max(magnitudes))

if os.path.exists(temp_file):
	with open(temp_file, 'r') as outfile:
		data = json.load(outfile)
		print(last_quakes[biggest_index] in data)
		if last_quakes[biggest_index] in data:
			exit()

result = os.system("notify-send --urgency critical '{}'".format(last_quakes[biggest_index]['bildirim']))

if result != 0:
	exit()
else:
	with open(temp_file, 'w') as outfile:
		json.dump([last_quakes[biggest_index]], outfile)
