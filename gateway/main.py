#! /usr/bin/env python
# coding: utf-8
import sys
import time
import timeit
import json
import ssl
import signal
import pickle
import hashlib
import traceback
from threading import Thread, RLock
from multiprocessing import Process
from ConfigParser import ConfigParser
# import pandas as pd
from logger import _Logger, _log
from common import DeviceInterface, Point
from protocol_modbus import MODBUSDevice
from protocol_dlt import DLTDevice
from protocol_opc import OPCDevice
from protocol_bacnet import BACNetDevice, init_bacnet
from concurrent.futures import ThreadPoolExecutor

import redis
import requests
import eventlet
from paho.mqtt import client as mqtt
from paho.mqtt import publish


REDIS_DB = 0
FREQ_READ_DATA = 180          # seconds, 默认采集数据频率   3分钟
FREQ_PUB_DATA = 300         # seconds, 默认上报数据频率     5分钟
FREQ_HEARTBEAT = 600         # seconds, 默认心跳包频率     10分钟
FREQ_CHECK_POINT = 1800     # seconds, 检测坏点频率       30分钟
READ_MODE = 0               # 点位读取模式: 0 单点，1 全部, 2 异步, 3 多端口并行
REDIS_CHANNEL = u"gateway:queue"
REDIS_BAD_MSGS = u"gateway:bad_msgs"
REDIS_BAD = u"gateway:bad"
REDIS_POINTS = u"gateway:points"
MESSAGE_SEP = ","
gateway_id = None
building_id = None
GATEWAY_VERSION = 0
__settings_file = "./settings.ini"
__gateway_id_file = "./gateway.id"
g_ca_file = "./ca.crt"
g_lock = RLock()
g_redis_push = None
g_tls = {"ca_certs": g_ca_file, "tls_version": ssl.PROTOCOL_TLSv1, "insecure": True}


with open(__gateway_id_file, 'rb') as f:
    gateway_id = f.read()

try:
    gateway_id = int(gateway_id)
except:
    raise Exception(u"can't find gateway id")

if gateway_id < 0:
    raise Exception(u"bad gateway id")

TOPIC_DATA = "gateway/{}".format(gateway_id)
TOPIC_HEART_BEAT = "gateway/gateway_heardbeat/{}".format(gateway_id)


class Settings:
    pass


class Gateway:
    pass


settings = Settings()
gateway = Gateway()


def load_settings():
    parser = ConfigParser()
    parser.read(__settings_file)

    global settings
    if parser.has_section(u"debug"):
        ini_obj = type('ini', (object,), dict(parser.items(u"debug")))
        setattr(settings, u'debug', ini_obj)
    else:
        raise Exception(u"debug settings not found!")

    if parser.has_section(u"mqtt"):
        ini_obj = type('ini', (object,), dict(parser.items(u'mqtt')))
        setattr(settings, u'mqtt', ini_obj)
    else:
        raise Exception(u"MQTT settings not found!")

    if parser.has_section(u"backend"):
        ini_obj = type('ini', (object,), dict(parser.items(u'backend')))
        setattr(settings, u'backend', ini_obj)
    else:
        raise Exception(u"backend settings not found!")

    if parser.has_section(u"bacnet"):
        ini_obj = type('ini', (object,), dict(parser.items(u"bacnet")))
        setattr(settings, u'bacnet', ini_obj)
    else:
        raise Exception(u"BACNET settings not found!")

    if parser.has_section(u"redis"):
        ini_obj = type('ini', (object,), dict(parser.items(u"redis")))
        setattr(settings, u'redis', ini_obj)
        global REDIS_DB
        if hasattr(settings.redis, "db"):
            REDIS_DB = settings.redis.db
        global g_redis_push
        g_redis_push = redis.Redis(settings.redis.server, settings.redis.port, db=REDIS_DB)
    else:
        raise Exception(u"redis settings not found!")


