#!/usr/bin/env python
# coding : utf-8

import serial
import os
import time
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import logging
import threading
import signal

import lingo

DBusGMainLoop(set_as_default=True)
port = '/dev/ttyS0'
os.environ['DISPLAY'] = ':1'


class BridgeShutdown(Exception):
    pass


class Bridge(lingo.IpodProtocolHandler):
    """
    Used for client devices that wish to emulate an iPod in order to interface with an accessory.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pick some random ipod type to begin with
        #self.ipod_type = IPOD_TYPE_GEN5_30GB

        # Default iPod name
        self.ipod_name = "Bridge"

        self.target_playlist = 0

        self.screen_size = (310, 168)

        self.notifications = False
        self.database = {}
        self.trackid = None
        self.extended_interface = False

        self.system_bus = dbus.SystemBus()
        self.shairport = self.system_bus.get_object('org.mpris.MediaPlayer2.ShairportSync', '/org/mpris/MediaPlayer2')
        self.player_manager = dbus.Interface(self.shairport, 'org.mpris.MediaPlayer2.Player')
        self.properties_manager = dbus.Interface(self.shairport, 'org.freedesktop.DBus.Properties')

        self.playing = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')

        logging.basicConfig(filename='/home/pi/bridge-shairport.log',
                            encoding='utf-8',
                            #filemode='',
                            level=logging.DEBUG,
                            format='%(asctime)s,%(name)s,%(levelname)s,%(message)s',
                            force=True)
        self.logger = logging.getLogger('bridge-shairport')

        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        self.poller_thread = threading.Thread(target=self.poller)
        self.shutdown_flag = threading.Event()
        self.play_control_available = threading.Semaphore()
        self.poller_thread.start()
        

    def shutdown(self, signal_number, frame):
        raise BridgeShutdown


    def update_database(self):
        metadata = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        if 'mpris:trackid' in metadata:
            trackid = metadata['mpris:trackid'].split('/')[-1]
            if trackid not in self.database:
                if not self.database:
                    index = 1
                else:
                    index = max(self.database.values())+1
                self.database[trackid] = index
            if self.trackid != trackid:
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.PlayStatusChangeNotification()
                res.lingo_type.payload.new_play_status = b'\x01'+self.database[trackid].to_bytes(4, 'big')
                self.trackid = trackid

                logger.debug(res)
                self.send_packet(res)
                logger.info('Sent|ExtendedInterfaceLingo|PlayStatusChangeNotification|Index|%d' %
                            self.database[trackid])

    def poller(self):
        self.logger.info('Starting poller thread')
        while not self.shutdown_flag.is_set():
            time.sleep(0.01)
            if self.extended_interface and self.notifications:
                self.play_control_available.acquire()
                self.update_database()
                self.play_control_available.release()

                self.play_control_available.acquire()
                playing = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
                if self.playing != playing:
                    self.playing = playing
                    res = lingo.LingoPacket()
                    res.lingo_type = lingo.ExtendedInterfaceLingo()
                    res.lingo_type.payload = lingo.PlayStatusChangeNotification()
                    if playing == 'Playing':
                        res.lingo_type.payload.new_play_status = b'\x06\x0A'
                    elif playing == 'Paused':
                        res.lingo_type.payload.new_play_status = b'\x06\x0B'
                    elif playing == 'Stopped':
                        res.lingo_type.payload.new_play_status = b'\x06\x02'

                    logger.debug(res)
                    self.send_packet(res)
                    logger.info('Sent|ExtendedInterfaceLingo|PlayStatusChangeNotification|PlaybackStatus|%s' % playing)
                self.play_control_available.release()
        self.logger.info('Stopping poller thread')


    def packet_received(self, packet: lingo.LingoPacket):
        self.logger.debug(packet)

        if isinstance(packet.lingo_type, lingo.GeneralLingo):
            if isinstance(packet.lingo_type.payload, lingo.IdentifyDeviceLingoes):
                self.logger.info('Received|GeneralLingo|IdentifyDeviceLingoes')
                res = lingo.LingoPacket()
                res.lingo_type = lingo.GeneralLingo()
                res.lingo_type.payload = lingo.GeneralACK()
                res.lingo_type.payload.command_result_status = 0x00
                res.lingo_type.payload.command_id_acknowledge = 0x13
                print(res)
                self.send_packet(res)

                res = lingo.LingoPacket()
                res.lingo_type = lingo.GeneralLingo()
                res.lingo_type.payload = lingo.GetAccessoryInfo()
                res.lingo_type.payload.accessory_info_type = lingo.ACCESSORY_INFO_TYPE_inv['ACCESSORY_NAME']
                print(res)
                self.send_packet(res)
            elif isinstance(packet.lingo_type.payload, lingo.RetAccessoryInfo):
                self.logger.info('Received|GeneralLingo|RetAccessoryInfo')

        elif isinstance(packet.lingo_type, lingo.SimpleRemoteLingo):
            if isinstance(packet.lingo_type.payload, lingo.ContextButtonStatus):
                button_bytes = packet.lingo_type.payload.button_bytes_string
                if button_bytes == 'NEXT_TRACK':
                    self.player_manager.Next()
                elif button_bytes == 'PREVIOUS_TRACK':
                    self.player_manager.Previous()
                elif button_bytes == 'PLAY_PAUSE':
                    self.player_manager.PlayPause()
                elif button_bytes in ('POWER_OFF', 'STOP'):
                    self.player_manager.Stop()
                elif button_bytes == 'SHUFFLE_SETTING_ADVANCE':
                    shuffle_status = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Shuffle')
                    if shuffle_status:
                        self.properties_manager.Set('org.mpris.MediaPlayer2.Player', 'Shuffle', False)
                    else:
                        self.properties_manager.Set('org.mpris.MediaPlayer2.Player', 'Shuffle', True)
                elif button_bytes == 'REPEAT_SETTING_ADVANCE':
                    repeat_status = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'LoopStatus')
                    if repeat_status == 'None':
                        self.properties_manager.Set('org.mpris.MediaPlayer2.Player', 'LoopStatus', 'Track')
                    elif repeat_status == 'Track':
                        self.properties_manager.Set('org.mpris.MediaPlayer2.Player', 'LoopStatus', 'Playlist')
                    elif repeat_status == 'Playlist':
                        self.properties_manager.Set('org.mpris.MediaPlayer2.Player', 'LoopStatus', 'None')
                self.logger.info('Received|SimpleRemoteLingo|ContextButtonStatus|%s' % button_bytes)

        elif isinstance(packet.lingo_type, lingo.ExtendedInterfaceLingo):
            if isinstance(packet.lingo_type.payload, lingo.RequestProtocolVersion):
                self.logger.info('Received|ExtendedInterfaceLingo|RequestProtocolVersion')
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ReturnProtocolVersion()
                res.lingo_type.payload.protocol_major_version = 0x01
                res.lingo_type.payload.protocol_minor_version = 0x09

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ReturnProtocolVersion|1.09')

            elif isinstance(packet.lingo_type.payload, lingo.GetPlayStatus):
                self.logger.info('Received|ExtendedInterfaceLingo|GetPlayStatus')
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ReturnPlayStatus()
                self.extended_interface = True

                player_status = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
                if player_status == 'Playing':
                    player_state = lingo.PLAYER_STATE_inv['PLAYING']
                elif player_status == 'Paused':
                    player_state = lingo.PLAYER_STATE_inv['PAUSED']
                elif player_status == 'Stopped':
                    player_state = lingo.PLAYER_STATE_inv['STOPPED']
                else:
                    player_state = lingo.PLAYER_STATE_inv['ERROR']
                res.lingo_type.payload.player_state = player_state

                metadata = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
                if 'mpris:length' in metadata:
                    length = metadata['mpris:length']
                    track_length = round(length/1000)
                else:
                    track_length = 0
                res.lingo_type.payload.track_length = track_length

                position = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Position')
                track_position = round(position/1000)
                res.lingo_type.payload.track_position = track_position

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('ExtendedInterfaceLingo|ReturnPlayStatus|%s|%d|%d' % (player_state, track_length,
                                                                                       track_position))

            elif isinstance(packet.lingo_type.payload, lingo.GetNumberCategorizedDBRecords):
                database_category = packet.lingo_type.payload.database_category_string
                self.logger.info('Received|ExtendedInterfaceLingo|GetNumberCategorizedDBRecords|%s' % database_category)
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ReturnNumberCategorizedDBRecords()

                if database_category == 'PLAYLIST':
                    database_record_count = 1
                elif database_category == 'ARTIST':
                    database_record_count = 10
                elif database_category == 'TRACK':
                    database_record_count = 10000
                elif database_category == 'ALBUM':
                    database_record_count = 10
                res.lingo_type.payload.database_record_count = database_record_count

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ReturnNumberCategorizedDBRecords|%d' %
                                 database_record_count)

            elif isinstance(packet.lingo_type.payload, lingo.GetCurrentPlayingTrackIndex):
                self.logger.info('Received|ExtendedInterfaceLingo|GetCurrentPlayingTrackIndex')
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ReturnCurrentPlayingTrackIndex()

                player_status = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
                if player_status == 'Playing' :
                    playback_track_index = self.database[self.trackid]
                else:
                    playback_track_index = -1
                res.lingo_type.payload.playback_track_index = playback_track_index

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ReturnCurrentPlayingTrackIndex|%d' % playback_track_index)

            elif isinstance(packet.lingo_type.payload, lingo.GetIndexedPlayingTrackAlbumName):
                playback_track_index = packet.lingo_type.payload.playback_track_index
                self.logger.info('Received|ExtendedInterfaceLingo|GetIndexedPlayingTrackAlbumName|%d' %
                                 playback_track_index)
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ReturnIndexedPlayingTrackAlbumName()

                metadata = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
                res.lingo_type.payload.album_name = lingo.StringField()
                if 'xesam:album' in metadata:
                    album = str(metadata['xesam:album'])
                    album_name = album
                else:
                    album_name = ''
                res.lingo_type.payload.album_name.text = album_name

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ReturnCurrentPlayingTrackIndex|%s' % album_name)

            elif isinstance(packet.lingo_type.payload, lingo.GetIndexedPlayingTrackArtistName):
                playback_track_index = packet.lingo_type.payload.playback_track_index
                self.logger.info('Received|ExtendedInterfaceLingo|GetIndexedPlayingTrackArtistName|%d' %
                                 playback_track_index)
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ReturnIndexedPlayingTrackArtistName()

                metadata = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
                res.lingo_type.payload.artist_name = lingo.StringField()
                if 'xesam:artist' in metadata:
                    artist = str(metadata['xesam:artist'][0])
                    artist_name = artist
                else:
                    artist_name = ''
                res.lingo_type.payload.artist_name.text = artist_name

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ReturnIndexedPlayingTrackArtistName|%s' % artist_name)

            elif isinstance(packet.lingo_type.payload, lingo.GetIndexedPlayingTrackTitle):
                playback_track_index = packet.lingo_type.payload.playback_track_index
                self.logger.info('Received|ExtendedInterfaceLingo|GetIndexedPlayingTrackTitle|%d' %
                                 playback_track_index)
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ReturnIndexedPlayingTrackTitle()

                metadata = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
                res.lingo_type.payload.title = lingo.StringField()
                if 'xesam:title' in metadata:
                    title = str(metadata['xesam:title'])
                    title_song = title
                else:
                    title_song = ''
                res.lingo_type.payload.title.text = title_song

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ReturnIndexedPlayingTrackTitle|%s' % title_song)

            elif isinstance(packet.lingo_type.payload, lingo.PlayControl):
                control_command = packet.lingo_type.payload.play_control_command_string
                self.logger.info('Received|ExtendedInterfaceLingo|PlayControl|%s' % control_command)
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ACK()
                res.lingo_type.payload.command_result_status = lingo.COMMAND_RESULT_STATUS_inv['SUCCESS']
                res.lingo_type.payload.command_id_acknowledge = 0x0029
                if control_command == 'TOGGLE_PLAY_PAUSE':
                    self.play_control_available.acquire()
                    self.playing = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
                    self.player_manager.PlayPause()
                    playing = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
                    while playing == self.playing:
                        time.sleep(0.01)
                        playing = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
                    self.playing = playing
                    self.play_control_available.release()
                elif control_command == 'NEXT_TRACK':
                    self.play_control_available.acquire()
                    self.player_manager.Next()
                    self.update_database()
                    self.play_control_available.release()
                elif control_command == 'PREVIOUS_TRACK':
                    self.play_control_available.acquire()
                    self.player_manager.Previous()
                    self.update_database()
                    self.play_control_available.release()

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ACK')


            elif isinstance(packet.lingo_type.payload, lingo.ResetDBSelection):
                self.logger.info('Received|ExtendedInterfaceLingo|ResetDBSelection')
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ACK()
                res.lingo_type.payload.command_result_status = lingo.COMMAND_RESULT_STATUS_inv['SUCCESS']
                res.lingo_type.payload.command_id_acknowledge = 0x0016
                self.database = {}

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ACK')

            elif isinstance(packet.lingo_type.payload, lingo.PlayCurrentSelection):
                selection_track_record_index = packet.lingo_type.payload.selection_track_record_index
                self.logger.info('Received|ExtendedInterfaceLingo|PlayCurrentSelection|%d' %
                                 selection_track_record_index)
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ACK()
                if selection_track_record_index not in self.database.values():
                    command_result_status = lingo.COMMAND_RESULT_STATUS_inv['ERROR_BAD_PARAMETER']
                else:
                    command_result_status = lingo.COMMAND_RESULT_STATUS_inv['SUCCESS']
                res.lingo_type.payload.command_result_status = command_result_status
                res.lingo_type.payload.command_id_acknowledge = 0x0028
                self.player_manager.Play()
                time.sleep(1)

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ACK')

            elif isinstance(packet.lingo_type.payload, lingo.SetRepeat):
                new_repeat_state = packet.lingo_type.payload.new_repeat_state_string
                self.logger.info('Received|ExtendedInterfaceLingo|SetRepeat|%s' % new_repeat_state)
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ACK()
                res.lingo_type.payload.command_result_status = lingo.COMMAND_RESULT_STATUS_inv['SUCCESS']
                res.lingo_type.payload.command_id_acknowledge = 0x0031
                if new_repeat_state == 'REPEAT_OFF':
                    state = 'None'
                    self.properties_manager.Set('org.mpris.MediaPlayer2.Player', 'LoopStatus', state)
                elif new_repeat_state == 'REPEAT_ONE_TRACK':
                    state = 'Track'
                    self.properties_manager.Set('org.mpris.MediaPlayer2.Player', 'LoopStatus', state)
                elif new_repeat_state == 'REPEAT_ALL_TRACKS':
                    state = 'Playlist'
                    self.properties_manager.Set('org.mpris.MediaPlayer2.Player', 'LoopStatus', state)
                repeat_state = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'LoopStatus')
                while repeat_state != state:
                    time.sleep(0.01)
                    repeat_state = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'LoopStatus')

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ACK')

            elif isinstance(packet.lingo_type.payload, lingo.GetRepeat):
                self.logger.info('Received|ExtendedInterfaceLingo|GetRepeat')
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ReturnRepeat()
                repeat_status = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'LoopStatus')
                if repeat_status == 'None':
                    repeat_state = lingo.REPEAT_STATE_inv['REPEAT_OFF']
                elif repeat_status == 'Track':
                    repeat_state = lingo.REPEAT_STATE_inv['REPEAT_ONE_TRACK']
                elif repeat_status == 'Playlist':
                    repeat_state = lingo.REPEAT_STATE_inv['REPEAT_ALL_TRACKS']
                res.lingo_type.payload.repeat_state = repeat_state

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ReturnRepeat|%d' % repeat_state)

            elif isinstance(packet.lingo_type.payload, lingo.SetShuffle):
                new_shuffle_state = packet.lingo_type.payload.new_shuffle_state_string
                self.logger.info('Received|ExtendedInterfaceLingo|SetShuffle|%s' % new_shuffle_state)
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ACK()
                res.lingo_type.payload.command_result_status = lingo.COMMAND_RESULT_STATUS_inv['SUCCESS']
                res.lingo_type.payload.command_id_acknowledge = 0x002E
                if new_shuffle_state == 'SHUFFLE_OFF':
                    state = False
                    self.properties_manager.Set('org.mpris.MediaPlayer2.Player', 'Shuffle', state)
                elif new_shuffle_state == 'SHUFFLE_TRACKS':
                    state = True
                    self.properties_manager.Set('org.mpris.MediaPlayer2.Player', 'Shuffle', state)
                elif new_shuffle_state == 'SHUFFLE_ALBUMS':
                    state = True
                    self.properties_manager.Set('org.mpris.MediaPlayer2.Player', 'Shuffle', state)
                shuffle_state = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Shuffle')
                while shuffle_state != state:
                    time.sleep(0.01)
                    shuffle_state = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Shuffle')

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ACK')

            elif isinstance(packet.lingo_type.payload, lingo.GetShuffle):
                self.logger.info('Received|ExtendedInterfaceLingo|GetShuffle')
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ReturnShuffle()
                current_shuffle_mode = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Shuffle')
                if current_shuffle_mode:
                    shuffle_mode = lingo.SHUFFLE_STATE_inv['SHUFFLE_TRACKS']
                else:
                    shuffle_mode = lingo.SHUFFLE_STATE_inv['SHUFFLE_OFF']
                res.lingo_type.payload.shuffle_mode = shuffle_mode

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ReturnShuffle|%d' % shuffle_mode)

            elif isinstance(packet.lingo_type.payload, lingo.SetPlayStatusChangeNotification):
                enable_notifications = packet.lingo_type.payload.enable_notifications
                self.logger.info('Received|ExtendedInterfaceLingo|SetPlayStatusChangeNotification|%d' %
                                 enable_notifications)
                res = lingo.LingoPacket()
                res.lingo_type = lingo.ExtendedInterfaceLingo()
                res.lingo_type.payload = lingo.ACK()
                res.lingo_type.payload.command_result_status = lingo.COMMAND_RESULT_STATUS_inv['SUCCESS']
                res.lingo_type.payload.command_id_acknowledge = 0x0026
                if enable_notifications:
                    self.notifications = True
                else:
                    self.notifications = False

                self.logger.debug(res)
                self.send_packet(res)
                self.logger.info('Sent|ExtendedInterfaceLingo|ACK')

            else:
                self.logger.info('Received|ExtendedInterfaceLingo|UNKNOWN')

logger = logging.getLogger('bridge-shairport')


# We need to detect the baud rate
second_magic = False
while not second_magic:
    for baud_rate in [9600, 19200]:
        logger.debug('Trying baud rate', baud_rate)
        with serial.Serial(port, baud_rate) as serial_port:
            tries = 30
            first_magic = False
            second_magic = False
            while tries > 0:
                tries -= 1
                byte = serial_port.read(1)
                if byte == b'\xFF':
                    first_magic = True
                elif byte == b'\x55' and first_magic:
                    second_magic = True
            if second_magic:
                break

with serial.Serial(port, baud_rate) as serial_port:
    try:
        ipod = Bridge(serial_port)
        logger.info('Starting Bridge')
        logger.info('Baud rate is %d' % baud_rate)
        print('Started')
        ipod.run()
    except BridgeShutdown:
        ipod.shutdown_flag.set()
        ipod.poller_thread.join()