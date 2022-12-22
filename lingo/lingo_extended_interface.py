#!/usr/bin/env python
# coding : utf-8

# Created by PyCharm on 14/08/2022
# Filename : lingo_extended_interface

from suitcase.structure import Structure
from suitcase.fields import UBInt8, UBInt16, UBInt32, SBInt32, UBInt8Sequence, SBInt32, \
    Magic, LengthField, DispatchField, DispatchTarget, FieldProperty, Payload, CRCField, DependentField, \
    ConditionalField, BitField, BitNum, SubstructureField, BitBool, TypeField

from lingo.lingo_base import StringField

COMMAND_RESULT_STATUS = {
    0x00: 'SUCCESS',
    0x01: 'ERROR_UNKNOWN_DATABASE_CATEGORY',
    0x02: 'ERROR_COMMAND_FAILED',
    0x03: 'ERROR_OUT_OF_RESOURCES',
    0x04: 'ERROR_BAD_PARAMETER',
    0x05: 'ERROR_UNKNOWN_ID',
    0x06: 'RESERVED',
    0x07: 'ACCESSORY_NOT_AUTHENTICATED'
}
COMMAND_RESULT_STATUS_inv = {v: k for k,v in COMMAND_RESULT_STATUS.items()}

DATABASE_CATEGORY = {
    0x00: 'RESERVED',
    0x01: 'PLAYLIST',
    0x02: 'ARTIST',
    0x03: 'ALBUM',
    0x04: 'GENRE',
    0x05: 'TRACK',
    0x06: 'COMPOSER',
    0x07: 'AUDIOBOOK',
    0x08: 'PODCAST',
    0x09: 'NESTED_PLAYLIST'
}
DATABASE_CATEGORY_inv = {v: k for k,v in DATABASE_CATEGORY.items()}

PLAYER_STATE = {
    0x00: 'STOPPED',
    0x01: 'PLAYING',
    0x02: 'PAUSED',
    0xFF: 'ERROR'
}
PLAYER_STATE_inv = {v: k for k,v in PLAYER_STATE.items()}

PLAY_CONTROL_COMMAND = {
    0x00: 'RESERVED',
    0x01: 'TOGGLE_PLAY_PAUSE',
    0X02: 'STOP',
    0x03: 'NEXT_TRACK',
    0x04: 'PREVIOUS_TRACK',
    0x05: 'START_FF',
    0x06: 'START_REW',
    0x07: 'END_FF_REW'
}
PLAY_CONTROL_COMMAND_inv = {v: k for k,v in PLAY_CONTROL_COMMAND.items()}

REPEAT_STATE = {
    0x00: 'REPEAT_OFF',
    0x01: 'REPEAT_ONE_TRACK',
    0x02: 'REPEAT_ALL_TRACKS'
}
REPEAT_STATE_inv = {v: k for k,v in REPEAT_STATE.items()}

SHUFFLE_STATE = {
    0x00: 'SHUFFLE_OFF',
    0x01: 'SHUFFLE_TRACKS',
    0x02: 'SHUFFLE_ALBUMS'
}
SHUFFLE_STATE_inv = {v: k for k,v in SHUFFLE_STATE.items()}

class ACK(Structure):
    command_result_status = UBInt8()
    command_id_acknowledge = UBInt16()


class RequestProtocolVersion(Structure):
    pass


class ReturnProtocolVersion(Structure):
    protocol_major_version = UBInt8()
    protocol_minor_version = UBInt8()


class ResetDBSelection(Structure):
    pass


class GetNumberCategorizedDBRecords(Structure):
    database_category = UBInt8()
    database_category_string = FieldProperty(database_category, onget=lambda m: "%s" % DATABASE_CATEGORY[m])


class ReturnNumberCategorizedDBRecords(Structure):
    database_record_count = UBInt32()


class GetPlayStatus(Structure):
    pass


class ReturnPlayStatus(Structure):
    track_length = UBInt32()
    track_position = UBInt32()
    player_state = UBInt8()
    player_state_string = FieldProperty(player_state, onget=lambda m: "%s" % PLAYER_STATE[m])


