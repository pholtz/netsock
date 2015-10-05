#!/usr/bin/env python
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------#
# Summary:
# The purpose of this program is to run a TCP socket server and forward
# messages between clients connected to the server.
# 
# Name: socket_server.py
# Author: Paul Holtz
# Date: 9/29/2015
#-----------------------------------------------------------------------#

#Builtin
import SocketServer
import subprocess
import threading
import Queue
import sys
import os
#Private (modified builtin)
from psocket import BaseServer, TCPServer, ThreadingMixIn, BaseRequestHandler, StreamRequestHandler


def main():
    HOST, PORT = "localhost", 9999

    #List to hold the client socket objects
    client_list = []
    #Queue to foster communications between threads
    queue = Queue.Queue()

    #Initialize an empty usernames file
    with open("usernames.log", "w") as username_file:
        username_file.write("")

    # Create the server, binding to localhost on port 9999
    print "Starting server on port {0}.".format(PORT)
    #server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
    server = ThreadedTCPServer((HOST,PORT), MyTCPHandler, queue)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        #Clear username list
        print "Server closed. Goodbye!"




class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, queue):
        TCPServer.__init__(self, server_address, RequestHandlerClass, queue)
        self.queue = queue




class MyTCPHandler(StreamRequestHandler):


    def handle(self):
        """This method gets run whenever a new connection is established."""

        #Announce new connection
        print "Server: {0} connected.".format(self.client_address[0])

        #Initialize the data attribute
        self.data = "!"

        #Prompt the user to enter a username
        #Run checking against user list to make sure that username is unique
        self.username = self.check_username()

        #Broadcast this clients entry to all other clients
        self.broadcast("Client connected.")

        #Put the user in the user queue
        #This is very important! Do not modify this without good reason.
        self.queue.put(self)

        #Write connection to log file
        with open("chat.log", "a+") as log_file:
            log_file.write("{0}@{1}:{2} connected.\n".format(self.username, self.client_address[0], self.client_address[1]))

        #Turn off blocking mode
        self.request.setblocking(0)
        self.received_data = False

        #------------------------------------------#
        #       M E S S E N G E R    L O O P       #
        #------------------------------------------#
        while self.data:

            # self.rfile is a file-like object created by the handler;
            # we can now use e.g. readline() instead of raw recv() calls
            try:
                #Try to access the TCP Handler rfile resource
                self.data = self.rfile.readline().strip()
                
                #If the read line actually has data, print that data and check for a system command
                if self.data:
                    #If we made it this far, data is useful
                    self.received_data = True
                    print "{0}@{1}:{2}: {3}".format(self.username, self.client_address[0], self.client_address[1], self.data)
                    self.check_commands() if (self.data[0] == "!") else ""

            #This gets thrown when we can't read from the rfile resource
            except IOError:
                #Client is connected, but hasn't sent any data
                self.received_data = False


            #Data from the client is present, lets log it and broadcast to the other clients
            if self.received_data:
                #Write chat to log file
                with open("chat.log", "a+") as log_file:
                    log_file.write("{0}@{1}:{2}: {3}\n".format(self.username, self.client_address[0], self.client_address[1], self.data))
                #Broadcast data to all clients, including sender
                if self.data:
                    self.broadcast(self.data)
        #------------------------------------------#

        #Upon client disconnection, print to server
        print "Server: {0}@{1}:{2} >> Client disconnected.".format(self.username, self.client_address[0], self.client_address[1])
        #Remove the client from the queue -- Finish Him!
        self.remove_client()
        #Broadcast the disconnect message
        self.broadcast("Client disconnected.")
        #Write disconnect to log file
        with open("chat.log", "a+") as log_file:
            log_file.write("{0}@{1}:{2} >> Client disconnected.\n".format(self.username, self.client_address[0], self.client_address[1]))
        #Close the client socket
        self.request.close()



    def broadcast(self, message):
        handler_list = self.get_client_list()

        #Send the message to each client using the client's handler object
        for handler in handler_list:

            try:
                handler.wfile.write("{0}@{1}:{2} >> {3}".format(self.username, handler.client_address[0], handler.client_address[1], message))
                self.received_data = False
            except IOError as err:
                handler.request.close()
                print "\nBroadcast Error."
                print err
                sys.exit()
        

    def get_client_list(self):
        handler_list = []
        #Build the handler object list
        while not self.queue.empty():
            handler_list.append(self.queue.get())

        #Put them all back on the list when done!
        for handler in handler_list:
            self.queue.put(handler)

        return handler_list


    def remove_client(self):
        handler_list = []
        #Build the handler object list
        while not self.queue.empty():
            handler_list.append(self.queue.get())

        #Say farewell to the client
        handler_list.remove(self)

        #Put them all back on the list when done!
        #Except the client whose handler we are currently running -- he's dead now
        for handler in handler_list:
            self.queue.put(handler)


    def check_commands(self):
        if self.data == "!EXIT":
            self.request.close()
            self.received_data = False
            self.data = None

        elif self.data == "!LIST":
            command_list_string = "\
#--------------------------#\n\
#  C O M M A N D  L I S T  #\n\
#--------------------------#\n\
!LIST -- Displays this list.\n\
!HELP -- Displays general information about the chat client.\n\
!EXIT -- Exits the chat client and closes the connection.\n\
!CLEAR -- Clears the clients chat history.\n\
!USER -- Displays the full username of the client. (username@ip:port)\n\
!USERLIST -- Displays a list of all clients currently connected to the server.\n\
!TEST -- Prints a test message broadcasted to all clients.\n\
!PRINT -- Deprecated."
            self.wfile.write(command_list_string)
            self.received_data = False

        elif self.data == "!HELP":
            help_string = "\
#------------------------#\n\
#  C H A T  C L I E N T  #\n\
#------------------------#\n\
This program is a chat client which facilitates text-based communication \n\
with other users when connected to the same server. The network type is \n\
broadcast-based, meaning that any messages sent by a client are broadcast \n\
to all other clients connected to the server.\n\n\
Have Fun!"
            self.wfile.write(help_string)
            self.received_data = False

        elif self.data == "!CLEAR":
            #Do nothing on server side -- but don't broadcast this client-side command
            self.received_data = False

        elif self.data == "!USER":
            self.wfile.write("You are {0}@{1}:{2}.".format(self.username, self.client_address[0], self.client_address[1]))
            self.received_data = False

        elif self.data == "!USERLIST":
            client_list = self.get_client_list()
            client_string = "USERLIST:\n"
            for client in client_list:
                client_string = "{0}{1}@{2}:{3}\n".format(client_string, client.username, client.client_address[0], client.client_address[1])
            client_string = "{0}Total users: {1}".format(client_string, self.queue.qsize())
            self.wfile.write(client_string)
            self.received_data = False

        elif self.data == "!PRINT":
            print "***self***:\n{0}\n\n\n".format(dir(self))
            print "***request***:\n{0}\n\n\n".format(dir(self.request))
            print "***server***:\n{0}\n\n\n".format(dir(self.server))
            print "***queue***:\n{0}\n\n\n".format(dir(self.queue))
            self.received_data = False
        
        elif self.data == "!TEST":
            handler_list = []
            #Build the handler object list
            while not self.queue.empty():
                handler_list.append(self.queue.get())

            #Send the message to each client using the client's handler object
            for handler in handler_list:
                print "Sending deez nuts."
                try:
                    handler.wfile.write("deez nuts!")
                    self.received_data = False
                except IOError:
                    print "An IOError flew by!"
            
            #Put them all back on the list when done!
            for handler in handler_list:
                self.queue.put(handler)


    def check_username(self):
        """
        Loops until the user picks a username not already in the usernames.log file list.

        Returns the selected valid username.
        """

        self.wfile.write("Hello! Please enter a username (max 20 characters): ")

        user_ok = False
        while not user_ok:
            #Store the username requested by the client
            username = self.rfile.readline().strip()
            
            user_list = []
            #Check against file list of existing users
            with open("usernames.log", "a+") as username_file:
                user_list = [line.rstrip().split("@")[0] for line in username_file]
                if username in user_list:
                    #Tell client to retry with new username
                    self.wfile.write("USERNAME IN USE")
                    self.wfile.write("Username already in use. Try another: ")
                else:
                    #Add new user to the file list of users
                    user_ok = True
                    username_file.write("{0}@{1}:{2}\n".format(username, self.client_address[0], self.client_address[1]))
                    print "User {0}@{1}:{2} added.".format(username, self.client_address[0], self.client_address[1])
                    self.wfile.write("OK")

        return username




#------------------------#
#  E N T R Y  P O I N T  #
#------------------------#
if __name__ == "__main__":
    main()