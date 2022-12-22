#!/usr/bin/env python
# coding : utf-8

# Created by PyCharm on 14/08/2022
# Filename : lingo_base

from suitcase.structure import Structure
from suitcase.fields import UBInt8, UBInt16, UBInt32, SBInt32, UBInt8Sequence, SBInt32, \
    Magic, LengthField, DispatchField, DispatchTarget, FieldProperty, Payload, CRCField, DependentField, \
    ConditionalField, BitField, BitNum, SubstructureField, BitBool, TypeField


LINGOS = {
    0x00: 'GENERAL_LINGO',
    0X01: 'MICROPHONE_LINGO',
    0X02: 'SIMPLE_REMOTE_LINGO',
    0X03: 'DISPLAY_REMOTE_LINGO',
    0X04: 'EXTENDED_INTERFACE_LINGO',
    0X05: 'ACCESSORY_POWER_LINGO',
    0X07: 'RF_TUNER_LINGO',
    0X08: 'ACCESSORY_EQUALIZER_LINGO',
    0X09: 'SPORTS_LINGO',
    0X0A: 'DIGITAL_AUDIO_LINGO',
    0X0C: 'STORAGE_LINGO',
    0X0E: 'LOCATION_LINGO'
}

def ipod_checksum(data, crc=0):
    return 0x100 - (sum(data) & 0xFF) - crc


class CatchAll(Structure):
    data = Payload()


class StringField(Structure):
    data = Payload()
    text = FieldProperty(data, onget=lambda v: v.decode('utf-8'), onset=lambda v: v.encode('utf-8'))
    terminator = Magic(b'\x00')


from lingo.lingo_general import GeneralLingo
from lingo.lingo_microphone import MicrophoneLingo
from lingo.lingo_simple_remote import SimpleRemoteLingo
from lingo.lingo_display_remote import DisplayRemoteLingo
from lingo.lingo_extended_interface import ExtendedInterfaceLingo
from lingo.lingo_accessory_power import AccessoryPowerLingo
from lingo.lingo_rf_tuner import RFTunerLingo
from lingo.lingo_accessory_equalizer import AccessoryEqualizerLingo
from lingo.lingo_sports import SportsLingo
from lingo.lingo_digital_audio import DigitalAudioLingo
from lingo.lingo_storage import StorageLingo
from lingo.lingo_location import LocationLingo

class LingoPacket(Structure):
    header = Magic(b'\xFF\x55')
    payload_length = LengthField(UBInt8(), get_length=lambda l: l.getval() - 1, set_length=lambda f, v: f.setval(v + 1))
    payload_length_large = ConditionalField(UBInt16(), condition=lambda m: m.payload_length == 0)
    lingo = DispatchField(UBInt8())
    lingo_type = DispatchTarget(greedy=False, length_provider=payload_length, dispatch_field=lingo, dispatch_mapping={
        0x00: GeneralLingo,
        0x01: MicrophoneLingo,
        0x02: SimpleRemoteLingo,
        0x03: DisplayRemoteLingo,
        0x04: ExtendedInterfaceLingo,
        0x05: AccessoryPowerLingo,
        0x07: RFTunerLingo,
        0x08: AccessoryEqualizerLingo,
        0x09: SportsLingo,
        0x0A: DigitalAudioLingo,
        0x0C: StorageLingo,
        0x0E: LocationLingo
    })
    checksum = CRCField(UBInt8(), algo=ipod_checksum, start=2, end=-1)