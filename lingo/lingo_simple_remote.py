#!/usr/bin/env python
# coding : utf-8

# Created by PyCharm on 14/08/2022
# Filename : lingo_simple_remote

from suitcase.structure import Structure
from suitcase.fields import UBInt8, UBInt16, UBInt32, SBInt32, UBInt8Sequence, SBInt32, \
    Magic, LengthField, DispatchField, DispatchTarget, FieldProperty, Payload, CRCField, DependentField, \
    ConditionalField, BitField, BitNum, SubstructureField, BitBool, TypeField

BUTTON_STATUS = {
    b'\x00': 'NO_BUTTON',
    b'\x01': 'PLAY_PAUSE',
    b'\x02': 'VOLUME_UP',
    b'\x04': 'VOLUME_DOWN',
    b'\x08': 'NEXT_TRACK',
    b'\x10': 'PREVIOUS_TRACK',
    b'\x20': 'NEXT_ALBUM',
    b'\x40': 'PREVIOUS_ALBUM',
    b'\x80': 'STOP',
    b'\x00\x01': 'PLAY_RESUME',
    b'\x00\x02': 'PAUSE',
    b'\x00\x04': 'MUTE_TOGGLE',
    b'\x00\x08': 'NEXT_CHAPTER',
    b'\x00\x10': 'PREVIOUS_CHAPTER',
    b'\x00\x20': 'NEXT_PLAYLIST',
    b'\x00\x40': 'PREVIOUS_PLAYLIST',
    b'\x00\x80': 'SHUFFLE_SETTING_ADVANCE',
    b'\x00\x00\x01': 'REPEAT_SETTING_ADVANCE',
    b'\x00\x00\x02': 'POWER_ON',
    b'\x00\x00\x04': 'POWER_OFF',
    b'\x00\x00\x08': 'BACKLIGHT_30_SECS',
    b'\x00\x00\x10': 'BEGIN_FAST_FORWARD',
    b'\x00\x00\x20': 'BEGIN_REWIND',
    b'\x00\x00\x40': 'MENU',
    b'\x00\x00\x80': 'SELECT',
    b'\x00\x00\x00\x01': 'UP_ARROW',
    b'\x00\x00\x00\x02': 'DOWN_ARROW',
}
BUTTON_STATUS_inv = {v: k for k,v in BUTTON_STATUS.items()}


class ContextButtonStatus(Structure):
    button_bytes = Payload()
    button_bytes_string = FieldProperty(button_bytes, onget=lambda m: "%s" % (BUTTON_STATUS[m.rstrip(b'\x00')] if m != b'\x00\x00\x00\x00' else BUTTON_STATUS[b'\x00']))


class SimpleRemoteLingo(Structure):
    command = DispatchField(UBInt8())
    payload = DispatchTarget(length_provider=None, dispatch_field=command, dispatch_mapping={
        0x00: ContextButtonStatus,
        #0x01: CatchAll,
        #0x02: CatchAll,
        #0x03: CatchAll,
        #0x04: CatchAll,
        #0x0D: CatchAll,
        #0x0E: CatchAll,
    })