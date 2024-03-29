import PluginLoader
import sys

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from private_info import city
from private_info import token
from private_info import org
from private_info import bucket
from private_info import DB_url
from private_info import logging_file


client2 = InfluxDBClient(url=DB_url, token=token)
write_api = client2.write_api(write_options=SYNCHRONOUS)


class InfluxDBOutput(PluginLoader.Plugin):
    """Outputs the data from the inverter logger to InfluxDB"""

    def process_message(self, msg):
        data_point = [Point("solarpanel").tag("location", city).field("power",msg.p_ac(1)),
                      Point("solarpanel").tag("location", city).field("Temp", msg.temp),
                      Point("solarpanel").tag("location", city).field("power today", msg.e_today),
                      Point("solarpanel").tag("location", city).field("power total",
                           ((((msg.e_today * 10) - (int(msg.e_today * 10))) / 10) + msg.e_total))
                      ]

        write_api.write(bucket=bucket, org=org, record=data_point)
        with open(logging_file, "a") as f:
            print(f'Inverter ID: {msg.id}', file=f)
            print(f'E Today : {msg.e_today}  Total: {((((msg.e_today * 10) - (int(msg.e_today * 10))) / 10) + msg.e_total)}', file=f)
            print(f'H Total : {msg.h_total}   Temp : {msg.temp}', file=f)
            print(f'errorMsg: {msg.errorMsg}', file=f)
            print(f'PV1   V: {msg.v_pv(1)}   I: {msg.i_pv(1)}', file=f)
            print(f'PV2   V: {msg.v_pv(2)}   I: {msg.i_pv(2)}', file=f)
            print(f'PV3   V: {msg.v_pv(3)}   I: {msg.i_pv(3)}', file=f)
            print(f'L1    P: {msg.p_ac(1)}   V: {msg.v_ac(1)}   I: {msg.i_ac(1)}   F: {msg.f_ac(1)}', file=f)
            print(f'L2    P: {msg.p_ac(2)}   V: {msg.v_ac(2)}   I: {msg.i_ac(2)}   F: {msg.f_ac(2)}', file=f)
            print(f'L3    P: {msg.p_ac(3)}   V: {msg.v_ac(3)}   I: {msg.i_ac(3)}   F: {msg.f_ac(3)}', file=f)

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
