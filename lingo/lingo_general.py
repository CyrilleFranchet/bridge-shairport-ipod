#!/usr/bin/env python
# coding : utf-8

# Created by PyCharm on 14/08/2022
# Filename : lingo_general

from suitcase.structure import Structure
from suitcase.fields import UBInt8, UBInt16, UBInt32, SBInt32, UBInt8Sequence, SBInt32, \
    Magic, LengthField, DispatchField, DispatchTarget, FieldProperty, Payload, CRCField, DependentField, \
    ConditionalField, BitField, BitNum, SubstructureField, BitBool, TypeField

from lingo.lingo_base import LINGOS

ACCESSORY_INFO_TYPE = {
    0x00: 'ACCESSORY_INFO_CAPABILITIES',
    0x01: 'ACCESSORY_NAME',
    0x02: 'ACCESSORY_MINIMUM_SUPPORTED_FIRMWARE',
    0x03: 'ACCESSORY_MINIMUM_SUPPORTED_LINGO',
    0x04: 'ACCESSORY_FIRMWARE_VERSION',
    0x05: 'ACCESSORY_HARDWARE_VERSION',
    0x06: 'ACCESSORY_MANUFACTURER',
    0x07: 'ACCESSORY_MODEL_NUMBER',
    0x08: 'ACCESSORY_SERIAL_NUMBER',
    0x09: 'ACCESSORY_INCOMING_MAXIMUM_PAYLOAD_SIZE'
}
ACCESSORY_INFO_TYPE_inv = {v: k for k,v in ACCESSORY_INFO_TYPE.items()}

class RequestIdentify(Structure):
    pass


class Identify(Structure):
    supported_lingo = UBInt8()
    supported_lingo_string = FieldProperty(supported_lingo, onget=lambda m: "%s" % LINGOS[m])


class IdentifyDeviceLingoes(Structure):
    spoken_lingoes = BitField(32,
                              dummy1 = BitNum(19),
                              storage_lingo = BitBool(),
                              dummy2 = BitBool(),
                              digital_audio_lingo = BitBool(),
                              sports_lingo = BitBool(),
                              accessory_equalizer_lingo = BitBool(),
                              rf_tuner = BitBool(),
                              usb_host_control_lingo = BitBool(),
                              accessory_power_lingo = BitBool(),
                              extended_interface_lingo = BitBool(),
                              display_remote_lingo = BitBool(),
                              simple_remote_lingo = BitBool(),
                              microphone_lingo = BitBool(),
                              general_lingo = BitBool()
                              )
    options = BitField(32,
                       dummy = BitNum(28),
                       power_control_bits = BitNum(2),
                       authentication_control_bits = BitNum(2)
                       )
    id = UBInt8Sequence(4)


class GeneralACK(Structure):
    command_result_status = UBInt8()
    command_id_acknowledge = UBInt8()


class GetAccessoryInfo(Structure):
    accessory_info_type = UBInt8()
    accessory_info_type_string = FieldProperty(accessory_info_type, onget=lambda m: "%s" % ACCESSORY_INFO_TYPE[m])
    accessory_info_type_parameters_lingo = ConditionalField(UBInt8(), condition=lambda m: m.accessory_info_type == 0x03)


class RetAccessoryInfo(Structure):
    accessory_info_type = UBInt8()
    accessory_info_type_string = FieldProperty(accessory_info_type, onget=lambda m: "%s" % ACCESSORY_INFO_TYPE[m])
    accessory_info_type_data = ConditionalField(Payload(), condition=lambda m: m.accessory_info_type in (0x01, 0x06, 0x07, 0x08))
    accessory_info_type_data_string = FieldProperty(accessory_info_type_data, onget=lambda d: d.decode('utf-8').rstrip('\x00'))
    accessory_capabilities = ConditionalField(BitField(32,
                                                       dummy = BitNum(22),
                                                       accessory_incoming_max_payload_size = BitBool(),
                                                       accessory_serial_number = BitBool(),
                                                       accessory_model_number = BitBool(),
                                                       accessory_manufacturer = BitBool(),
                                                       accessory_hardware_version = BitBool(),
                                                       accessory_firmware_version = BitBool(),
                                                       accessory_minimum_supported_lingo = BitBool(),
                                                       accessory_minimum_supported_firmware = BitBool(),
                                                       accessory_name = BitBool(),
                                                       accessory_info_capabilities = BitBool()
                                                       ), condition=lambda m: m.accessory_info_type == 0x00)


class DevACK(Structure):
    transid1 = BitNum(8)
    transid2 = BitNum(8)
    ackStatus = UBInt8()
    command_id_acknowledge = UBInt8()


class GeneralLingo(Structure):
    command = DispatchField(UBInt8())
    payload = DispatchTarget(length_provider=None, dispatch_field=command, dispatch_mapping={
        0x00: RequestIdentify,
        0x01: Identify,
        0x02: GeneralACK,
        #0x03: CatchAll,
        #0x04: CatchAll,
        #0x05: CatchAll,
        #0x06: CatchAll,
        #0x07: CatchAll,
        #0x08: CatchAll,
        #0x09: CatchAll,
        #0x0A: CatchAll,
        #0x0B: CatchAll,
        #0x0C: CatchAll,
        #0x0D: CatchAll,
        #0x0E: CatchAll,
        #0x0F: CatchAll,
        #0x10: CatchAll,
        0x13: IdentifyDeviceLingoes,
        #0x14: CatchAll,
        #0x15: CatchAll,
        #0x16: CatchAll,
        #0x17: CatchAll,
        #0x18: CatchAll,
        #0x19: CatchAll,
        #0x1A: CatchAll,
        #0x1B: CatchAll,
        #0x1C: CatchAll,
        #0x1D: CatchAll,
        #0x1E: CatchAll,
        #0x1F: CatchAll,
        #0x23: CatchAll,
        #0x24: CatchAll,
        #0x25: CatchAll,
        0x27: GetAccessoryInfo,
        0x28: RetAccessoryInfo,
        #0x29: CatchAll,
        #0x2A: CatchAll,
        #0x2B: CatchAll,
        #0x38: CatchAll,
        #0x39: CatchAll,
        #0x3A: CatchAll,
        #0x3B: CatchAll,
        #0x3C: CatchAll,
        #0x3F: CatchAll,
        #0x40: CatchAll,
        0x41: DevACK,
        #0x42: CatchAll,
        #0x43: CatchAll,
        #0x49: CatchAll,
        #0x4A: CatchAll,
        #0x4B: CatchAll,
        #0x4C: CatchAll,
        #0x4D: CatchAll,
        #0x4E: CatchAll,
        #0x4F: CatchAll,
        #0x51: CatchAll,
    })