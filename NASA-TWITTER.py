import requests
import json
from PIL import Image, ImageDraw, ImageFont
from requests_oauthlib import OAuth1
import os
import sys
from datetime import datetime, date, timedelta
import yaml

ts_filename = 'ts.yaml'

with open(ts_filename, "r") as stream:
    try:
        ts = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

CONSUMER_KEY = ts['api_key']
CONSUMER_SECRET = ts['api_key_secret']
ACCESS_TOKEN = ts['access_token']
ACCESS_SECRET = ts['access_token_secret']
BEARER_TOKEN = ts['bearer_token']
USER_ID = ts['user_id']

MEDIA_ENDPOINT_URL = 'https://upload.twitter.com/1.1/media/upload.json'
NASA_A_ENDPOINT_URL = 'https://ssd-api.jpl.nasa.gov/cad.api?neo=false&sort=dist&limit=1&diameter=true&kind=a'
NASA_C_ENDPOINT_URL = 'https://ssd-api.jpl.nasa.gov/cad.api?neo=false&sort=dist&limit=1&diameter=true&kind=c'
POST_ENDPOINT_URL = 'https://api.twitter.com/2/tweets'

oauth = OAuth1(CONSUMER_KEY, client_secret=CONSUMER_SECRET,
               resource_owner_key=ACCESS_TOKEN, resource_owner_secret=ACCESS_SECRET)

today = date.today()
yesterday = today - timedelta(days=1)
today_date = today.strftime("%d-%m-%Y")
yesterday_date = yesterday.strftime("%d-%m-%Y")

emoji_explanation = "🟢 : distance > 1,000,000km\n🟠 : 1,000,000 > distance > 384,400\n🔴 : distance < 384,400km"


def getNowTime():
    now = datetime.now()
    current_time = now.strftime("%H-%M-%S")
    return current_time


log_filename = 'logs.txt'

image_filename = f'./pngs/result_{today_date}_{getNowTime()}.png'
media_id = None
media_category = 'TweetImage'

valdict = {}
choix_ca = ''

print("GATHERING NASA'S API DATA")

with open(log_filename, 'a') as f:
    f.write(
        "-----------------------------------------------------------------------------------------\n")
    f.write(f"[{today_date}]\n")
    f.write(f"[{getNowTime()}] (EVENT) NASA'S API : GATHERING DATA\n")


r_a = requests.get(NASA_A_ENDPOINT_URL)
r_a_dict = r_a.json()
val_a_dict = dict()


if int(r_a_dict['count']) > 0:
    for i in range(len(r_a_dict['fields'])):
        for key, value in zip(r_a_dict['fields'], r_a_dict['data'][i]):
            val_a_dict[key] = value
        break
else:
    choix_ca = 'c'

r_c = requests.get(NASA_C_ENDPOINT_URL)
r_c_dict = r_c.json()
val_c_dict = dict()

if int(r_c_dict['count']) > 0:
    for i in range(len(r_c_dict['fields'])):
        for key, value in zip(r_c_dict['fields'], r_c_dict['data'][i]):
            val_c_dict[key] = value
        break
else:
    choix_ca = 'a'

if choix_ca == '':
    if val_a_dict['dist'] < val_c_dict['dist']:
        choix_ca = 'a'
    else:
        choix_ca = 'c'

if choix_ca == 'a':
    valdict = val_a_dict.copy()
elif choix_ca == 'c':
    valdict = val_c_dict.copy()

with open(log_filename, 'a') as f:
    f.write(
        f"[{getNowTime()}] (DATA) NASA'S API ASTEROID : {json.dumps(val_a_dict)}\n")
    f.write(
        f"[{getNowTime()}] (DATA) NASA'S API COMET : {json.dumps(val_c_dict)}\n")
    f.write(f"[{getNowTime()}] (EVENT) TYPE CHOICE : {choix_ca}\n")


def auToKm(au: float):
    km = au * 149597870.7
    return round(km)


def getDiameterFromH(H: float):
    diameter_min = 1329 / pow(0.25, 0.5) * pow(10, -0.2 * H)
    diameter_max = 1329 / pow(0.05, 0.5) * pow(10, -0.2 * H)
    return diameter_min, diameter_max


def diameterToStr(vals: dict):
    if vals['diameter'] == None:
        diam_min, diam_max = getDiameterFromH(float(vals['h']))
        diam_min = round(diam_min * 1000)
        diam_max = round(diam_max * 1000)
        return f"estimé entre {diam_min}m et {diam_max}m"
    else:
        return "de " + str(round(float(vals['diameter']), 2)) + "km"


def distanceTerreLune(dist: int):
    dist = round(dist / 384400, 2)
    return "(soit " + str(dist) + " fois la distance terre-lune)"


def sToH(speed: float):
    speed = speed * 3600
    return round(speed)


def emojiFromDist(dist: int):
    if dist > 999999:
        return "🟢"
    elif 999999 >= dist >= 384400:
        return "🟠"
    else:
        return "🔴"


