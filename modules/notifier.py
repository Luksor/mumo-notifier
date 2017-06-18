#!/usr/bin/env python
# -*- coding: utf-8

from mumo_module import (commaSeperatedIntegers, MumoModule)
import re, socket, json, sched, time, threading, BaseHTTPServer, uuid, sqlite3

class notifier(MumoModule):
    default_config = {'notifier':(
                                ('servers', commaSeperatedIntegers, []),
                                ),
                                lambda x: re.match('(all)|(server_\d+)', x):(
                    	        ('notifier_server_ip', str, '0.0.0.0'),
                                ('notifier_server_port', int, 9040),
                                ('webpanel_public_address', str, 'http://example.com'),
                    )
                    }

    def parseNotification(self, notification):
        feedInfo = notification["feedName"].split('-')
        parsed = "<center>"
        if notification["link"] is not None:
            parsed += "<a href=\"" + notification["link"] + "\">"
        if notification["imageURL"] is not None:
            parsed += "<img src=\"" + notification["imageURL"] + "\"></img><br>"
        if notification["color"] is not None:
            parsed += "<font color=\"" + notification["color"] + "\">"
        parsed += "<b><font size=\"4\">" + notification["title"] + "</font></b><br>"
        if notification["link"] is not None:
            parsed += "</a>"
        parsed += "<font size=\"3\">"
        if notification["extra"] is not None:
            if feedInfo[1] == "4chan":
                parsed += ">>>/" + notification["extra"]["board"] + "/" + str(notification["extra"]["id"])
                parsed += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                parsed += str(notification["extra"]["replies"]) + "/"
                parsed += str(notification["extra"]["images"]) + "/"
                parsed += str(notification["extra"]["page"]) + "<br>"
            elif feedInfo[1] == "youtube":
                parsed += notification["extra"]["displayName"] + "<br>"
            elif feedInfo[1] == "vinesauce":
                parsed += notification["extra"]["displayName"] + "<br>"
            else:
                parsed += str(notification["extra"]) + "<br>"
        parsed += "</font><font size=\"2\">" + feedInfo[0] + " &#8594; " + feedInfo[1]
        if len(feedInfo) > 2:
            parsed += " &#8594; " + feedInfo[2]
        parsed += "</font>"
        if notification["color"] is not None:
            parsed += "</font>"
        parsed += "</center>"
        return parsed

    def connection_thread(self):
        if not hasattr(self, 'server'):
            self.server=self.manager().getMeta().getBootedServers()[0]

        log = self.log()

        try:
            scfg = getattr(self.cfg(), 'server_%d' % self.server.id())
        except AttributeError:
            scfg = self.cfg().all

        while True:
            log.debug("Sending update command.")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((scfg.notifier_server_ip, scfg.notifier_server_port))
                sock.sendall("{\"command\": \"update\"}\n")

                while True:
                    received_json = sock.makefile().readline()
                    log.debug("Received new update.")
                    try:
                        received = json.loads(received_json)
                        result = ""
                        entries = 0
                        for notification in received["notifications"]:
                            if notification["error"] is False:
                                result += self.parseNotification(notification)
                                entries += 1
                            else:
                                log.debug("Error in notification:\n" + notification["title"] + "\n" + notification["description"])
                        for status in received["status"]:
                            if status["error"] is False:
                                result += self.parseNotification(status)
                                entries += 1
                            else:
                                log.debug("Error in status:\n" + status["title"] + "\n" + status["description"])
                        if entries > 0:
                            self.server.sendMessageChannel(0, True, result)
                    except ValueError:
                        log.debug("Invalid data received!")
                        break

                log.debug("Connection closed!")
                sock.close()

            except socket.error:
                log.debug("Connection error!")
            log.debug("Restarting connection in 30 seconds!")
            time.sleep(30)

    def getRequestHandler(self, scfg, log):
        class SimpleRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
            HTTP_200 = 'HTTP/1.0 200 OK\r\n\r\n'
            HTTP_404 = 'HTTP/1.0 404 Not Found\r\n\r\n'

            def do_GET(self):
                url = re.split(ur"[\u003f\s]+", self.path)
                if url[0] == "/":
                    self.wfile.write(self.HTTP_200 + self.getFileContent("index.html"))
                elif url[0] == "/style.css":
                    self.wfile.write(self.HTTP_200 + self.getFileContent("style.css"))
                elif url[0] == "/script.js":
                    self.wfile.write(self.HTTP_200 + self.getFileContent("script.js"))
                elif url[0] == "/jquery-3.1.1.min.js":
                    self.wfile.write(self.HTTP_200 + self.getFileContent("jquery-3.1.1.min.js"))
                elif url[0] == "/feeds.json":
                    received_json = ""
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.connect((scfg.notifier_server_ip, scfg.notifier_server_port))
                        sock.sendall("{\"command\": \"list\"}\n")
                        received_json = sock.makefile().readline()
                        log.debug("Received feed list.")
                        sock.close()
                    except socket.error:
                        log.debug("Connection error!")
                    self.wfile.write(self.HTTP_200 + received_json)
                else:
                    self.wfile.write(self.HTTP_404 + "404 Not Found")

            def getFileContent(self, fileName):
                with open("notifier-data/" + fileName, 'r') as content_file:
                    content = content_file.read()
                return content
        return SimpleRequestHandler

    def runWebServer(self):
        if not hasattr(self, 'server'):
            self.server=self.manager().getMeta().getBootedServers()[0]

        log = self.log()

        try:
            scfg = getattr(self.cfg(), 'server_%d' % self.server.id())
        except AttributeError:
            scfg = self.cfg().all

        server_class = BaseHTTPServer.HTTPServer
        handler_class = self.getRequestHandler(scfg, log)
        server_address = ('', 8833)
        httpd = server_class(server_address, handler_class)
        httpd.serve_forever()

    def __init__(self, name, manager, configuration = None):
        MumoModule.__init__(self, name, manager, configuration)
        self.murmur = manager.getMurmurModule()

    def connected(self):
        manager = self.manager()
        log = self.log()
        log.debug("Register for Server callbacks")

        servers = self.cfg().notifier.servers
        if not servers:
            servers = manager.SERVERS_ALL

        manager.subscribeServerCallbacks(self, servers)

        db = sqlite3.connect('notifier-data/sqlite.db')
        
        t = threading.Thread(target=self.connection_thread)
        t.daemon = True
        t.start()
        t = threading.Thread(target=self.runWebServer)
        t.daemon = True
        t.start()

    def userTextMessage(self, server, user, message, current=None):
        try:
            scfg = getattr(self.cfg(), 'server_%d' % server.id())
        except AttributeError:
            scfg = self.cfg().all

        words = re.split(ur"[\u200b\s]+", message.text)
        command = words[0]
        if (command == "!notifier"):
            name = user.name
            token = str(uuid.uuid4())
            server.sendMessage(user.session, "<a href=\"" + scfg.webpanel_public_address + ":8833/?user=" + name + "&token=" + token + "\">Configure notifications.</a>")

    def disconnected(self): pass
    def userConnected(self, server, state, context = None): pass
    def userDisconnected(self, server, state, context = None): pass
    def userStateChanged(self, server, state, context = None): pass
    def channelCreated(self, server, state, context = None): pass
    def channelRemoved(self, server, state, context = None): pass
    def channelStateChanged(self, server, state, context = None): pass
