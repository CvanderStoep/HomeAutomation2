import logging

import PluginLoader

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from private_info import city
from private_info import token
from private_info import org
from private_info import bucket
from private_info import DB_url

# Eigen logger voor de meetwaarden (DEBUG); self.logger is de InverterLogger uit config.cfg.
detail_logger = logging.getLogger(__name__)


client2 = InfluxDBClient(url=DB_url, token=token)
write_api = client2.write_api(write_options=SYNCHRONOUS)


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

        data_point = [Point("solarpanel").tag("location", city).field("power",msg.p_ac(1)),
                      Point("solarpanel").tag("location", city).field("Temp", msg.temp),
                      Point("solarpanel").tag("location", city).field("power today", msg.e_today),
                      Point("solarpanel").tag("location", city).field("power total",
                           ((((msg.e_today * 10) - (int(msg.e_today * 10))) / 10) + msg.e_total))
                      ]

        write_api.write(bucket=bucket, org=org, record=data_point)
        if detail_logger.isEnabledFor(logging.DEBUG):
            detail_logger.debug('Inverter ID: %s', msg.id)
            detail_logger.debug('E Today : %s  Total: %s', msg.e_today,
                                ((((msg.e_today * 10) - (int(msg.e_today * 10))) / 10) + msg.e_total))
            detail_logger.debug('H Total : %s   Temp : %s', msg.h_total, msg.temp)
            detail_logger.debug('errorMsg: %s', msg.errorMsg)
            for i in (1, 2, 3):
                detail_logger.debug('PV%s   V: %s   I: %s', i, msg.v_pv(i), msg.i_pv(i))
            for i in (1, 2, 3):
                detail_logger.debug('L%s    P: %s   V: %s   I: %s   F: %s',
                                    i, msg.p_ac(i), msg.v_ac(i), msg.i_ac(i), msg.f_ac(i))

        # sys.stdout.write('Inverter ID: {0}\n'.format(msg.id))
        # sys.stdout.write('E Today : {0:>5}   Total: {1:<5}\n'.format(msg.e_today, (
        #         (((msg.e_today * 10) - (int(msg.e_today * 10))) / 10) + msg.e_total)))
        # sys.stdout.write('E Today : {}   Total2: {}\n'.format(msg.e_today,  msg.e_total))

        # sys.stdout.write('H Total : {0:>5}   Temp : {1:<5}\n'.format(msg.h_total, msg.temp))
        # sys.stdout.write('errorMsg: {0:>5}\n'.format(msg.errorMsg))

        # sys.stdout.write('PV1   V: {0:>5}   I: {1:>4}\n'.format(msg.v_pv(1), msg.i_pv(1)))
        # sys.stdout.write('PV2   V: {0:>5}   I: {1:>4}\n'.format(msg.v_pv(2), msg.i_pv(2)))
        # sys.stdout.write('PV3   V: {0:>5}   I: {1:>4}\n'.format(msg.v_pv(3), msg.i_pv(3)))

        # sys.stdout.write(
        #     'L1    P: {0:>5}   V: {1:>5}   I: {2:>4}   F: {3:>5}\n'.format(msg.p_ac(1), msg.v_ac(1), msg.i_ac(1),
        #                                                                    msg.f_ac(1)))
        # sys.stdout.write(
        #     'L2    P: {0:>5}   V: {1:>5}   I: {2:>4}   F: {3:>5}\n'.format(msg.p_ac(2), msg.v_ac(2), msg.i_ac(2),
        #                                                                    msg.f_ac(2)))
        # sys.stdout.write(
        #     'L3    P: {0:>5}   V: {1:>5}   I: {2:>4}   F: {3:>5}\n'.format(msg.p_ac(3), msg.v_ac(3), msg.i_ac(3),
        #                                                                    msg.f_ac(3)))