def fetch_gateway_config_offline():
    types = {
        "opc": 1,
        "dlt": 2,
        "modbus": 3,
        "bacnet": 4
    }
    parser = ConfigParser()
    parser.read(__settings_file)
    global gateway
    if not parser.has_section(u"gateway"):
        raise Exception(u"gateway settings not found!")
    configs = dict(parser.items(u"gateway"))
    if parser.has_option(u"gateway", u"freq_pub"):
        setattr(gateway, u"freq_pub", int(configs[u"freq_pub"]))
    if parser.has_option(u"gateway", u"freq_read"):
        setattr(gateway, u"freq_read", int(configs[u"freq_read"]))
    if parser.has_option(u"gateway", u"mode_read"):
        setattr(gateway, u"mode_read", int(configs[u"mode_read"]))
        global READ_MODE
        _mode = int(int(configs[u"mode_read"]))
        if _mode == 0 or _mode == 1 or _mode == 2 or _mode == 3:
            READ_MODE = _mode
    if parser.has_option(u"gateway", u"building_id"):
        global building_id
        building_id = int(int(configs[u"building_id"]))
    devicedata = pd.read_csv("points.csv", sep="\r\n", delimiter=",",encoding='gb18030')
    cdevices = {}
    for index, row in devicedata.iterrows():
        if row[0] not in cdevices:
            cdevices[row[0]] = {
                "influx_key": row[0],
                "type_id": int(types[row[1]]),
                "config": json.loads(row[2]),
                "points": []
            }
            point = {
                "property_name": row[3],
                "field_name": row[4],
                "display_name": row[5],
                "config": json.loads(row[6]),
            }
            cdevices[row[0]]["points"].append(point)
        else:
            point = {
                "property_name": row[3],
                "field_name": row[4],
                "display_name": row[5],
                "config": json.loads(row[6]),
            }
            cdevices[row[0]]["points"].append(point)
    devices = dict()
    total_points = 0
    for item in cdevices:
        try:
            # 1: modbus  2: dlt   3: opc    4: bacnet
            type_id = int(cdevices[item]["type_id"])
            config = cdevices[item]["config"]

            if type_id == 2:
                device = MODBUSDevice(**config)
            elif type_id == 3:
                device = DLTDevice(**config)
            elif type_id == 1:
                device = OPCDevice(**config)
            elif type_id == 4:
                device = BACNetDevice(**config)

            else:
                raise TypeError("unknown device type")

            influx_key = cdevices[item]["influx_key"]
            setattr(device, "influx_key", influx_key)

            if not hasattr(cdevices[item], "points") and "points" not in cdevices[item]:
                raise TypeError("device miss points config")

            points = cdevices[item]["points"]
            points_dict = dict()
            for p in points:
                if isinstance(p, dict):
                    point = Point(**p)
                    total_points += 1
                    point.influx_key = influx_key
                    h_key = hash_key(influx_key, point.field_name)
                    p = load_point(h_key)
                    # 使用缓存的点位值
                    if isinstance(p, Point):
                        point.value = p.value
                        point.time_stamp = p.time_stamp

                    if is_bad_point(h_key):
                        point.is_bad = True

                    points_dict[point.field_name] = point

            setattr(device, "points", points_dict)
            devices[influx_key] = device

        except Exception as e:
            _log(u"Error when init lower device", e, item)
            continue

    _log(u"load gateway total points: %d" % total_points)

    with g_lock:
        setattr(gateway, u"devices", devices)
        setattr(gateway, u"total_points", total_points)


def fetch_gateway_config():
    global gateway, GATEWAY_VERSION
    _log(u"loading device configs from AIoT...")
    if not hasattr(settings, u"backend"):
        raise Exception(u"Error: settings has no backend config")

    _url = u"{}/api/gateway_seriesnew/{}/".format(settings.backend.server, gateway_id)
    response = requests.get(_url, auth=(settings.backend.username, settings.backend.password))
    if response.status_code != 200:
        raise Exception(u"Error: cannot request {}".format(_url))

    result = json.loads(response.text)
    _log(u"starting parse gateway devices...")

    # do load or update gateway version & configs
    if int(result[u"version"]) != GATEWAY_VERSION:
        for key in result:
            setattr(gateway, key, result[key])
            if key == u"version":
                GATEWAY_VERSION = int(result[u"version"])
                gateway.version = GATEWAY_VERSION

            if key == u"id":
                gateway.id = gateway_id

            if key == u"building_id":
                global building_id
                building_id = int(result[key])

            if key == u"mode_read":
                global READ_MODE
                _mode = int(result[key])
                if _mode == 0 or _mode == 1 or _mode == 2 or _mode == 3:
                    READ_MODE = _mode

            # update gateway.devices
            if key == u"Devices":
                devices = dict()
                total_points = 0
                for item in gateway.Devices:
                    try:
                        if "type_id" not in item:
                            raise TypeError("device miss type_id")

                        if "config" not in item:
                            raise TypeError("device miss config")

                        # 1: modbus  2: dlt   3: opc    4: bacnet
                        type_id = int(item["type_id"])
                        config = json.loads(item["config"])

                        if type_id == 2:
                            device = MODBUSDevice(**config)
                        elif type_id == 3:
                            device = DLTDevice(**config)
                        elif type_id == 1:
                            device = OPCDevice(**config)
                        elif type_id == 4:
                            device = BACNetDevice(**config)

                        else:
                            raise TypeError("unknown device type")

                        if "influx_key" not in item:
                            raise TypeError("device miss influx_key")

                        influx_key = item["influx_key"]
                        setattr(device, "influx_key", influx_key)

                        if not hasattr(item, "points") and "points" not in item:
                            raise TypeError("device miss points config")

                        points = item["points"]
                        points_dict = dict()
                        for p in points:
                            if isinstance(p, dict):
                                point = Point(**p)
                                total_points += 1
                                point.influx_key = influx_key
                                h_key = hash_key(influx_key, point.field_name)
                                p = load_point(h_key)
                                # 使用缓存的点位值
                                if isinstance(p, Point):
                                    point.value = p.value
                                    point.time_stamp = p.time_stamp

                                if is_bad_point(h_key):
                                    point.is_bad = True

                                points_dict[point.field_name] = point

                        setattr(device, "points", points_dict)
                        devices[influx_key] = device

                    except Exception as e:
                        _log(u"Error when init lower device", e, item)
                        continue

                _log(u"load gateway total points: %d" % total_points)

                with g_lock:
                    setattr(gateway, u"devices", devices)
                    setattr(gateway, u"total_points", total_points)

        _log(u"load gateway config done! updated!\r\n")
    else:
        _log(u"load gateway config done! no change!\r\n")


