import subprocess
import json
import re
def install(container_name):
   subprocess.run(["docker","exec","--privileged",container_name,"apt-get", "update"])
   subprocess.run(["docker","exec","--privileged",container_name,"apt-get","-y", "install", "iproute2"])
   subprocess.run(["docker","exec","--privileged",container_name,"apt-get","-y", "install", "iputils-ping"])
   return()
def create_bridges():
     for i in range(1,6):
      bridge_name = "bridge" + str(i) 
      subprocess.run(["docker", "network", "create", bridge_name])
     return()

def create_containers(*args):
      container_names = []
      for i in range(len(args)):
       subprocess.run(["docker", "run", "-d","--name",args[i], "nginx"])
       subprocess.run(["docker","start", args[i]])
       container_names.append(args[i])
      return(container_names)
def connect_bridges(bridge, container):
       subprocess.run(["docker", "network", "connect",bridge, container])
       return()
def add_route(container, net_addr,getway,inter):
       subprocess.run(["docker", "exec", "--privileged",container,"ip","route","add",net_addr,"via",getway,"dev",inter])
       return()
#add_route("router1","172.24.0.0/16","172.20.0.3","eth3") 
def del_route(container, net_addr,getway,inter):
       subprocess.run(["docker", "exec", "--privileged",container,"ip","route","del",net_addr,"via",getway,"dev",inter])
       return()
def change_default(container,getway,inter):
       subprocess.run(["docker", "exec", "--privileged",container,"ip","route","change","default","via",getway,"dev",inter])
       return()
#change_default("nginx1","172.23.0.2","eth1") 
def inter_up(container,inter):
       subprocess.run(["docker", "exec", "--privileged",container,"ip","link","set","dev",inter,"up"])
       return()
#inter_up("router1","eth1")
def get_interfaces(container_name):
    cmd = ['docker', 'exec', container_name, 'ip', 'addr', 'show']
    try:
        output = subprocess.check_output(cmd)
        output_str = output.decode()
        #print(output_str)  # add this line to print the output
        return output_str
    except subprocess.CalledProcessError:
        print(f"Error running command: {' '.join(cmd)}")
        return None
def find_interface_by_subnet(container_name, subnet):
    output_str = get_interfaces(container_name)
    if output_str is None:
        return None
    pattern = r'inet\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\/(\d{1,2})\s+brd\s+\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s+scope\s+global\s+(\w+)'
    matches = re.findall(pattern, output_str)
    for match in matches:
        ip_address, cidr, interface_name = match
        if subnet in ip_address+'/'+cidr:
            return interface_name
    return None
def get_bridge_subnet(network_name):
    cmd = ['docker', 'network', 'inspect', network_name]
    output = subprocess.check_output(cmd)
    network_data = json.loads(output.decode())[0]
    subnet = network_data['IPAM']['Config'][0]['Subnet']
    return subnet.split('/')[0]
#example
#subnet = get_bridge_subnet("bridge3")
#subnet_prefix = subnet[:-1] # remove the last octet of the IP address
#interface_name = find_interface_by_subnet("router1", subnet_prefix)
#if interface_name is not None:
   # print(f"Interface with subnet {subnet} found: {interface_name}")
#else:
   # print(f"No interface found with subnet {subnet}")
def get_interface_ip(container_name, interface_name):
    cmd = ['docker', 'exec', container_name, 'ip', 'addr', 'show', interface_name]
    output = subprocess.check_output(cmd)
    output_str = output.decode()
    # find the line that contains the IP address
    ip_line = [line for line in output_str.split('\n') if 'inet' in line][0]
    # extract the IP address from the line
    ip_address = ip_line.strip().split(' ')[1].split('/')[0]
    return ip_address
#ip_address = get_interface_ip("router1", interface_name)
#print(ip_address)

#call_functions

#crate_containers
container_names=create_containers("nginx1", "nginx2", "nginx3", "nginx4", "router1", "router2")
#install_dependencies
for container_name in container_names:
 install(container_name)
#create_bridges
create_bridges()
#connect_bridges
connect_bridges("bridge1","nginx1")
connect_bridges("bridge1","router1")
connect_bridges("bridge2","nginx2")
connect_bridges("bridge2","router1")
connect_bridges("bridge3","router1")
connect_bridges("bridge3","router2")
connect_bridges("bridge4","nginx3")
connect_bridges("bridge4","router2")
connect_bridges("bridge5","nginx4")
connect_bridges("bridge5","router2")
#create routes for router1  
container="router1"
bridges=["bridge4","bridge5"]
for bridge in bridges:
 net_addr=get_bridge_subnet(bridge)
 getway=get_interface_ip("router2", find_interface_by_subnet("router2", get_bridge_subnet("bridge3")[:-1]))
 inter=find_interface_by_subnet("router1", get_bridge_subnet("bridge3")[:-1])
 add_route(container,net_addr+"/16",getway,inter)
#create routes for router2  
container="router2"
bridges=["bridge1","bridge2"]
for bridge in bridges:
 net_addr=get_bridge_subnet(bridge)
 getway=get_interface_ip("router1", find_interface_by_subnet("router1", get_bridge_subnet("bridge3")[:-1]))
 inter=find_interface_by_subnet("router2", get_bridge_subnet("bridge3")[:-1])
 add_route(container,net_addr+"/16",getway,inter)

#change default for nginx1:
container="nginx1"
getway=get_interface_ip("router1", find_interface_by_subnet("router1", get_bridge_subnet("bridge1")[:-1]))
inter=find_interface_by_subnet("nginx1", get_bridge_subnet("bridge1")[:-1])
change_default(container,getway,inter)
#change default for nginx2:
container="nginx2"
getway=get_interface_ip("router1", find_interface_by_subnet("router1", get_bridge_subnet("bridge2")[:-1]))
inter=find_interface_by_subnet("nginx2", get_bridge_subnet("bridge2")[:-1])
change_default(container,getway,inter)
#change default for nginx3:
container="nginx3"
getway=get_interface_ip("router2", find_interface_by_subnet("router2", get_bridge_subnet("bridge4")[:-1]))
inter=find_interface_by_subnet("nginx3", get_bridge_subnet("bridge4")[:-1])
change_default(container,getway,inter)
#change default for nginx4:
container="nginx4"
getway=get_interface_ip("router2", find_interface_by_subnet("router2", get_bridge_subnet("bridge5")[:-1]))
inter=find_interface_by_subnet("nginx4", get_bridge_subnet("bridge5")[:-1])
change_default(container,getway,inter)