def distanceTerreLuneInt(dist: int):
    dist = round(dist / 384400, 2)
    return dist


def drawing(DTL: float):
    draw = ""
    DTL = DTL * 10
    if DTL <= 10:
        for i in range(10):
            if i == 0:
                draw += "🌎"
            elif i == DTL:
                draw += "🌟"
            else:
                draw += "-"
        draw += "🌙"
    else:
        for i in range(round(DTL)):
            if i == 0:
                draw += "🌎"
            elif i == 10:
                draw += "🌙"
            else:
                draw += "-"
        draw += "🌟"

    width = 180 + 30 * len(draw)
    height = 140

    font_emo = ImageFont.truetype("Apple Color Emoji.ttc", size=32)
    font = ImageFont.truetype("Arial Unicode.ttf", size=114)
    img = Image.new('RGB', (width, height), (40, 40, 40))
    imgDraw = ImageDraw.Draw(img)

    for i in range(len(draw)):
        if draw[i] == "-":
            text = " " * i + draw[i] + " " * (len(draw) - i)
            text_box = imgDraw.textbbox((0, 0), text, font)
            new_w = text_box[2] - text_box[0]
            new_h = text_box[3] - text_box[1]
            x = round((width - new_w) / 2) - text_box[0] + 13
            y = round((height - new_h) / 2) - text_box[3] + 50
            imgDraw.text((x, y), text, font=font, embedded_color=True)
        else:
            text = " " * i + draw[i] + " " * (len(draw) - i)
            text_box = imgDraw.textbbox((0, 0), text, font_emo)
            new_w = text_box[2] - text_box[0]
            new_h = text_box[3] - text_box[1]
            x = round((width - new_w) / 2) - text_box[0] + 13
            y = round((height - new_h) / 2) - text_box[3] + 33
            imgDraw.text((x, y), text, font=font_emo, embedded_color=True)

    img.save(image_filename)

    return draw


with open(log_filename, 'a') as f:
    f.write(
        f"[DATA NAME DIST] : {valdict['des']} : {auToKm(float(valdict['dist']))}\n")

print("CREATING TWEET TEXT")

with open(log_filename, 'r') as f:
    file_brut = f.read()

yesterday_name = ""
file_brut = file_brut.split(f'[{yesterday_date}]')[
    1].split(f'[{today_date}]')[0]
file_brut = file_brut.split("\n")
for element in file_brut:
    element = element.split(" : ")
    if element[0] == '[DATA NAME DIST]':
        yesterday_name = str(element[1])
        yesterday_dist = int(element[2].split("\n")[0])


def getDiffDist(today_dist: int, today_name: str, yesterday_dist: int, yesterday_name: str):
    if today_name == yesterday_name:
        dist = today_dist - yesterday_dist
        if dist > 0:
            return f". Cet objet spacial s'est éloigné de {'{:,}'.format(dist)}km depuis hier"
        elif dist == 0:
            return ". Cet objet spacial ne s'est pas rapproché depuis hier"
        else:
            return f". Cet objet spacial s'est rapproché de {str('{:,}'.format(dist)).split('-')[1]}km depuis hier"
    else:
        return ""


def typeToString(type: str):
    if type == 'a':
        return "'#asteroide"
    elif type == 'c':
        return "a #comete"


with open(log_filename, 'a') as f:
    f.write(f"[{getNowTime()}] (EVENT) TWEET : CREATING TWEET'S TEXT\n")
tweet_text = f"{emojiFromDist(auToKm(float(valdict['dist'])))} L{typeToString(choix_ca)} {valdict['des']} d'un diamètre {diameterToStr(valdict)} passe actuellement à {str('{:,}'.format(auToKm(float(valdict['dist']))))}km de la #terre {distanceTerreLune(int(auToKm(float(valdict['dist']))))} à une vitesse de {str(round(float(valdict['v_rel']), 2)) + 'km/s'} ({sToH(float(valdict['v_rel']))}km/h){getDiffDist(auToKm(float(valdict['dist'])), valdict['des'], yesterday_dist, yesterday_name)} {emojiFromDist(auToKm(float(valdict['dist'])))}"
with open(log_filename, 'a') as f:
    f.write(f"[{getNowTime()}] (DATA) TWEET'S TEXT : {tweet_text}\n")

print("CREATING PNG")
with open(log_filename, 'a') as f:
    f.write(f"[{getNowTime()}] (EVENT) PNG : CREATING PNG\n")
drawing(distanceTerreLuneInt(auToKm(float(valdict['dist']))))
with open(log_filename, 'a') as f:
    f.write(f"[{getNowTime()}] (DATA) PNG : PNG '{image_filename}' CREATED\n")

print('POST INIT')
total_bytes = os.path.getsize(image_filename)
with open(log_filename, 'a') as f:
    f.write(f"[{getNowTime()}] (EVENT) TWEET : POST INIT\n")
request_data = {'command': 'INIT', 'media_type': 'image/png',
                'total_bytes': total_bytes, 'media_category': media_category}
req = requests.post(url=MEDIA_ENDPOINT_URL, data=request_data, auth=oauth)
try:
    media_id = req.json()['media_id']
