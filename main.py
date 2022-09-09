from platform import node
from client import *
from tree import Tree
from aioconsole import ainput
import asyncio

logging.basicConfig(level=logging.DEBUG, format=None)
if sys.platform == 'win32' and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
#function that reads a txt file and json/dict
#recives the file route and the encoding
def read_file(file,encoding="utf8"):
    reader = open(file, "r", encoding=encoding).read()
    return yaml.load(reader, Loader=yaml.FullLoader)


def input_algorithm():
    cond = False
    while cond!=True:
        algorithm = input("Select routing algorithm \nDistance vector routing -> 1  \nLink state routing -> 2 \nFlooding -> 3  ")
        if algorithm == "1" or algorithm == "2" or algorithm == '3':
            cond = True
            return algorithm
        else:
            print('please select a valid option')

async def input_chat():
    cond = False
    while cond!=True:
        input_chat_var =  await ainput("Select an option \nStart Chat -> 1  \nLeave chat -> 2 ")
        if input_chat_var == "1" or input_chat_var == "2":
            cond = True
            return input_chat_var
        else:
            print('please select a valid option')
            
#creat msg to send           
def create_msg(xmpp,reciber,msg):
    return "msg|" + str(xmpp.jid_name) + "|" + str(reciber) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(msg)


async def main_loop(xmpp):
    loop_cond = True
    origin_user,destiny_user = '',''
    while loop_cond:
        chat = await input_chat()
        if chat == '2':
            loop_cond = False
            xmpp.disconnect()
        elif chat == '1':
            reciber = await ainput("Enter the username to send him/her a msg -> ")
            active_chat = True
            while active_chat:
                msg = await ainput("Enter the msg -> ")
                if len(msg) > 0:
                    if xmpp.algorithm =='1':
                        
                        msg = create_msg(xmpp,reciber,msg)
                        graph = xmpp.graph
                        for p, d in xmpp.graph.nodes(data=True):
                            print(d)
                            if d['jid'] == xmpp.jid_name:
                                origin_user = p
                            if d['jid'] == reciber:
                                destiny_user = p
                                
                        shortest_path=nx.shortest_path(xmpp.graph, origin_user, destiny_user)
                        print(shortest_path)
                        shortest_path.pop(0)
                        send_to = shortest_path[0]
                        
                        username_reciber= ''
                        for (p, d) in xmpp.graph.nodes(data=True):
                            if (p == send_to):
                                username_reciber = d['jid']
                        print('Sending msg to -> ',username_reciber)
                        
                        #add the rest of the nodes to the msg
                        rest_nodes = '#'.join(str(path) for path in shortest_path)
                        msg = msg+"*"+rest_nodes
                        xmpp.send_message(mto=destiny_user,mbody=msg,mtype='chat')
                    
                    elif xmpp.algorithm == '2':
                        target_users = []
                        for x in xmpp.graph.nodes().data():
                            if x[1]["jid"] == reciber[2]:
                                target_users.append(x)
                                
                        msg = create_msg(xmpp,reciber,msg)
                        shortest = nx.shortest_path(xmpp.graph, source=xmpp.nodo, target=target_users[0][0])
                        
                        if len(shortest) > 0:
                            xmpp.send_message(mto=xmpp.users[shortest[1]],mbody=msg,mtype='chat')
                        else:
                            xmpp.send_message(mto=reciber,mbody=msg,mtype='chat')
                    
                    elif xmpp.algorithm == '3':
                        msg = create_msg(xmpp,reciber,msg)
                        for i in xmpp.nodes:
                            xmpp.send_message(mto=xmpp.users[i],mbody=msg,mtype='chat') 
                               
                        
if __name__ == "__main__":
    #get the topo ande the users from files
    topo = read_file("topo.txt")
    #names = read_file("users.txt")
    names = read_file("users_test.txt")
    
    
    
    username = input("Username -> ")
    pswd = input("Password -> ")
    algorithm = input_algorithm()
    #set nodes and nodo in users info from the txt file
    for key, value in names["config"].items():
        if username == value:
            nodo = key
            nodes = topo["config"][key]
            
    #print(nodo,nodes)
    #print(names['config'])
    graph = Tree(topo, names).get_graph()
    

    xmpp = Client(username, pswd, algorithm, nodo, nodes, names["config"], graph)
    xmpp.connect() 
    xmpp.loop.run_until_complete(xmpp.connected_event.wait())
    xmpp.loop.create_task(main_loop(xmpp))
    xmpp.process(forever=False)