try:
    load_settings()
except:
    traceback.print_exc()
    sys.exit(1)


class MessageType:
    HEARTBEAT = 0
    DATA = 1
    BADPOINTS = 2


class MQTTClient(Thread):

    def __init__(self, server, username, password, topics):
        Thread.__init__(self)
        self.setDaemon(True)
        self._logger = _Logger("./command.log", name="command")
        client_id = u"ELC_GATEWAY_SUB_{}".format(gateway_id)
        self.client = mqtt.Client(clean_session=False, client_id=client_id)
        self.client.max_inflight_messages_set(100)
        self.client.username_pw_set(username, password)
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_disconnect = self.on_disconnect
        self.client.on_connect = self.on_connect
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLSv1, ca_certs=g_ca_file)
        self.client.tls_insecure_set(True)
        self.client.connect(server[0], server[1])

        for topic in topics:
            if u"gateway" in topic:
                topic = u"{}{}".format(topic, gateway_id)
            else:
                topic = u"{}{}".format(topic, building_id)

            _log(u"MQTT Subscriber subscribe topic[{}]".format(topic))
            self.client.subscribe(topic)

    def on_message(self, client, user_data, msg):
        topic = msg.topic.lower()
        pay_load = msg.payload.decode("utf-8")
        _log(u"Topic[{}] on message: {}".format(topic, pay_load))
        if u"command" in topic:
            self.deal_command(pay_load)
        elif u"updateversion" in topic:
            if int(settings.debug.mode) == 0:
                fetch_gateway_config()
            elif int(settings.debug.mode) == 1:
                fetch_gateway_config_offline()

    def on_subscribe(self, client, user_data, mid, granted_qos):
        _log(u"MQTT Subscriber subscribe success, mid={}".format(mid))

    def on_connect(self, client, user_data, flags, rc):
        if rc == 0:
            _log(u"MQTT Subscriber connect success!")
        else:
            raise Exception("Error: mqtt connect failed! code={}".format(rc))

    def on_disconnect(self, userdata, rc):
        _log(u"MQTT Subscriber client disconnected! Try reconnecting...")

    def deal_command(self, msg):
        payload = msg.split(" ")
        self._logger.log(u"received command: {}".format(msg))
        if len(payload) == 3:
            influx_key = payload[0].split(",")[0]
            kv_pairs = payload[1].split(",")
            timestamp = payload[2]

            global gateway
            if influx_key not in gateway.devices:
                self._logger.log(u"deal command: influx key [{}] not found in gateway.devices".format(influx_key))
                return

            device = gateway.devices[influx_key]
            for item in kv_pairs:
                kv = item.split("=")
                field_name = kv[0]
                value = kv[1]
                if isinstance(value, unicode):
                    if value.isdecimal():
                        value = int(value)
                    else:
                        try:
                            value = float(value)
                        except:
                            value = str(value)

                if field_name not in device.points:
                    self._logger.log(u"deal command: field_name[{}] not found in device[{}].points".format(field_name, influx_key))
                    continue

                try:
                    value = value / float(device.points[field_name].configs["factor"])
                except:
                    value = value

                h_key = hash_key(influx_key, field_name)
                is_bad = False
                write_only = False

                if g_redis_push.hget(REDIS_BAD, h_key):
                    is_bad = True

                point = device.points[field_name]
                if point.configs and u"write_only" in point.configs and point.configs[u"write_only"] == 1:
                    write_only = True

                # 跳过坏点并且该点位非只写
                if is_bad and not write_only:
                    self._logger.log(u"deal command: [{}, {}] is a bad point and not a write only point!".format(
                        influx_key, field_name))
                    continue

                property_name = point.property_name
                try:
                    if point.configs and isinstance(point.configs, dict):
                        result = device.do_write(property_name, value, *point.args, **point.configs)
                    else:
                        result = device.do_write(property_name, value)

                    if result:
                        self._logger.log(u"deal command: write value to device success!")
                    else:
                        self._logger.log(u"deal command: write value to device failed! {}".format(msg))
                except Exception as e:
                    self._logger.log(u"deal command: error occurred when write value to device!", e)

    def run(self):
        self.client.loop_forever()


