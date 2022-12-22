#!/usr/bin/env python
# coding : utf-8

import os
from mpris2 import get_players_uri, Player

import dbus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

os.environ['DISPLAY'] = ':1'

system_bus = dbus.SystemBus()
proxy = system_bus.get_object('org.mpris.MediaPlayer2.ShairportSync', '/org/mpris/MediaPlayer2')
player_manager = dbus.Interface(proxy, 'org.mpris.MediaPlayer2.Player')
properties_manager = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
#player_manager.Next()
#player_manager.Pause()
#player_manager.Play()
#player_manager.Previous()

print(properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Metadata'))
print(properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Shuffle'))
#print(properties_manager.Set('org.mpris.MediaPlayer2.Player', 'Shuffle', False))
#player_manager.Next()
#print(curr_volume)

#print([uri for uri in get_players_uri()])

#player = Player(dbus_interface_info={'dbus_uri': 'org.mpris.MediaPlayer2.ShairportSync'})
