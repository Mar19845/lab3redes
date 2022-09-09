import getpass
from networkx.algorithms.shortest_paths.generic import shortest_path
import yaml
import networkx as nx
import asyncio
import logging
from datetime import datetime
import slixmpp
import networkx as nx
import random
import sys



if sys.platform == 'win32' and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.DEBUG, format=None)
class Client(slixmpp.ClientXMPP):
    def __init__(self, jid_name, password, algorithm, nodo, nodes, users, graph):
        super().__init__(jid_name, password)
        self.received = set()
        self.initialize(jid_name, password, algorithm, nodo, nodes, users, graph)
        
        self.schedule(name="echo", callback=self.echo, seconds=10, repeat=True)
        self.schedule(name="update", callback=self.update_graph, seconds=10, repeat=True)
        
        
        
        self.connected_event = asyncio.Event()
        self.presences_received = asyncio.Event()

        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.recived_message)
        
        
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0199') # Ping
        
    async def start(self, event):
        self.send_presence() 
        await self.get_roster()
        self.connected_event.set() 
         
    def initialize(self, jid_name, password, algorithm, nodo, nodes, users, graph):
        self.algorithm = algorithm
        self.users = users
        self.graph = graph
        self.nodo = nodo
        self.nodes = nodes
        self.jid_name = jid_name
        self.password = password
    
    async def recived_message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            await self.send_msg(msg['body'])
            
    def echo(self):
        for i in self.nodes:
            msg = "echo|" + str(self.jid_name) + "|" + str(self.users[i]) + "||"+ str(datetime.timestamp(datetime.now())) +"|" + str(i) + "|"
            print(msg)
            self.send_message(mto=self.users[i],mbody=msg,mtype='chat')
            
    def update_graph(self):
        if self.algorithm == '1':
            for i in self.nodes:
                self.graph.nodes[i]["neighbors"] = self.graph.neighbors(i)
            
            #update graph
            neigh = nx.get_node_attributes(self.graph,'neighbors')

        elif self.algorithm == '2':
            # Updating states table
            for x in self.graph.nodes().data():
                if x[0] in self.nodes:
                    dataneighbors= x
            for x in self.graph.edges.data('weight'):
                if x[1] in self.nodes and x[0]==self.nodo:
                    dataedges = x
            nodes_strings = str(dataneighbors) + "|" + str(dataedges)
            for i in self.nodes:
                update_msg = "2|" + str(self.jid_name) + "|" + str(self.users[i]) + "|" + str(self.graph.number_of_nodes()) + "||" + str(self.nodo) + "|" + nodes_strings
                self.send_message(mto=self.users[i],mbody=update_msg,mtype='chat')
    
    def return_new_msg(self, message):
        message[4] = message[4] + "," + str(self.nodo)
        message[3] = str(int(message[3]) - 1)
        return "|".join(message)
    
    #part of the logic            
    async def send_msg(self, msg):
        message = msg.split('|')
        
        if message[0] == 'msg':
            
            if self.algorithm == '1':
                #DISTANCE VECTOR: SENT TO THE NEIGHBOR WITH THE SHORTEST DISTANCE
                print('DVR Algorithm\n')
                print(message)
                send_to  = message[6].split('*')[1].split('#')
                send_node = send_to[1]
                
                
                for p,d in self.graph.nodes(data=True):
                    if p == send_node:
                        jid_receiver = d['jid']
                        
                print('Sending msg to -> ', jid_receiver)
                
                #chek if the message is for me or not
                if message[2] == self.jid_name:
                    print("msg received -> " +  message[6])
                else:
                    if message[3] != '0':
                        msg_list = message[4].split(',')
                        if  self.nodo not in msg_list:
                            new_msg = self.return_new_msg(message)
                            self.send_message(mto=jid_receiver,mbody=new_msg,mtype='chat')  
                            # dijkstra distance
                            
            elif self.algorithm == '2':
                print('LSR Algorithm\n')
                if message[2] == self.jid_name:
                    print("msg received -> " +  message[6])
                else:
                    if int(message[3])>0:
                        msg_list = message[4].split(',')
                        if self.nodo not in msg_list:
                            new_msg = self.return_new_msg(message)
                            target_users = []
                            
                            
                            for x in self.graph.nodes().data():
                                    if x[1]["jid"] == message[2]:
                                        target_users.append(x)
                            # dijkstra shortest distance
                            shortest = nx.shortest_path(self.graph, source=self.nodo, target=target_users[0][0])
                            if len(shortest) > 0:
                                self.send_message(mto=self.users[shortest[1]],mbody=new_msg,mtype='chat')  
            elif self.algorithm == '3':
                print('Flooding Algorithm\n')
                if message[2] == self.jid_name:
                     print("msg received -> " +  message[6])
                else:
                    if message[3] != '0':
                        msg_list = message[4].split(',')
                        if self.nodo not in msg_list:
                            new_msg = self.return_new_msg(message)
                            for i in self.nodes:
                                self.send_message(mto=self.users[i],mbody=new_msg,mtype='chat')  
        elif message[0] == 'echo':
            # get the distance between nodes
            if message[6] == '':
                now = datetime.now()
                timestamp = datetime.timestamp(now)
                msg = msg + str(timestamp)
                self.send_message(mto=message[1],mbody=msg,mtype='chat')
            else:
                difference = float(message[6]) - float(message[4])
                self.graph.nodes[message[5]]['weight'] = difference