class ProcessPublishData(Process):

    def __init__(self, redis_server="127.0.0.1", redis_db=0, redis_port=6379, mqtt_server=None, mqtt_port=None,
                 mqtt_user=None, mqtt_pwd=None, tls=None):
        Process.__init__(self)
        # self.daemon = True

        self.redis_server = redis_server
        self.redis_port =redis_port
        self.redis_db = redis_db
        self.mqtt_server = mqtt_server
        self.mqtt_port = mqtt_port
        self.mqtt_auth = {u"username": mqtt_user, u"password": mqtt_pwd}
        self._tls = tls

    def on_publish(self, client, userdata, mid):
        pass

    def on_subscribe(self, client, user_data, mid, granted_qos):
        pass

    def on_message(self, client, user_data, msg):
        pass

    def on_disconnect(self, userdata, rc):
        _log(u"DataPublisher MQTT Client disconnected! Try reconnect...")

    def on_connect(self, client, user_data, flags, rc):
        if rc == 0:
            _log(u"DataPublisher MQTT Client connect success!")
        else:
            _log(u"DataPublisher MQTT Client connect failed! Return code =", rc)

    def run(self):
        client_id = u"ELC_GATEWAY_PUB_{}".format(gateway_id)
        mqtt_client = mqtt.Client(clean_session=False, client_id=client_id)
        mqtt_client.username_pw_set(self.mqtt_auth.get(u"username"), self.mqtt_auth.get(u"password"))
        # mqtt_client.on_message = self.on_message
        # mqtt_client.on_subscribe = self.on_subscribe
        # mqtt_client.on_publish = self.on_publish
        mqtt_client.on_disconnect = self.on_disconnect
        mqtt_client.on_connect = self.on_connect
        mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLSv1, ca_certs=g_ca_file)
        mqtt_client.tls_insecure_set(True)
        mqtt_client.connect(self.mqtt_server, self.mqtt_port)
        mqtt_client.loop_start()

        redis_cli = redis.Redis(self.redis_server, self.redis_port, db=self.redis_db)
        msg = None

        while True:
            if msg is None:
                msg = redis_cli.blpop(REDIS_CHANNEL, timeout=1)
                if not msg:
                    continue
                msg = msg[1]

            if not msg:
                continue

            try:
                # msg old: 1,190001_116,CWPStateMA,1.000000
                # msg new: 190001_116 CWPStateMA=1.00000 1559621642000000000
                #      or: 190001_116 CWPStateMA=1.00000,CWPStateNew=0.00000 1559621642000000000
                args = msg.split(" ")
                if len(args) == 3:
                    t = args[2]
                    if len(t) == 19:
                        payload = u" ".join(args)
                        # _log(u"publish data:", payload)

                        mqtt_client.publish(TOPIC_DATA, payload)
                        if not mqtt_client.socket():
                            raise Exception(u"emqx server connect error!")
                        msg = None
                        continue

                # 处理格式错误mqtt报文
                redis_cli.rpush(REDIS_BAD_MSGS, msg)
                msg = None

            except:
                # 发送失败， 重试
                traceback.print_exc()
                continue


class ProcessHeartBeat(Process):

    def __init__(self, freq=60, mqtt_server=None, mqtt_port=None, mqtt_user=None, mqtt_pwd=None):
        Process.__init__(self)
        # self.daemon = True
        self._freq = freq
        self.mqtt_server = mqtt_server
        self.mqtt_port = mqtt_port
        self.mqtt_auth = {u"username": mqtt_user, u"password": mqtt_pwd}
        self._tls = None

    def run(self):
        while True:
            try:
                payload = u"PING"
                _log(u"heart beat process:PING")
                self._tls = {"ca_certs": g_ca_file, "tls_version": ssl.PROTOCOL_TLSv1, "insecure": True}
                publish.single(TOPIC_HEART_BEAT, payload, hostname=self.mqtt_server, port=self.mqtt_port,
                               tls=self._tls, auth=self.mqtt_auth)

            except:
                traceback.print_exc()

            time.sleep(self._freq)


class ThreadCheckBadPoints(Thread):

    def __init__(self, freq=3600):
        Thread.__init__(self)
        self.setDaemon(True)
        self._freq = freq

    def run(self):

        while True:

            if READ_MODE == 2:
                t = Thread(target=async_check_thread)
            else:
                t = Thread(target=check_bad_points)

            t.setDaemon(True)
            t.start()
            time.sleep(self._freq)


class ThreadLoopReadPoints(Thread):

    def __init__(self, freq=300):
        Thread.__init__(self)
        self.setDaemon(True)
        self._freq = freq

    def run(self):
        while True:
            if hasattr(gateway, u"freq_read"):
                freq_read = int(gateway.freq_read)
                if self._freq != freq_read:
                    self._freq = freq_read

            if READ_MODE == 2:
                t = Thread(target=async_read_thread)
            elif READ_MODE == 3:
                t = Thread(target=async_read_by_ip)
            else:
                t = Thread(target=read_all_points)

            t.setDaemon(True)
            t.start()

            time.sleep(self._freq)


