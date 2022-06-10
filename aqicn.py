from prometheus_client import Gauge
import json

_gauges = {
    "aqi": Gauge("aqicn_air_quality_index", "Air Quality Index in ppm", ["city"]),
}


def extract_metrics(logger, request_content):

    data = request_content

    if data['status'] != 'ok':
        logger.info(f"Status not ok: {data['status']}")
    else:
        _extract_aqi(data)

    # for key in data:
    #     metric = data[key]

    #     if metric['type'] in _functionMap:
    #         _functionMap[metric['type']](metric)
    #     else:
    #         logger.info(f"Unknown metric type \"{metric['type']}\".")


def _extract_aqi(data):

    value = data['data']['aqi']
    city_name = data['data']['city']['name']

    _gauges['aqi'].labels(city=city_name).set(value)