class GetCurrentPlayingTrackIndex(Structure):
    pass


class ReturnCurrentPlayingTrackIndex(Structure):
    playback_track_index = SBInt32()


class GetIndexedPlayingTrackTitle(Structure):
    playback_track_index = SBInt32()


class ReturnIndexedPlayingTrackTitle(Structure):
    title = SubstructureField(StringField)


class GetIndexedPlayingTrackArtistName(Structure):
    playback_track_index = SBInt32()


class ReturnIndexedPlayingTrackArtistName(Structure):
    artist_name = SubstructureField(StringField)


class GetIndexedPlayingTrackAlbumName(Structure):
    playback_track_index = SBInt32()


class ReturnIndexedPlayingTrackAlbumName(Structure):
    album_name = SubstructureField(StringField)


class SetPlayStatusChangeNotification(Structure):
    enable_notifications = UBInt8()


class PlayStatusChangeNotification(Structure):
    new_play_status = Payload()


class PlayCurrentSelection(Structure):
    selection_track_record_index = SBInt32()


class PlayControl(Structure):
    play_control_command = UBInt8()
    play_control_command_string = FieldProperty(play_control_command, onget=lambda m: "%s" % PLAY_CONTROL_COMMAND[m])


class GetShuffle(Structure):
    pass


class ReturnShuffle(Structure):
    shuffle_mode = UBInt8()
    shuffle_mode_string = FieldProperty(shuffle_mode, onget=lambda m: "%s" % SHUFFLE_STATE[m])


class SetShuffle(Structure):
    new_shuffle_state = UBInt8()
    new_shuffle_state_string = FieldProperty(new_shuffle_state, onget=lambda m: "%s" % SHUFFLE_STATE[m])


class GetRepeat(Structure):
    pass


class ReturnRepeat(Structure):
    repeat_state = UBInt8()
    repeat_state_string = FieldProperty(repeat_state, onget=lambda m: "%s" % REPEAT_STATE[m])


class SetRepeat(Structure):
    new_repeat_state = UBInt8()
    new_repeat_state_string = FieldProperty(new_repeat_state, onget=lambda m: "%s" % REPEAT_STATE[m])


class SetDisplayImage(Structure):
    pass


class GetMonoDisplayImageLimits(Structure):
    pass


class ReturnMonoDisplayImageLimits(Structure):
    pass


class ExtendedInterfaceLingo(Structure):
    command = UBInt16()
    payload = DispatchTarget(length_provider=None, dispatch_field=command, dispatch_mapping={
        0x0001: ACK,
        0x0012: RequestProtocolVersion,
        0x0013: ReturnProtocolVersion,
        0x0016: ResetDBSelection,
        0x0018: GetNumberCategorizedDBRecords,
        0x0019: ReturnNumberCategorizedDBRecords,
        0x001C: GetPlayStatus,
        0x001D: ReturnPlayStatus,
        0x001E: GetCurrentPlayingTrackIndex,
        0x001F: ReturnCurrentPlayingTrackIndex,
        0x0020: GetIndexedPlayingTrackTitle,
        0x0021: ReturnIndexedPlayingTrackTitle,
        0x0022: GetIndexedPlayingTrackArtistName,
        0x0023: ReturnIndexedPlayingTrackArtistName,
        0x0024: GetIndexedPlayingTrackAlbumName,
        0x0025: ReturnIndexedPlayingTrackAlbumName,
        0x0026: SetPlayStatusChangeNotification,
        0x0027: PlayStatusChangeNotification,
        0x0028: PlayCurrentSelection,
        0x0029: PlayControl,
        0x002C: GetShuffle,
        0x002D: ReturnShuffle,
        0x002E: SetShuffle,
        0x002F: GetRepeat,
        0x0030: ReturnRepeat,
        0x0031: SetRepeat,
        0x0032: SetDisplayImage,
        0x0033: GetMonoDisplayImageLimits,
        0x0034: ReturnMonoDisplayImageLimits,
    })