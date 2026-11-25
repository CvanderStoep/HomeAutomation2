from influxdb_client import Point


def hue_lights(bridge):
    data_point = []

    for light in bridge.lights:
        light_on = 1 if light.on else 0
        data_point.append(Point("hue_lights").tag("light", light.name).field("on", light_on))

    return data_point
