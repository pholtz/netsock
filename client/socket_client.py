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


def main():

	print "Starting chat client."
	ip = str(raw_input("Enter an ip address to connect to: "))
	port = int(raw_input("Enter a port to connect to: "))

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

	#Create the root Tk object
	root = Tk()

	#Set the window title
	root.wm_title("pchat client")

	#Set the custom JCI favicon graphic
	extension = os.path.split(__file__)[0]
	if not extension:
		extension = "."
	try:
		print "{0}/burn.gif".format(extension)
		print os.path.exists("{0}/burn.gif".format(extension))
		favicon = PhotoImage(file="{0}/burn.png".format(extension))
		root.tk.call('wm', 'iconphoto', root._w, favicon)
	except:
		print "Couldn't load icon, using Tkinter default."

	#Add the top-mount cascading menu
	add_menu(root)

	main_frame = Frame(master=root, borderwidth=6, relief=GROOVE)
	client_frame(main_frame, sock, username, client_ip, client_port)
	main_frame.grid()

	#try:
		#Hand over control to Tkinter
		#From here everything will be handled through callbacks
	root.mainloop()
	#finally:
		#print "Shutting down socket."
		#sock.shutdown(socket.SHUT_WR)
		#sock.close()




class client_frame(ttk.Frame):

	def __init__(self, root=None, sock=None, username=None, client_ip=None, client_port=None):
		#Frame.__init__(self, master)
		#self.pack()
		self.root = root
		self.sock = sock
		self.username = username
		self.ip = client_ip
		self.port = client_port

		self.create()

		self.sock.setblocking(0)
		self.check_messages()


	def create(self):

		self.bg_color = "#222222"
		self.fg_color = "#009933"

		self.extension = os.path.split(__file__)[0]
		if not self.extension:
			self.extension = "."
		self.title_image = Image.open("{0}/ns.png".format(self.extension))
		self.title_image.thumbnail((100, 30))
		self.title_photo = ImageTk.PhotoImage(self.title_image)
		self.title_label = Label(master=self.root, image=self.title_photo)
		self.title_label.grid(row=0, column=0, padx=5, pady=5, columnspan=2, sticky=W)

		self.scrollbar = Scrollbar(master=self.root)
		self.scrollbar.grid(row=1, column=2, padx=5, sticky="NWS")

		self.chat_text = Text(master=self.root, width=100, height=20, wrap=WORD, yscrollcommand=self.scrollbar.set)
		self.chat_text.grid(row=1, column=0, columnspan=2, sticky="W")

		self.scrollbar.config(command=self.chat_text.yview)


		self.username = Label(master=self.root, width=35, height=1, fg="#002222", anchor="w", text="{0}@{1}:{2} >> ".format(self.username, self.ip, self.port))
		self.username.grid(row=2, column=0, padx=5, pady=5, sticky="W")

		self.chat_entry = Entry(master=self.root, width=100, justify=LEFT)
		self.chat_entry.bind("<Return>", self.send_chat_enter)
		self.chat_entry.grid(row=2, column=1, padx=5, pady=5, sticky="W")

		self.chat_button = Button(master=self.root, width=10, height=1, text="Send", command=self.send_chat)
		self.chat_button.grid(row=2, column=2, padx=5, pady=5)

		#Set the focus to the message prompt so the user can begin typing immediately
		self.chat_entry.focus()



	def send_chat_enter(self, event):
		"""Redirects to send_chat to send a message over the socket."""
		self.send_chat()


	def send_chat(self):
		"""Method to send the contents of the chat entry field over the socket."""
		#Make text widget writeable
		self.chat_text.config(state=NORMAL)

		message = self.chat_entry.get()
		if message:
			self.sock.send("{0}\n".format(message))
			self.chat_entry.delete(0, END)

			#Check for user exit command
			if message == "!EXIT":
				print "Exiting client thread."
				sys.exit()
			elif message == "!CLEAR":
				self.chat_text.delete(1.0, END)

		#Return text to read-only state
		self.chat_text.config(state=DISABLED)



	def check_messages(self):
		"""Method to check for new messages over the socket."""
		#Make text widget writeable
		self.chat_text.config(state=NORMAL)

		try:
			self.data = self.sock.recv(1024)
			#print self.data
			self.chat_text.insert(END, "{0}\n".format(self.data))
			self.chat_text.yview(END)
		except:
			pass
		
		#Set timer to call this method again
		self.root.after(1000, self.check_messages)
		
		#Return text to read-only state
		self.chat_text.config(state=DISABLED)




#------------------#
#  Menu Functions  #
#------------------#
def new_instance():
	extension = os.path.split(__file__)[0]
	if not extension:
		extension = "."
	subprocess.Popen(["python", "{0}/socket_client.py".format(extension)])


def open_file():
    name = askopenfilename()
    print name

def about_chat_client(root):
    window = Toplevel(master=root, takefocus=True, bd=6, relief=GROOVE)
    window.wm_title("About chat client")
    extension = os.path.split(__file__)[0]
    if not extension:
        extension = "."
    try:
        favicon = PhotoImage(file="{0}/images/jci.gif".format(extension))
        window.tk.call("wm", "iconphoto", window._w, favicon)
    except:
        print "Couldn't load JCI image, using default."

    courier_new = tkFont.Font(family="Courier New", size=10, weight="normal", slant="roman", underline=0, overstrike=0)

    label1 = Label(master=window, text=about_language_database_tools_message, wraplength=800, justify=LEFT, font=courier_new)
    label1.pack()

def add_menu(root):
    menu = Menu(root)
    root.config(menu=menu)
    filemenu = Menu(menu)

    menu.add_cascade(label="File", menu=filemenu)
    filemenu.add_command(label="New", command=new_instance)
    #filemenu.add_command(label="Open...", command=open_file)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)

    helpmenu = Menu(menu)
    menu.add_cascade(label="Help", menu=helpmenu)

    helpmenu.add_command(label="About chat client", command=lambda: about_chat_client(root))


about_chat_client_message = "\
Summary: \tThis program is a graphical chat client. Its purpose is to allow users to talk over a local network.\n\
Author: \tPaul Holtz\n\
Date: \t\t10/2/2015"




#------------------------#
#  E N T R Y  P O I N T  #
#------------------------#
if __name__ == '__main__':
	main()