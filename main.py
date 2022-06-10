from prometheus_client import start_http_server
from http import client, HTTPStatus
import logging
import time
import sys
import os
import aqicn
import signal
from threading import Event
import requests

"""
Enviroment variable lables used to read values from.
HOST_PORT       Sets port to run the prometheus http server, default to 80
LATITUDE        Sets the latitude to use for the AQI calculation
LONGITUDE       Sets the longitude to use for the AQI calculation
DECONZ_TOKEN    Sets deconz token, default is 'demo'
UPDATE_INTERVAL Sets interval between updates in seconds, default is 10.0 seconds
"""

POST_LABLE = 'HOST_PORT'
LATITUDE_LABLE = 'LATITUDE'
LONGITUDE_LABLE = 'LONGITUDE'
TOKEN_LABLE = 'AQICN_TOKEN'
TIMEOUT_LABLE = 'UPDATE_INTERVAL'

exit = Event()


def signalShuttdown(self, *args):
    exit.set()


config = {
    'host_port': 80,
    'lat': '',
    'lon': '',
    'token': 'demo',
    'timeout': 10.0
}

if POST_LABLE in os.environ:
    config['host_port'] = int(os.environ[POST_LABLE])

if LATITUDE_LABLE in os.environ:
    config['lat'] = os.environ[LATITUDE_LABLE]

if LONGITUDE_LABLE in os.environ:
    config['lon'] = os.environ[LONGITUDE_LABLE]

if TOKEN_LABLE in os.environ:
    config['token'] = os.environ[TOKEN_LABLE].strip()

if TIMEOUT_LABLE in os.environ:
    config['timeout'] = float(os.environ[TIMEOUT_LABLE])


def create_logger(scope):
    logger = logging.getLogger(scope)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%dT%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


if __name__ == '__main__':
    logger = create_logger('aqicn-exporter')

    if config['token'] == 'demo':
        logger.error(
            f"Demo aqicn token provided. Please provide your own token.")
        sys.exit(1)

    if not config['lat'] or not config['lon']:
        logger.error(
            f"Latitude or longitude not set. Please set them in the environment variables.")
        sys.exit(1)

    start_http_server(config['host_port'])

    signal.signal(signal.SIGTERM, signalShuttdown)
    signal.signal(signal.SIGHUP, signalShuttdown)
    signal.signal(signal.SIGINT, signalShuttdown)
    signal.signal(signal.SIGABRT, signalShuttdown)

    while not exit.is_set():

        r = requests.get('https://api.waqi.info/feed/geo:' +
                         config['lat'] + ';' + config['lon'] + '/?token=' + config['token'])

        if r.json()['status'] == 'ok':
            aqicn.extract_metrics(logger, r.json())
            logger.info(f"Request succeeded")
        else:
            logger.error(
                f"Request did not result in a successful status, {r.json()['status']}.")

        sleepTime = 0.0

        while (config['timeout'] > sleepTime) and not exit.is_set():
            time.sleep(0.1)
            sleepTime += 0.1

    logger.info("shutting down")
