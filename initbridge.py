from phue import Bridge

import env_config


def initbridge():
    bridge = Bridge(ip=env_config.hue_bridge_ip(), config_file_path='./.python_hue')  # connected to Deco mesh

    # Gebruikt de koppelgegevens uit .python_hue. Alleen de allereerste keer (zonder .python_hue)
    # moet je eerst op de knop van de Hue bridge drukken.
    bridge.connect()
    return bridge
