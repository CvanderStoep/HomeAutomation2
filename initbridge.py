from phue import Bridge


def initbridge():
    from private_info import ip_address_hue_bridge
    bridge = Bridge(ip=ip_address_hue_bridge, config_file_path='./.python_hue')  # connected to Deco mesh

    # Gebruikt de koppelgegevens uit .python_hue. Alleen de allereerste keer (zonder .python_hue)
    # moet je eerst op de knop van de Hue bridge drukken.
    bridge.connect()
    return bridge