class ThreadEnqueueData(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.setDaemon(True)

    @staticmethod
    def loop_devices():
        _log(u"LOOP_DEVICES: start!")
        total = 0
        has_value = 0
        if not hasattr(gateway, u"devices"):
            return

        if not isinstance(gateway.devices, dict):
            return

        # device
        for influx_key, device in gateway.devices.items():
            if not isinstance(device, DeviceInterface):
                _log(u"LOOP_DEVICES: bad device [{}]".format(influx_key))
                continue

            if not hasattr(device, u"points"):
                _log(u"LOOP_DEVICES: device[{}] has no points!".format(influx_key))
                continue

            if not isinstance(device.points, dict):
                _log(u"LOOP_DEVICES: device[{}] has bad format of points".format(influx_key))
                continue

            dict_values = dict()
            for field_name, point in device.points.items():
                total += 1
                if not isinstance(point, Point):
                    _log(u"LOOP_DEVICES: device[{}] has a bad point[{}]".format(influx_key, field_name))
                    continue

                _field_name = point.field_name
                if _field_name is None:
                    _log(u"LOOP_DEVICES: device[{}] point[{}] has no field_name".format(influx_key, field_name))
                    device.points.pop(field_name)
                    continue

                if point.value is None or point.time_stamp is None:
                    continue
                time_new = int(int(time.time()) * 1e9)
                if int((time_new - point.time_stamp) / 1e9) > FREQ_READ_DATA * 2:
                    continue
                dict_values.setdefault(_field_name, point.value)
                save_point(point)
                has_value += 1

            # 设备所有点位值都为空，跳过
            if not dict_values:
                continue

            t = int(int(time.time()) * 1e9)
            k_values = list()
            for k, v in dict_values.items():
                if isinstance(v, float):
                    k_values.append(u"%s=%f" % (k, v))
                else:
                    k_values.append(u"{}={}".format(k, v))

            payload = u"{} {} {}".format(influx_key, u",".join(k_values), t)
            g_redis_push.rpush(REDIS_CHANNEL, payload)
            # _log(u"LOOP_DEVICES: {}".format(payload))

        _log(u"LOOP_DEVICES: done! total points: %d, has value: %d" % (total, has_value))

    def run(self):
        self.loop_devices()


def hash_key(influx_key, field_name):
    # h = hashlib.md5()
    # data = "#".join([str(influx_key), str(property_name), str(field_name)])
    # h.update(data.encode("utf-8"))
    # return h.hexdigest()
    return u"{}#{}".format(influx_key, field_name)


def save_point(point):
    if not isinstance(point, Point):
        return

    h_key = hash_key(point.influx_key, point.field_name)
    binary_obj = pickle.dumps(point)
    return g_redis_push.hset(REDIS_POINTS, h_key, binary_obj)


def load_point(h_key):
    binary_obj = g_redis_push.hget(REDIS_POINTS, h_key)

    if binary_obj:
        point = pickle.loads(binary_obj)
        return point

    return None


def is_bad_point(key, point=None):
    if point and isinstance(point, Point):
        if hasattr(point, u"is_bad"):
            return point.is_bad

    return g_redis_push.hget(REDIS_BAD, key) == "True"


def mark_bad_point(key, point=None):
    if point and isinstance(point, Point):
        point.is_bad = True
    if hasattr(settings.debug, "check_flag"):
        if int(settings.debug.check_flag) == 1:
            g_redis_push.hset(REDIS_BAD, key, "True")
        else:
            pass
    else:
        g_redis_push.hset(REDIS_BAD, key, "True")


def remove_bad_point(key):
    return g_redis_push.hdel(REDIS_BAD, key)


def check_bad_points():
    _log(u"CHECK_BAD_POINTS: start")
    if not hasattr(settings, u"redis"):
        _log(u"CHECK_BAD_POINTS: cannot find redis settings")
        return

    if not hasattr(gateway, u"devices"):
        _log(u"CHECK_BAD_POINTS: gateway has no devices")
        return

    redis_cli = redis.Redis(settings.redis.server, settings.redis.port, db=REDIS_DB)
    for influx_key, device in gateway.devices.items():
        if not isinstance(device, DeviceInterface):
            continue

        if not hasattr(device, u"points"):
            continue

        if not isinstance(device.points, dict):
            continue

        for field_name, point in device.points.items():
            if isinstance(point, Point):
                if point.configs and u"write_only" in point.configs and point.configs[u"write_only"] == 1:
                    continue

                h_key = hash_key(influx_key, point.field_name)
                if point.is_bad:
                    mark_bad_point(h_key)

    bad_points = redis_cli.hgetall(REDIS_BAD)
    if len(bad_points) < 1:
        _log(u"CHECK_BAD_POINTS: gateway has no bad points!")
        return

    start = timeit.default_timer()
    total = 0
    removed = 0

    for h_key in bad_points.keys():
        total += 1

        influx_key, field_name = h_key.split("#")
        device = gateway.devices.get(influx_key)

        if not isinstance(device, DeviceInterface):
            _log(u"CHECK_BAD_POINTS: bad device[{}], continue".format(influx_key))
            remove_bad_point(h_key)
            continue

        if not hasattr(device, u"points") or not isinstance(device.points, dict):
            _log(u"CHECK_BAD_POINTS: device [{}] has no points or points is not a dict!".format(h_key))
            remove_bad_point(h_key)
            continue

        point = device.points.get(field_name)
        if not point or not isinstance(point, Point):
            _log(u"CHECK_BAD_POINTS: No such point [{}] in device [{}]".format(field_name, influx_key))
            remove_bad_point(h_key)
            continue

        if point.configs and u"write_only" in point.configs and point.configs[u"write_only"] == 1:
            continue

        try:
            if hasattr(point, u"configs") and isinstance(point.configs, dict):
                value = device.do_read(point.property_name, **point.configs)
            else:
                value = device.do_read(point.property_name)

            if value is None:
                _log(u"CHECK_BAD_POINTS: point[{}, {}] has no value return".format(influx_key, point.field_name))
                continue

            point.value = value
            point.time_stamp = int(int(time.time()) * 1e9)

            if remove_bad_point(h_key):
                removed += 1

        except Exception as e:
            _log(u"CHECK_BAD_POINTS: point[{}, {}], {}".format(influx_key, point.field_name, str(e)))
            continue

    end = timeit.default_timer()
    elapsed = end - start
    _log(u"CHECK_BAD_POINTS: finished! total bad points: %d, removed: %d, elapsed: %.2f seconds" %
         (total, removed, elapsed))

    bad_points = redis_cli.hgetall(REDIS_BAD)
    t = int(int(time.time()) * 1e9)

    if len(bad_points) > 0:
        payload = u"bad points: {}, {}".format(u"|".join(bad_points.keys()), t)
    else:
        payload = u"bad points:"

    _log(u"CHECK_BAD_POINTS: bad points in cache: {}".format(len(bad_points)))

    auth = {"username": settings.mqtt.username, "password": settings.mqtt.password}
    g_tls = {"ca_certs": g_ca_file, "tls_version": ssl.PROTOCOL_TLSv1, "insecure": True}
    publish.single(TOPIC_HEART_BEAT, payload, hostname=settings.mqtt.server,
                   port=settings.mqtt.port, tls=g_tls, auth=auth)


def read_all_points():
    if not hasattr(gateway, u"devices"):
        _log(u"Error: gateway has no lower devices to read!")
        return

    _log(u"start loop read points, mode: {}".format(READ_MODE))
    start = timeit.default_timer()
    total = 0
    read = 0

    for influx_key, device in gateway.devices.items():
        # 单点轮询
        if READ_MODE == 0:
            for point in device.points.values():
                total += 1
                h_key = hash_key(influx_key, point.field_name)

                # 跳过坏点
                if is_bad_point(h_key):
                    continue

                if isinstance(point, Point):
                    try:
                        if point.configs and isinstance(point.configs, dict):
                            point_configs = point.configs
                        else:
                            point_configs = dict()

                        value = device.do_read(point.property_name, **point_configs)

                        if value is None:
                            raise ValueError(u"do_read() return None")

                        point.value = value
                        point.time_stamp = int(int(time.time()) * 1e9)
                        read += 1

                    except Exception as e:
                        _log(u"SERIAL_READ MODE[{}] Error: [{}, {}], {}".format(READ_MODE, influx_key,
                                                                                point.field_name, unicode(e)))
                        if h_key:
                            mark_bad_point(h_key, point)

                        continue

        # 设备全部点位一次读取
        elif READ_MODE == 1:
            total += len(device.points.keys())
            try:
                result = device.read_all()

                if result is False:
                    raise ValueError(u"read_all() return False")

                read += len(device.points.keys())

            except Exception as e:
                _log(u"SERIAL_READ MODE[{}] Error: [{}], {}".format(READ_MODE, influx_key, unicode(e)))
                continue

    end = timeit.default_timer()
    elapsed = end - start
    _log(u"loop read points finished! total: %d, read points: %d, elapsed: %.2f seconds" % (total, read, elapsed))


def async_read_thread():
    if not hasattr(gateway, u"devices"):
        _log(u"ASYNC_READ_POINT: gateway has no lower devices to read!")
        return

    _log(u"ASYNC_READ_POINT: start")

    pool_num = 1000
    if hasattr(gateway, u"total_points"):
        pool_num = int(gateway.total_points)

    pool = eventlet.GreenPool(pool_num)
    start = timeit.default_timer()
    total = 0

    for influx_key, device in gateway.devices.items():
        if not isinstance(device, DeviceInterface):
            continue

        if not hasattr(device, u"points"):
            continue

        for k, point in device.points.items():
            if not isinstance(point, Point):
                continue

            h_key = hash_key(influx_key, point.field_name)
            if not is_bad_point(h_key):
                total += 1
                pool.spawn(async_read_point, device, point)

    pool.waitall()
    end = timeit.default_timer()
    elapsed = end - start
    _log(u"ASYNC_READ_POINT: finished! total: %d, elapsed: %.2f seconds" % (total, elapsed))


def async_read_by_ip():
    if not hasattr(gateway, u"devices"):
        _log(u"ASYNC_READ_POINT: gateway has no lower devices to read!")
        return

    _log(u"ASYNC_READ_IP: start")
    ip_pool = {}

    start = timeit.default_timer()
    total = 0
    read = 0
    p = ThreadPoolExecutor(8)
    result_list = []
    for influx_key, device in gateway.devices.items():
        if not isinstance(device, DeviceInterface):
            continue

        if not hasattr(device, u"points"):
            continue

        total += len(device.points)

        dev_ip = device.configs.get("ip")
        dev_port = device.configs.get("port", 0)
        dev = "{}:{}".format(dev_ip, dev_port)
        if dev:
            if ip_pool.get(dev):
                ip_pool[dev][influx_key] = device
            else:
                ip_pool[dev] = {}
                ip_pool[dev][influx_key] = device

    for _ip in ip_pool:
        obj = p.submit(read_all_device, ip_pool[_ip])
        _log("ip {} now start".format(_ip))
        result_list.append(obj)
    p.shutdown()
    for obj in result_list:
        read += obj.result()

    end = timeit.default_timer()
    elapsed = end - start
    _log(u"ASYNC_READ_IP: finished! total: %d, read: %d, elapsed: %.2f seconds" % (total, read, elapsed))


def read_all_device(devices):
    read = 0

    for influx_key, device in devices.items():
        # 单点轮询
        for point in device.points.values():
            h_key = hash_key(influx_key, point.field_name)

            # 跳过坏点
            if is_bad_point(h_key):
                continue

            if isinstance(point, Point):
                try:
                    if point.configs and isinstance(point.configs, dict):
                        point_configs = point.configs
                    else:
                        point_configs = dict()

                    value = device.do_read(point.property_name, **point_configs)

                    if value is None:
                        raise ValueError(u"do_read() return None")

                    point.value = value
                    point.time_stamp = int(int(time.time()) * 1e9)
                    read += 1

                except Exception as e:
                    _log(u"SERIAL_READ MODE[{}] Error: [{}, {}], {}".format(READ_MODE, influx_key,
                                                                            point.field_name, unicode(e)))
                    if h_key:
                        mark_bad_point(h_key, point)

                    continue
    return read


def async_read_point(device, point):
    if isinstance(device, DeviceInterface):
        if isinstance(point, Point):
            if point.configs and isinstance(point.configs, dict):
                point_configs = point.configs
            else:
                point_configs = dict()

            h_key = hash_key(point.influx_key, point.field_name)
            try:
                value = device.do_read(point.property_name, **point_configs)
                if value is None:
                    raise Exception(u"do_read() return None")

                point.value = value
                point.time_stamp = int(int(time.time()) * 1e9)
                return value
            except Exception as e:
                mark_bad_point(h_key, point)
                _log(u"ASYNC_READ_POINT Error: [{}, {}], {}".format(point.influx_key, point.field_name, unicode(e)))
    return None


def async_check_thread():
    _log(u"ASYNC_Check_Point: start")
    if not hasattr(settings, u"redis"):
        _log(u"ASYNC_Check_Point: cannot find redis settings")
        return

    if not hasattr(gateway, u"devices"):
        _log(u"ASYNC_Check_Point: gateway has no devices")
        return

    redis_cli = redis.Redis(settings.redis.server, settings.redis.port, db=REDIS_DB)
    bad_points = redis_cli.hgetall(REDIS_BAD)
    if len(bad_points) < 1:
        _log(u"ASYNC_Check_Point: gateway has no bad points!")
        return

    pool_num = len(bad_points)
    pool = eventlet.GreenPool(pool_num)
    start = timeit.default_timer()
    total = 0

    for h_key, v in bad_points.items():
        if v != "True":
            remove_bad_point(h_key)
            continue

        influx_key, field_name = h_key.split(u"#")
        device = gateway.devices.get(influx_key)
        if not device:
            remove_bad_point(h_key)
            continue

        if not isinstance(device, DeviceInterface):
            gateway.devices.pop(h_key)
            remove_bad_point(h_key)
            continue

        if not hasattr(device, u"points") or not isinstance(device.points, dict):
            gateway.devices.pop(h_key)
            remove_bad_point(h_key)
            continue

        point = device.points.get(field_name)

        if not point or not isinstance(point, Point):
            device.points.pop(field_name)
            remove_bad_point(h_key)
            continue

        if not point.is_bad:
            remove_bad_point(h_key)
            continue

        if point.configs and u"write_only" in point.configs and point.configs[u"write_only"] == 1:
            remove_bad_point(h_key)
            continue

        total += 1
        pool.spawn(async_check_point, device, point)

    pool.waitall()
    end = timeit.default_timer()
    elapsed = end - start
    _log(u"ASYNC_Check_Point: finished! total bad points: %d, elapsed: %.2f seconds" %
         (total, elapsed))

    bad_points = redis_cli.hgetall(REDIS_BAD)
    t = int(int(time.time()) * 1e9)

    if len(bad_points) > 0:
        payload = u"bad points: {}, {}".format(u"|".join(bad_points.keys()), t)
    else:
        payload = u"bad points:"

    _log(u"ASYNC_Check_Point: bad points in cache: {}".format(len(bad_points)))

    auth = {"username": settings.mqtt.username, "password": settings.mqtt.password}
    g_tls = {"ca_certs": g_ca_file, "tls_version": ssl.PROTOCOL_TLSv1, "insecure": True}
    publish.single(TOPIC_HEART_BEAT, payload, hostname=settings.mqtt.server,
                   port=settings.mqtt.port, tls=g_tls, auth=auth)


def async_check_point(device, point):
    if isinstance(device, DeviceInterface):
        if isinstance(point, Point):
            if point.configs and isinstance(point.configs, dict):
                point_configs = point.configs
            else:
                point_configs = dict()

            h_key = hash_key(point.influx_key, point.field_name)
            try:
                value = device.do_read(point.property_name, **point_configs)
                if value is None:
                    raise Exception(u"do_read() return None")

                point.is_bad = False
                remove_bad_point(h_key)
                point.value = value
                point.time_stamp = int(int(time.time()) * 1e9)
                return value
            except Exception as e:
                _log(u"ASYNC_Check_Point Error: [{}, {}], {}".format(point.influx_key, point.field_name, unicode(e)))
    return None


def enqueue_single_point_data(point):
    t = int(int(time.time()) * 1e9)
    payload = u"{} {}={} {}".format(point.influx_key, point.field_name, point.value, t)
    g_redis_push.rpush(REDIS_CHANNEL, payload)
    _log("report value: ", payload)


def fake_gateway_for_debug():
    fake_bacnet_device = {
        "type": "bacnet",
        "influx_key": "190002_012",
        "points": [
            {
                "property_name": "multiStateValue:2",
                "field_name": "PHHStateRun",
                "priority": 16,
            },
            {
                "property_name": "multiStateValue:3",
                "field_name": "PHHStateFault",
                "priority": 16,
            },
            {
                "property_name": "multiStateValue:4",
                "field_name": "PHHStateMA",
                "priority": 16,
            }
        ],
        "config": {
            "ip": "192.168.1.21",
            "port": 47809
        },
    }

    fake_opc_device = {
        "type": "opc",
        "influx_key": "190001_001",
        "points": [
            {
                "property_name": "P0.R.LGJ1.LRT15",
                "field_name": "CCRTempT3",
            },
        ],
        "config": {
            "address": "http://192.168.1.135/soap",
        },
    }

    fake_devices = list()
    fake_devices.append(fake_bacnet_device)
    fake_devices.append(fake_opc_device)
    global gateway
    setattr(gateway, u"Devices", fake_devices)


p_publish_data = None
p_heart_beat = None


def sig_handler(signum, frame):
    global p_publish_data, p_heart_beat
    _log("\r\n")

    try:
        if p_publish_data and p_publish_data.is_alive():
            _log(u"kill publish data process")
            p_publish_data.terminate()
    except:
        pass

    try:
        if p_heart_beat and p_heart_beat.is_alive():
            _log(u"kill heart beat process")
            p_heart_beat.terminate()
    except:
        pass

    _log(u"gateway Exit!\r\n")
    sys.exit(0)


signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)


