#!/usr/bin/env python3
import requests
import json
import datetime
import locale
import os
import operator
import urllib.parse
from math import sqrt, sin, cos, sqrt, atan2, radians
import argparse




parser = argparse.ArgumentParser(description='Boğaziçi  Üniversitesi Kandilli Rasathanesine ait sot veriler.')

parser.add_argument(
        '-m','--mod',
        default='magnitude', 
        choices=['magnitude','distance', 'hybrid'],
        help='Hybrid hem mesafeyi hem de enerjiyi baz alarak önem sırasını ve bildirimin önceliğini belirler.'
)


parser.add_argument(
        '-c', '--coord',
        metavar=('lat','lon'),
        nargs=2,
        type=float, 
        default=('41.0082', '28.97784'),
)

parser.add_argument('-k','--kritik',
        type=float, 
        default=5.0, 
        help='Kritik depremler için alt sınır enerjisi.'
)

args = parser.parse_args()
print('Args;', args)

def get_biggest(_mags):
        return max(_mags.items(), key=operator.itemgetter(1))[0]


def get_dist(_coords):
    coord = [float(i) for i in args.coord]
    _coords = _coords.split(",")
    _coords = [float(i) for i in _coords]


    #Dünyanın çapı
    R = 6373.0

    lat1 = radians(coord[0])
    lon1 = radians(coord[1])
    lat2 = radians(_coords[0])
    lon2 = radians(_coords[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Eratosthenes of Cyrene, deden ölsün
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c



    

# Türkçe tarih formatı ve karakerler için 
# locale'yi tr_tr.utf8 yapıyorum.
locale.setlocale(locale.LC_ALL, 'tr_TR.utf8')

# Kullanılacak değişkenler falan
temp_file        = '{}/.cache/son-depremler.json'.format(os.getenv("HOME"))
notification_str = "{4} tarihinde\n{0} bölgesinde büyüklükleri:\nML: {1} \nMW: {2} \nMD: {3} olan bir deprem gerçekleşti. {5} kilometre ötede."
cmd_template     = "notify-send --urgency {} '{}'"
notification     = ""
last_quakes      = []
magnitudes       = []
distances        = []



# İsteği yap
req = requests.get('http://kandilli-son-depremler-api.herokuapp.com/')
# Bildirim öncelik parametresini al
def get_urgency(_magnitude):
        if (_magnitude >= args.kritik): 
                return 'critical'
        elif (_magnitude >= args.kritik-2.0): #TODO; input al?
                return 'normal'
        else:
                return 'low'




# İstek gövdesini json'a dönüştür ve ilk 10 elemanı dön
smol_dist = float('inf') #global variable oh no
for quake in req.json()[slice(30)]:
        # büyüklükleri float olarak ayıkla
        # daha sonra aralarından büyük olanı alacağız
        mags = {
                'ml': float(quake['ml'] or 0),
                'mw': float(quake['mw'] or 0),
                'md': float(quake['md'] or 0)
        }
        dist = get_dist(quake['geolocation'])
        if dist < smol_dist:
            smol_dist = dist
        # Alacağız demiştim.
        biggest = get_biggest(mags)
        # Genel büyüklükler listesine en büyük M* değerini ekle
        # Üç büyüklük türünden en büyük olanı alıyoruz.
        magnitudes.append(quake[biggest])
        distances.append(dist)
        # Bildirim metnine verdiğimiz parametreleri yerleştiriyoruz.
        last_quakes.append(notification_str.format(
                *(
                        str(quake['address']),
                        str(quake['ml'] or 0),
                        str(quake['mw'] or 0),
                        str(quake['md'] or 0),
                        # Lanet tarih formatlama işleri
                        str(datetime
                                .datetime
                                .strptime(quake['timestamp'], '%Y.%m.%d %H:%M:%S')
                                .strftime('%d %B %Y %A, %H:%M')),
                        # Burada bitiyor.
                        "{:.2f}".format(dist)
                )
        ))

# Gelen ilk 10 satırdan en şiddetli olanın büyüklük türünü (ml,mw,md neyse işte) alıyoruz.
mag           = max(magnitudes)
dist          = min(distances)
# En şiddetli olanı bildirimler listesinden çekip alıyoruz.
biggest_index = magnitudes.index(mag)
closest_index = distances.index(dist)


# Bu bildirim daha önce gösterilmişse bu script biter.
if os.path.exists(temp_file):
        with open(temp_file, 'r') as outfile:
                if last_quakes[biggest_index] in json.load(outfile):
                    exit()



if args.mod == 'distance':
    kriter = last_quakes[closest_index]
elif args.mod == 'magnitude':
    kriter = last_quakes[biggest_index]
else:
    kriter = last_quakes[closest_index] #TODO; hybrid'i hesapla lol
 
# Bildirim komutunu çalıştır.
message = cmd_template.format(
                *(
                        get_urgency(float(mag or 0)), # Önceliği al. 5 ve üstü kritik, 3-5 arası normal, kalanı düşük
                kriter
                )
        )
result  = os.system(message)

# 0 döner. dönmezse hata vardır.
if result != 0:
        exit()
else:
        # Gösterilen bildirimi cache'e kaydetsin. spam yapmasın.
        with open(temp_file, 'w') as outfile:
                json.dump([last_quakes[biggest_index]], outfile)
