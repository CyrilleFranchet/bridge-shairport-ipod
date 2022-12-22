#!/usr/bin/env python
# coding : utf-8

# Created by PyCharm on 14/08/2022
# Filename : ipod
import logging

from suitcase.protocol import StreamProtocolHandler

from lingo.lingo_base import LingoPacket

class IpodProtocolHandler:
    def __init__(self, stream, read_args=None, write_args=None):
        self.stream = stream
        self.handler = StreamProtocolHandler(LingoPacket, self.packet_received)
        self.running = False
        self.read_args = read_args or {}
        self.write_args = write_args or {}

    def run(self):
        """
        Read from the underlying stream and pass it to the packet handler, until `stop()` is called.
        """
        self.running = True

        while self.running:
            data = self.stream.read(**self.read_args)
            logging.debug(data)

            if len(data):
                self.handler.feed(data)

    def stop(self):
        """
        Stops reading data from the stream.
        """
        self.running = False

    def send_packet(self, packet: LingoPacket):
        """
        Packs and sends an LingoPacket over the underlying stream.
        :param packet: The packet to pack and send.
        """
        self.stream.write(packet.pack(), **self.write_args)

    def packet_received(self, packet: LingoPacket):
        """
        Called when a fully-formed packet is received from the underlying data stream.
        :param packet: The packet that was received.
        """
        pass