except:
    with open(log_filename, 'a') as f:
        f.write(
            f"[{getNowTime()}] (ERROR) TWEET : POST INIT FAILED WITH ERROR : {req.json()}\n")
    sys.exit(0)
segment_id = 0

print('POST APPEND')
with open(log_filename, 'a') as f:
    f.write(f"[{getNowTime()}] (EVENT) TWEET : POST APPEND\n")
with open(image_filename, 'rb') as file:
    file_data = file.read()
request_data = {'command': 'APPEND',
                'media_id': media_id, "segment_index": segment_id}
files = {'media': file_data}
req = requests.post(url=MEDIA_ENDPOINT_URL,
                    data=request_data, files=files, auth=oauth)
if req.status_code < 200 or req.status_code > 299:
    with open(log_filename, 'a') as f:
        f.write(
            f"[{getNowTime()}] (ERROR) TWEET : POST APPEND FAILED WITH ERROR : {req.json()}\n")
    sys.exit(0)

print('POST FINALIZE')
with open(log_filename, 'a') as f:
    f.write(f"[{getNowTime()}] (EVENT) TWEET : POST FINALIZE\n")
request_data = {'command': 'FINALIZE', 'media_id': media_id}
req = requests.post(url=MEDIA_ENDPOINT_URL, data=request_data, auth=oauth)
media_id_string = req.json()['media_id_string']
processing_info = req.json().get('processing_info', None)

playload = json.dumps({"text": tweet_text, "media": {
    "media_ids": [media_id_string]}})
req = requests.post(url=POST_ENDPOINT_URL, headers={
    'Content-Type': 'application/json'}, data=playload, auth=oauth)
tweet_id = req.json()['data']['id']
if req.status_code == 201:
    print("TWEET POSTED")
    with open(log_filename, 'a') as f:
        f.write(f"[{getNowTime()}] (EVENT) TWEET : TWEET POSTED SUCCESSFULLY\n")
else:
    with open(log_filename, 'a') as f:
        f.write(
            f"[{getNowTime()}] (ERROR) TWEET : POST FINALIZE FAILED WITH ERROR : {req.json()}\n")
    print("AN ERROR OCCURED!")

playload = json.dumps({"text": emoji_explanation, "reply": {
    "in_reply_to_tweet_id": tweet_id}})
req = requests.post(url=POST_ENDPOINT_URL, headers={
    'Content-Type': 'application/json'}, data=playload, auth=oauth)
rep_tweet_id = req.json()['data']['id']
if req.status_code == 201:
    print("REPLY EXP POSTED")
    with open(log_filename, 'a') as f:
        f.write(
            f"[{getNowTime()}] (EVENT) REPLY : REPLY EXP POSTED SUCCESSFULLY\n")
else:
    with open(log_filename, 'a') as f:
        f.write(
            f"[{getNowTime()}] (ERROR) REPLY : REPLY EXP POST FAILED WITH ERROR : {req.json()}\n")
    print("AN ERROR OCCURED!")

FOLLOWER_ENDPOINT_URL = f'https://api.twitter.com/2/users/{USER_ID}/followers?max_results=1'
req = requests.get(url=FOLLOWER_ENDPOINT_URL, headers={
    "Authorization": f'Bearer {BEARER_TOKEN}'})
last_follower = req.json()['data'][0]['username']

with open(log_filename, 'a') as f:
    f.write(f"[DATA LAST FOLLOWER] : {last_follower}\n")

with open(log_filename, 'r') as f:
    file_brut = f.read()

yesterday_follower = ""
file_brut = file_brut.split(f'[{yesterday_date}]')[
    1].split(f'[{today_date}]')[0]
file_brut = file_brut.split("\n")
for element in file_brut:
    element = element.split(" : ")
    if element[0] == '[DATA LAST FOLLOWER]':
        yesterday_follower = str(element[1])

if last_follower != yesterday_follower:
    playload = json.dumps({"text": f'Dernier follower: @{last_follower}\nMerci !', "reply": {
        "in_reply_to_tweet_id": rep_tweet_id}})
    req = requests.post(url=POST_ENDPOINT_URL, headers={
        'Content-Type': 'application/json'}, data=playload, auth=oauth)

    if req.status_code == 201:
        print("REPLY LAST POSTED")
        with open(log_filename, 'a') as f:
            f.write(
                f"[{getNowTime()}] (EVENT) REPLY : REPLY LAST POSTED SUCCESSFULLY\n")
    else:
        with open(log_filename, 'a') as f:
            f.write(
                f"[{getNowTime()}] (ERROR) REPLY : REPLY LAST POST FAILED WITH ERROR : {req.json()}\n")
        print("AN ERROR OCCURED!")
else:
    with open(log_filename, 'a') as f:
        f.write(
            f"[{getNowTime()}] (EVENT) LAST FOLLOWER : NOT POSTING LAST REPLY BECAUSE YESTERDAY FOLLOWER IS THE SAME AS TODAY'S\n")
