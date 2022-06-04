import os
import random
import requests
import string
import time
import json
from base64 import b64encode
from hmac import new
from hashlib import sha1
from json_minify import json_minify


session = requests.Session()


def tz_filter():
    UTC = {
        "GMT0": 0, "GMT1": 60, "GMT2": 120, "GMT3": 180, "GMT4": 240, "GMT5": 300, "GMT6": 360,
        "GMT7": 420, "GMT8": 480, "GMT9": 540, "GMT10": 600, "GMT11": 660, "GMT12": +720,
        "GMT13": +780, "GMT-1": -60, "GMT-2": -120, "GMT-3": -180, "GMT-4": -240, "GMT-5": -300,
        "GMT-6": -360, "GMT-7": -420, "GMT-8": -480, "GMT-9": -540, "GMT-10": -600, "GMT-11": -660
        }
    hour = time.strftime("%H", time.gmtime())
    if hour == "00": return UTC["GMT-1"]
    if hour == "01": return UTC["GMT-2"]
    if hour == "02": return UTC["GMT-3"]
    if hour == "03": return UTC["GMT-4"]
    if hour == "04": return UTC["GMT-5"]
    if hour == "05": return UTC["GMT-6"]
    if hour == "06": return UTC["GMT-7"]
    if hour == "07": return UTC["GMT-8"]
    if hour == "08": return UTC["GMT-9"]
    if hour == "09": return UTC["GMT-10"]
    if hour == "10": return UTC["GMT13"]
    if hour == "11": return UTC["GMT12"]
    if hour == "12": return UTC["GMT11"]
    if hour == "13": return UTC["GMT10"]
    if hour == "14": return UTC["GMT9"]
    if hour == "15": return UTC["GMT8"]
    if hour == "16": return UTC["GMT7"]
    if hour == "17": return UTC["GMT6"]
    if hour == "18": return UTC["GMT5"]
    if hour == "19": return UTC["GMT4"]
    if hour == "20": return UTC["GMT3"]
    if hour == "21": return UTC["GMT2"]
    if hour == "22": return UTC["GMT1"]
    if hour == "23": return UTC["GMT0"]


class Client:
    def __init__(self, device_id):
        self.api = "https://service.narvii.com/api/v1"
        self.device_id = self.generate_device_id() if device_id is None else device_id
        self.headers = {"NDCDEVICEID": self.device_id, "SMDEVICEID": "b89d9a00-f78e-46a3-bd54-6507d68b343c", "Accept-Language": "en-EN", "Content-Type": "application/json; charset=utf-8", "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.1.1; SM-G973N Build/beyond1qlteue-user 5; com.narvii.amino.master/3.4.33562)", "Host": "service.narvii.com", "Accept-Encoding": "gzip", "Connection": "keep_alive"}
        self.sid, self.auid = None, None
        self.comId = self.get_from_link(link=input('ComLink >> '))['linkInfoV2']['extensions']['community']['ndcId']

    def generate_signature_message(self, data):
        signature_message = b64encode(bytes.fromhex("42") + new(bytes.fromhex("F8E7A61AC3F725941E3AC7CAE2D688BE97F30B93"), data.encode("utf-8"), sha1).digest()).decode("utf-8")
        self.headers["NDC-MSG-SIG"] = signature_message
        return signature_message

    def generate_device_id(self):
        identifier = os.urandom(20)
        mac = new(bytes.fromhex("02B258C63559D8804321C5D5065AF320358D366F"), bytes.fromhex("42") + identifier, sha1)
        return f"42{identifier.hex()}{mac.hexdigest()}".upper()

    def login(self, email, password):
        data = json.dumps({"email": email, "secret": f"0 {password}", "deviceID": self.device_id, "clientType": 100, "action": "normal", "timestamp": (int(time.time() * 1000))})
        self.headers["ndc-msg-sig"] = self.generate_signature_message(data=data)
        request = session.post(f"{self.api}/g/s/auth/login", data=data, headers=self.headers)
        print(request.json()['api:statuscode'])
        if request.json()['api:statuscode'] != 0: raise Exception(request.json()['api:message'])
        try: self.sid, self.auid = request.json()["sid"], request.json()["auid"]
        except Exception: raise Exception('Bad email, password or unverified acount')
        return request.json()

    def send_active_object(self, comId, start_time: int = None, end_time: int = None, timers: list = None, tz: int = -time.timezone // 1000):
        data = {"userActiveTimeChunkList": [{"start": start_time, "end": end_time}], "timestamp": int(time.time() * 1000), "optInAdsFlags": 2147483647, "timezone": tz}
        if timers: data["userActiveTimeChunkList"] = timers
        data = json_minify(json.dumps(data))
        self.headers["ndc-msg-sig"] = self.generate_signature_message(data=data)
        request = session.post(f"{self.api}/x{comId}/s/community/stats/user-active-time?sid={self.sid}", data=data, headers=self.headers)
        return request.json()

    def get_from_link(self, link):
        return session.get(f"{self.api}/g/s/link-resolution?q={link}", headers=self.headers).json()


def main():
    device_id = None
    if input('Have own deviceId? (y/n) >> ').lower() == 'y':
        device_id = input('DeviceId >> ')
    client = Client(device_id)
    client.login(email=input('Email >> '), password=input('Password >> '))
    while True:
        print(f"send_active_object: {client.send_active_object(comId=client.comId, timers=[{'start': int(time.time()), 'end': int(time.time()) + 300} for _ in range(50)], tz=tz_filter())['api:message']}.")
        print('start sleep one hour...')
        time.sleep(3600)


if __name__ == '__main__':
    main()
