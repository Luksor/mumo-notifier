#!/usr/bin/env python
# -*- coding: utf-8

from mumo_module import (commaSeperatedIntegers, MumoModule)
import re, socket, json, sched, time, threading, BaseHTTPServer, uuid

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
        parsed = "<center>"
        if notification["link"] is not None:
            parsed += "<a href=\"" + notification["link"] + "\">"
        if notification["imageURL"] is not None:
            parsed += "<img src=\"" + notification["imageURL"] + "\"></img><br>"
        if notification["color"] is not None:
            parsed += "<font color=\"" + notification["color"] + "\">"
        parsed += notification["title"]
        if notification["color"] is not None:
            parsed += "</font>"
        if notification["link"] is not None:
            parsed += "</a>"
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
                            result += self.parseNotification(notification)
                            entries += 1
                        for status in received["status"]:
                            result += self.parseNotification(status)
                            entries += 1
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

    class SimpleRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        HTTP_200 = 'HTTP/1.0 200 OK\r\n\r\n'
        HTTP_404 = 'HTTP/1.0 404 Not Found\r\n\r\n'

        def do_GET(self):
            url = re.split(ur"[\u003f\s]+", self.path)
            if url[0] == "/":
                self.wfile.write(self.HTTP_200 + self.getFileContent("index.html"))
            elif url[0] == "/style.css":
                self.wfile.write(self.HTTP_200 + self.getFileContent("style.css"))
            elif url[0] == "/bootstrap.min.css":
                self.wfile.write(self.HTTP_200 + self.getFileContent("bootstrap.min.css"))
            else:
                self.wfile.write(self.HTTP_404 + "404 Not Found")

        def getFileContent(self, fileName):
            with open("notifier-data/" + fileName, 'r') as content_file:
                content = content_file.read()
            return content

    def runWebServer(self, server_class=BaseHTTPServer.HTTPServer,
        handler_class=SimpleRequestHandler):
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
            server.sendMessageChannel(user.channel, False, "<a href=\"" + scfg.webpanel_public_address + ":8833/?token=" + str(uuid.uuid4()) + "\">Configure notifications.</a>")

    def disconnected(self): pass
    def userConnected(self, server, state, context = None): pass
    def userDisconnected(self, server, state, context = None): pass
    def userStateChanged(self, server, state, context = None): pass
    def channelCreated(self, server, state, context = None): pass
    def channelRemoved(self, server, state, context = None): pass
    def channelStateChanged(self, server, state, context = None): pass