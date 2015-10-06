#!/usr/bin/env python
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------#
# Summary:
# The purpose of this program is to connect to a socket_server instance
# over a local network and perform text-based communication using
# sockets.
# 
# Name: socket_client.py
# Author: Paul Holtz
# Date: 10/2/2015
#-----------------------------------------------------------------------#

#Builtin Imports
import socket
import sys
import os
import time

from Tkinter import *
import ttk
import tkFont
from tkFileDialog   import askopenfilename, askdirectory

import subprocess
import ConfigParser
from glob import glob
import Queue
import threading
from PIL import Image, ImageTk

from gi.repository import Gtk, GLib



def main():
    #Set up the socket client connection
    print "Starting chat client."
    ip = "127.0.0.1"#str(raw_input("Enter an ip address to connect to: "))
    port = 9999#int(raw_input("Enter a port to connect to: "))

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Connect to the server socket
    try:
        sock.connect((ip, port))
        print "Server is {0}".format(sock.getpeername())
    except:
        print "Could not connect to given server."
        sys.exit()

    address_tuple = sock.getsockname()
    client_ip = address_tuple[0]
    client_port = address_tuple[1]  

    #Server should prompt for a username
    user_ok = False
    while not user_ok:
        username = raw_input(sock.recv(1024))
        sock.send(username + "\n")
        reply_from_server = sock.recv(1024)
        #Check reply from server
        if "OK" in reply_from_server:
            user_ok = True
        elif "USERNAME IN USE" in reply_from_server:
            user_ok = False
        else:
            print "Server says: {0}.\nExiting.".format(reply_from_server)
            sys.exit()

    print "Username {0} ok.".format(username)


    #Start the glade/GTK User Interface
    main_window = Hello_World(sock, username, client_ip, client_port)
    Gtk.main() 





class Hello_World:
    def __init__(self, sock=None, username=None, client_ip=None, client_port=None):
        self.sock = sock
        self.username = username
        self.client_ip = client_ip
        self.client_port = client_port

        self.gladefile = "client.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.gladefile)

        self.textbuffer = self.builder.get_object("text_buffer")

        self.entry = self.builder.get_object("text_entry")

        self.text_window = self.builder.get_object("text_window")
        self.adjustment = self.builder.get_object("vert_scroll")

        
        dict = { "on_window_destroy" : self.on_window_destroy, "button_clicked" : self.on_click, "enter_pressed" : self.enter_pressed }
               
        self.builder.connect_signals(dict)
        
        self.window = self.builder.get_object("window")
        
        self.window.show()

        self.sock.setblocking(0)
        self.check_for_message()
        self.keep_scrolling()
        

    def on_window_destroy(self, window):
        Gtk.main_quit()


    def enter_pressed(self, entry):
        self.send_text(self.entry.get_text())

    def on_click(self, button):
        self.send_text(self.entry.get_text())


    def insert_text(self, entry_text):
        self.textbuffer.insert_at_cursor(entry_text + "\n")


    def send_text(self, entry_text):
        if entry_text:
            self.sock.send("{0}\n".format(entry_text))
            self.entry.set_text("")

            if entry_text == "!EXIT":
                Gtk.main_quit()

            elif entry_text == "!CLEAR":
                print dir(self.textbuffer.props)
                self.textbuffer.set_text("", 0)


    def check_for_message(self):
        #print "Checking..."
        try:
            self.data = self.sock.recv(1024)
            #print self.data
            self.textbuffer.insert_at_cursor(self.data + "\n")

        except:
            pass

        GLib.timeout_add(1000, self.check_for_message)


    def keep_scrolling(self):
        self.adjustment.set_value(self.adjustment.get_upper())
        GLib.timeout_add(50, self.keep_scrolling)



if __name__ == "__main__":
    main()
