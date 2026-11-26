#!/usr/bin/python
"""InverterExport program.

Get data from a Wi-Fi kit logger and save/send the data to the defined plugin(s)
"""
import argparse
import configparser
import logging
import logging.config
import re
import socket  # Needed for talking to logger
import sys
import time

from PluginLoader import Plugin
import InverterMsg  # Import the Msg handler
import InverterLib  # Import the library


class InverterExport(object):
    """
    Get data from the inverter(s) and store the data in a configured output
    format/location.

    """

    config = None
    logger = None

    def __init__(self, config_file):
        # Load the setting
        config_files = [InverterLib.expand_path('config-default.cfg'),
                        InverterLib.expand_path(config_file)]

        self.config = configparser.RawConfigParser()
        self.config.read(config_files)

        # add command line option -p / --plugins to override the output plugins used
        # (parse_known_args: onbekende argumenten van het aanroepende programma negeren)
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', '--plugins', dest="plugins",
                            help="output plugins to use")

        self.options, self.args = parser.parse_known_args()

        # Eenmalige setup (logger en output-plugins); hoeft niet elke uitleesronde opnieuw.
        self.build_logger(self.config)
        self.load_plugins()

    def load_plugins(self):
        """Load the configured output plugins."""
        # Prepare path for plugin loading
        sys.path.append(InverterLib.expand_path('outputs'))

        Plugin.config = self.config
        Plugin.logger = self.logger

        enabled_plugins = self.config.get('general', 'enabled_plugins') \
            .split(',')

        # if -p / --plugin option giving at command line, override enabled plugins
        if self.options.plugins:
            enabled_plugins = self.options.plugins.split(',')

        for plugin_name in enabled_plugins:
            plugin_name = plugin_name.strip()
            self.logger.debug('Importing output plugin ' + plugin_name)
            __import__(plugin_name)

    def run(self):
        """Get information from inverter and store is configured outputs."""

        # Connect to logger
        if not self.config.has_option('logger', 'gateways'):
            self.logger.error('no gateways defined in configuration file, exiting.')
            return []

        if (self.config.get('logger', 'gateways') == 'auto'):
            # get loggers
            gateway_list = InverterLib.getLoggers().split(',')
            if (len(gateway_list) < 2):
                self.logger.error('No loggers found: {0}, exiting.'.format(gateway_list))
                return []
            self.logger.info('Loggers found  on the network: {0}.'.format(gateway_list))
        else:
            gateway_list = self.config.get('logger', 'gateways').split(',')
            if (len(gateway_list) % 2):
                self.logger.error(
                    'incorrect number of values in configuration file for gateways: {0}, exiting.'.format(gateway_list))
                return []

        for i in range(0, len(gateway_list), 2):
            ip = gateway_list[i]
            sn = gateway_list[i + 1]

            self.logger.info('Connecting to logger with IP: {0} and SN {1}'.format(ip, sn))

            port = self.config.get('logger', 'port')
            timeout = self.config.getfloat('logger', 'timeout')

            next = False
            for res in socket.getaddrinfo(ip, port, socket.AF_INET,
                                          socket.SOCK_STREAM):
                family, socktype, proto, canonname, sockadress = res
                try:
                    self.logger.info('connecting to {0} port {1}'.format(ip, port))
                    logger_socket = socket.socket(family, socktype, proto)
                    logger_socket.settimeout(timeout)
                    logger_socket.connect(sockadress)
                except socket.error as msg:
                    self.logger.error('Could not open socket')
                    self.logger.error(msg)
                    self.logger.error(
                        'Error connecting to logger with IP: {0} and SN {1}, trying next logger.'.format(ip, sn))
                    next = True
                    break
            if (next):
                continue

            data = InverterLib.createV4RequestFrame(int(sn))
            logger_socket.sendall(data)

            # dump raw data to log
            self.logger.debug('RAW sent Packet (len={0}): '.format(len(data)) + ':'.join(
                hex(ord(chr(x)))[2:].zfill(2) for x in bytearray(data)) + '  ' + re.sub('[^\x20-\x7f]', '', ''.join(
                chr(x) for x in bytearray(data))))

            # Per uitleesronde wordt maximaal één meetbericht verwerkt. Extra pakketten
            # die de logger daarna nog stuurt, worden alleen gelogd (met ruwe bytes),
            # niet weggeschreven: die gaven nep-pieken in InfluxDB.
            measured = False
            try:
                while True:
                    try:
                        data = logger_socket.recv(1024)
                    except socket.timeout:
                        if not measured:
                            self.logger.error(
                                'Timeout connecting to logger with IP: {0} and SN {1}, trying next logger.'.format(ip, sn))
                        break

                    if not data:  # logger heeft de verbinding gesloten
                        break

                    # dump raw data to log
                    self.logger.debug('RAW received Packet (len={0}): '.format(len(data)) + ':'.join(
                        hex(ord(chr(x)))[2:].zfill(2) for x in bytearray(data)) + '  ' + re.sub('[^\x20-\x7f]', '', ''.join(
                        chr(x) for x in bytearray(data))))

                    msg = InverterMsg.InverterMsg(data)

                    if len(data) > 12:
                        # log DATA length
                        self.logger.debug('DATA len={0}: '.format(msg.len))

                        if (msg.msg)[:9] == 'DATA SEND':
                            self.logger.debug("Exit Status: {0}".format(msg.msg))
                            break

                        if (msg.msg)[:11] == 'NO INVERTER':
                            self.logger.debug("Inverter(s) are in sleep mode: {0} received".format(msg.msg))
                            break

                    if measured or not self.looks_like_measurement(data):
                        self.logger.warning('Extra/onbekend pakket genegeerd (len={0}): {1}'.format(
                            len(data), data.hex(':')))
                        continue

                    self.logger.info("Inverter ID: {0}".format(msg.id))
                    if (msg.len > 140):
                        self.logger.info("Inverter main firmware version: {0}".format(msg.main_fwver))
                        self.logger.info("Inverter slave firmware version: {0}".format(msg.slave_fwver))
                    self.logger.info("RUN State: {0}".format(msg.run_state))

                    for plugin in Plugin.plugins:
                        self.logger.debug('Run plugin' + plugin.__class__.__name__)
                        plugin.process_message(msg)
                    measured = True
            finally:
                logger_socket.close()

    @staticmethod
    def looks_like_measurement(data):
        """Een meetbericht moet lang genoeg zijn voor alle velden (errorMsg staat op offset 93..96)."""
        return len(data) >= 97

    def build_logger(self, config):
        # Build logger
        """
        Build logger for this program


        Args:
            config: configparser with settings from file
        """
        log_levels = dict(notset=0, debug=10, info=20, warning=30, error=40, critical=50)
        log_dict = {
            'version': 1,
            # Laat loggers van de andere modules (realtimemonitoring, get_*) intact.
            'disable_existing_loggers': False,
            'formatters': {
                'f': {'format': '%(asctime)s %(levelname)s %(message)s'}
            },
            'handlers': {
                'none': {'class': 'logging.NullHandler'},
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'f'
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'filename': InverterLib.expand_path(config.get('log',
                                                                   'filename')),
                    # pas openen bij de eerste logregel: bij type = console wordt er geen
                    # (lege) logfile aangemaakt, en de app-map hoeft niet schrijfbaar te zijn
                    'delay': True,
                    'formatter': 'f'},
            },
            'loggers': {
                'InverterLogger': {
                    'handlers': config.get('log', 'type').split(','),
                    'level': log_levels[config.get('log', 'level')],
                    # Heeft eigen handlers; niet ook nog via de root-logger (dubbele regels).
                    'propagate': False,
                }
            }
        }
        logging.config.dictConfig(log_dict)
        self.logger = logging.getLogger('InverterLogger')

    def override_config(self, section, option, value):
        """Override config settings"""
        self.config.set(section, option, value)


if __name__ == "__main__":
    inverter_exporter = InverterExport('config.cfg')

    while True:
        inverter_exporter.run()
        time.sleep(60)
