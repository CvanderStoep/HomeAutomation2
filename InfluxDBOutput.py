import logging

import PluginLoader
import influx_db

from influxdb_client import Point

from private_info import city

# Eigen logger voor de meetwaarden (DEBUG); self.logger is de InverterLogger uit config.cfg.
detail_logger = logging.getLogger(__name__)


def e_total_precise(msg):
    """Totale opbrengst in kWh, met dezelfde resolutie (0,01 kWh) als de dagopbrengst.

    De inverter geeft e_total in stappen van 0,1 kWh en e_today in stappen van 0,01 kWh.
    Het deel van e_today onder de 0,1 kWh (bijv. 0,04 bij e_today = 3,64) wordt bij
    e_total opgeteld, zodat het totaal net zo fijn oploopt als de dagopbrengst.
    """
    below_tenth = (msg.e_today * 10 - int(msg.e_today * 10)) / 10
    return round(msg.e_total + below_tenth, 2)


class InfluxDBOutput(PluginLoader.Plugin):
    """Outputs the data from the inverter logger to InfluxDB"""

    # Grenzen voor onmogelijke waarden. Echte pieken van de panelen gaan tot ca. 2100 W.
    MAX_POWER = 3000     # W
    MAX_E_TODAY = 30     # kWh
    TEMP_RANGE = (-40, 100)  # °C

    def is_plausible(self, msg):
        p_ac, e_today, temp = msg.p_ac(1), msg.e_today, msg.temp
        ok = (0 <= p_ac <= self.MAX_POWER
              and 0 <= e_today <= self.MAX_E_TODAY
              and self.TEMP_RANGE[0] <= temp <= self.TEMP_RANGE[1])
        if not ok:
            self.logger.warning(
                'Onmogelijke waarden, niet weggeschreven: p_ac={0} e_today={1} temp={2} raw (len={3}): {4}'.format(
                    p_ac, e_today, temp, len(msg.raw_msg), bytes(msg.raw_msg).hex(':')))
        return ok

    def process_message(self, msg):
        if not self.is_plausible(msg):
            return

        e_total = e_total_precise(msg)
        data_point = [Point("solarpanel").tag("location", city).field("power", msg.p_ac(1)),
                      Point("solarpanel").tag("location", city).field("Temp", msg.temp),
                      Point("solarpanel").tag("location", city).field("power today", msg.e_today),
                      Point("solarpanel").tag("location", city).field("power total", e_total)
                      ]

        influx_db.write(data_point)

        if detail_logger.isEnabledFor(logging.DEBUG):
            detail_logger.debug('Inverter ID: %s', msg.id)
            detail_logger.debug('E Today : %s  Total: %s', msg.e_today, e_total)
            detail_logger.debug('H Total : %s   Temp : %s', msg.h_total, msg.temp)
            detail_logger.debug('errorMsg: %s', msg.errorMsg)
            for i in (1, 2, 3):
                detail_logger.debug('PV%s   V: %s   I: %s', i, msg.v_pv(i), msg.i_pv(i))
            for i in (1, 2, 3):
                detail_logger.debug('L%s    P: %s   V: %s   I: %s   F: %s',
                                    i, msg.p_ac(i), msg.v_ac(i), msg.i_ac(i), msg.f_ac(i))