def main():
    try:
        time.sleep(2)
        init_bacnet(settings.bacnet.localaddr)
        if int(settings.debug.mode) == 0:
            fetch_gateway_config()
        elif int(settings.debug.mode) == 1:
            fetch_gateway_config_offline()

        if building_id is None or building_id < 0:
            raise Exception("no building id")

        redis_cli = redis.Connection(settings.redis.server, settings.redis.port, db=REDIS_DB)
        redis_cli.connect()

        global p_publish_data, p_heart_beat

        # mqtt 订阅客户端
        t_mqtt = MQTTClient(server=(settings.mqtt.server, settings.mqtt.port),
                       username=settings.mqtt.username, password=settings.mqtt.password,
                       topics=settings.mqtt.topics.split(u","))
        t_mqtt.start()

        # 心跳包子进程
        p_heart_beat = ProcessHeartBeat(freq=FREQ_HEARTBEAT, mqtt_server=settings.mqtt.server,
                                        mqtt_port=settings.mqtt.port, mqtt_user=settings.mqtt.username,
                                        mqtt_pwd=settings.mqtt.password)
        p_heart_beat.start()

        # 数据上报子进程
        p_publish_data = ProcessPublishData(redis_server=settings.redis.server, redis_port=settings.redis.port,
                                            redis_db=REDIS_DB, mqtt_server=settings.mqtt.server,
                                        mqtt_port=settings.mqtt.port, mqtt_user=settings.mqtt.username,
                                        mqtt_pwd=settings.mqtt.password, tls=g_tls)
        p_publish_data.start()

        # 坏点检测子线程
        t_check_bad_points = ThreadCheckBadPoints(freq=FREQ_CHECK_POINT)
        t_check_bad_points.start()

        # 读取点位线程
        t_loop_read = ThreadLoopReadPoints()
        t_loop_read.start()

    except:
        _log(traceback.print_exc())
        time.sleep(10)      # 失败后延迟10秒重启，防止不停请求gateway配置
        sys.exit(1)

    redis_cli.disconnect()
    del redis_cli

    # fake_gateway_for_debug()
    _freq_pub = FREQ_PUB_DATA
    time.sleep(5)

    while True:
        if hasattr(gateway, u"freq_pub"):
            freq_pub = int(gateway.freq_pub)
            if _freq_pub != freq_pub:
                _freq_pub = freq_pub

        t_pub = ThreadEnqueueData()
        t_pub.start()
        time.sleep(_freq_pub)


if __name__ == '__main__':

    main()
