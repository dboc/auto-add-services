#!/usr/bin/python
# -*- coding: utf-8 -*-

# @author: Daniel Carvalho
# @email : daniel.carvalho@prodest.es.gov.br

# Update: 25/06/2019
from zabbix_api import ZabbixAPI
import os
import re
import io
import sys
import ssl


# Change to UTF8 Encoding in Python 2
if sys.version_info.major < 3:
    reload(sys)
    sys.setdefaultencoding('utf8')

# ##Classes## #


class ServiceGroup:
    def __init__(self, name, groupId):
        self.name = name
        self.id = groupId
        self.srvHosts = []
        self.stillExist = False


class ServiceHost:
    def __init__(self, name, hostsId, parentId):
        self.name = name
        self.id = hostsId
        self.parentId = parentId
        self.srvTriggers = []
        self.stillExist = False


class ServiceTrigger:
    def __init__(self, name, triggerId, parentId):
        self.name = name
        self.id = triggerId
        self.parentId = parentId
        self.stillExist = False

# ##Functions Utils## #


def contains_name(name, listObj):
    for idx in range(len(listObj)):
        if(name == listObj[idx].name):
            return listObj[idx]
    return None


def contains_hostID(hostID, listObj):
    for idx in range(len(listObj)):
        matchObj = re.match(r'.*\|HostID=([0-9]+)\|', listObj[idx].name)
        if(matchObj and not matchObj.end() == -1):
            if(matchObj.group(1) == hostID):
                return listObj[idx]
    return None


def contains_groupID(groupID, listObj):
    for idx in range(len(listObj)):
        matchObj = re.match(r'.*\|GroupID=([0-9]+)\|', listObj[idx].name)
        if(matchObj and not matchObj.end() == -1):
            if(matchObj.group(1) == groupID):
                return listObj[idx]
    return None


def delete_servicegroup(group, zabbixAPI):
    for host in group.srvHosts:
        for trigger in host.srvTriggers:
            sts = zabbixAPI.service.delete([trigger.id])
        sts = zapi.service.delete([host.id])
    sts = zapi.service.delete([group.id])


def delete_servicehost(host, zabbixAPI):
    for trigger in host.srvTriggers:
        sts = zabbixAPI.service.delete([trigger.id])
    sts = zapi.service.delete([host.id])


def fullmatch(regex, string, flags=0):
    """Emulate python-3.4 re.fullmatch()."""
    return re.match("(?:" + regex + r")\Z", string, flags=flags)

# ##Coding###
# Parameters
SERVER = "http://127.0.0.1" # Your Zabbix IP
USERNAME = "your_username"
PASSWORD = "your_pass"
TAG_NAME = "SLA"

# Template HOST NAME
TPL_HOSTNAME = '{} |HostID={}|'
TPL_GROUPNAME = '{} |GroupID={}|'

# Open File Config
scriptPath = os.path.dirname(__file__)
configFile = open(os.path.join(scriptPath, 'config'), 'r')
config_lines = []
if(not configFile):
    print("File 'config' not found")
    exit(-1)
else:
    for idxL, line in enumerate(configFile.readlines()):
        matchObj = re.match('^(.+);([0-2])', line)
        if(not matchObj):
            print("Erro in 'config' line {} : {}".format(idxL, line))
            exit(-1)
        elif(matchObj.lastindex < 2):
            print("Erro in 'config' line {} : {}".format(idxL, line))
            exit(-1)
        config_lines.append(line)

# Zabbix API
if sys.version_info.major < 3:
    ssl._create_default_https_context = ssl._create_unverified_context
zapi = ZabbixAPI(server=SERVER, ssl_verify=False)
zapi.session.verify = False
zapi.login(USERNAME, PASSWORD)

# Service Variables
srvGroups = []
srvTriggers = []
srvHosts = []

# GET ALL Services
itServices = zapi.service.get(
    {
        "selectDependencies": ["serviceid"],
        "selectParent": ["name"], "sortfield": ['name'],
        "output": "extend"
    })
for service in itServices:
    # Nivel 1
    if(not service['parent']):
        newServiceGroup = ServiceGroup(
                                       service['name'],
                                       service['serviceid'])
        srvGroups.append(newServiceGroup)
    # Nivel 3
    elif (not service['dependencies'] and service['parent']):
        newServiceTrigger = ServiceTrigger(service['name'],
                                           service['serviceid'],
                                           service['parent']['serviceid'])
        srvTriggers.append(newServiceTrigger)
    # Nivel 2
    else:
        newServiceHost = ServiceHost(
                                     service['name'],
                                     service['serviceid'],
                                     service['parent']['serviceid'])
        srvHosts.append(newServiceHost)

# Filling ServiceGroup srvGroup-> srvHosts-> srvTriggers
for idxT in range(len(srvTriggers)):
    for idxH in range(len(srvHosts)):
        if(srvTriggers[idxT].parentId == srvHosts[idxH].id):
            srvHosts[idxH].srvTriggers.append(srvTriggers[idxT])
for idxH in range(len(srvHosts)):
    for idxG in range(len(srvGroups)):
        if(srvHosts[idxH].parentId == srvGroups[idxG].id):
            srvGroups[idxG].srvHosts.append(srvHosts[idxH])

# GET ALL GROUP
hostgroups = zapi.hostgroup.get(
    {
        "output": ["name", "groupid"],
        "sortfield": "name"
    })

# Looping in config lines
for idxL, line in enumerate(config_lines):
    matchObj = re.match('^(.+);([0-2])', line)
    pattern, algth = matchObj.group(1), matchObj.group(2)

    # Looping in GROUP
    for group in hostgroups:
        # If not match pattern then continue
        if(not fullmatch(pattern, (group['name']))):
            continue

        # Check ServiceGroup with same name
        groupname = TPL_GROUPNAME.format(group['name'], group['groupid'])
        srvgroup_matched = None
        srvgroup_matchedName = contains_name(groupname, srvGroups)
        srvgroup_matchedID = contains_groupID(group['groupid'], srvGroups)

        if(not srvgroup_matchedName and not srvgroup_matchedID):
            # CREATE SERVICE GROUP
            print("Create Service(GROUP) : " + groupname)
            status = zapi.service.create(
                {
                    "name": groupname,
                    "algorithm": algth,
                    "showsla": "1",
                    "sortorder": "0",
                    "goodsla": "99.5"})
            srvgroup_matched = ServiceGroup(groupname,
                                            status['serviceids'][0])
            srvGroups.append(srvgroup_matched)
        elif(not srvgroup_matchedName and srvgroup_matchedID):
            # UPDATE SERVICE GROUP
            print("Update Service(GROUP) : " + groupname)
            status = zapi.service.update(
                {
                    "name": groupname,
                    "serviceid ": srvgroup_matchedID.id})
            srvgroup_matched = srvgroup_matchedID
            srvgroup_matched.name = groupname
        elif(srvgroup_matchedName and srvgroup_matchedID):
            srvgroup_matched = srvgroup_matchedName
        srvgroup_matched.stillExist = True

        # GET ALL HOST in HOSTGROUP
        hosts_in_group = zapi.host.get(
            {
                "groupids": group['groupid'],
                "output": ["name", "host", "hostid"]})

        # Looping in HOST
        for host in hosts_in_group:

            hostname = TPL_HOSTNAME.format(host['name'], host['hostid'])
            srvhost_matched = None

            # Check ServiceGroup with same ID
            srvhost_matchedID = contains_hostID(host['hostid'],
                                                srvgroup_matched.srvHosts)
            srvhost_matchedName = contains_name(hostname,
                                                srvgroup_matched.srvHosts)
            # GET ALL TRIGGER WITH TAG = $TAG_NAME
            triggers_in_host = zapi.trigger.get(
                {
                    "hostids": host['hostid'],
                    "tags": [{"tag": TAG_NAME}],
                    "output": "extend"})

            if(not triggers_in_host):
                continue

            elif(not srvhost_matchedID and not srvhost_matchedName):
                # CREATE SERVICE HOST
                print("Create Service(HOST) : " + hostname)
                status = zapi.service.create(
                    {
                        "name": hostname,
                        "algorithm": algth,
                        "parentid": srvgroup_matched.id,
                        "showsla": "1",
                        "sortorder": "0",
                        "goodsla": "99.5"})

                srvhost_matched = ServiceHost(hostname,
                                              status['serviceids'][0],
                                              srvgroup_matched.id)
                srvhost_matched.stillExist = True
                srvgroup_matched.srvHosts.append(srvhost_matched)

            elif(srvhost_matchedID and not srvhost_matchedName):
                # UPDATE SERVICE HOST
                print(
                    "Update Service(HOST) Name : {} - {} ".format(
                        srvhost_matchedID.name,
                        hostname))
                status = zapi.service.update(
                    {
                        "serviceid ": srvhost_matchedID.id,
                        "name": hostname})
                srvhost_matchedID.name = hostname
                srvhost_matched = srvhost_matchedID
            elif(srvhost_matchedID and srvhost_matchedName):
                srvhost_matched = srvhost_matchedID

            srvhost_matched.stillExist = True

            # Looping in Triggers
            for trigger in triggers_in_host:
                srvTriggerMatch = contains_name(trigger['description'],
                                                srvhost_matched.srvTriggers)
                if(not srvTriggerMatch):
                    print("Create Service(TRIGGER) :" + trigger['description'])
                    # CREATE SERVICE TRIGGER
                    status = zapi.service.create(
                        {
                            "name": trigger['description'],
                            "algorithm": algth,
                            "parentid": srvhost_matched.id,
                            "triggerid": trigger['triggerid'],
                            "showsla": "1",
                            "sortorder": "0",
                            "goodsla": "99.5"})

                    srvTriggerMatch = ServiceTrigger(trigger['description'],
                                                     status['serviceids'][0],
                                                     srvhost_matched.id)

                    srvhost_matched.srvTriggers.append(srvTriggerMatch)
                srvTriggerMatch.stillExist = True

            # Delete service trigger that was removed tag SLA or was deleted
            for trigger in srvhost_matched.srvTriggers:
                if(not trigger.stillExist):
                    print("Delete Service(TRIGGER) :" + trigger.name)
                    sts = zapi.service.delete([trigger.id])
        # Delete service host that was deleted
        for host in srvgroup_matched.srvHosts:
            if(not host.stillExist):
                for trigger in host.srvTriggers:
                    print("Delete Service(TRIGGER):" + trigger.name)
                    sts = zapi.service.delete([trigger.id])
                print("Delete Service(Host) :" + host.name)
                sts = zapi.service.delete([host.id])
# Delete service group that was deleted
for group in srvGroups:
        if(not group.stillExist):
            pattern_tmpl = r".*\s\|GroupID=[0-9]+\|"
            if(not re.match(pattern_tmpl, group.name)):
                print(
                    "Service(GROUP) not deleted, not in pattern:" + group.name)
                continue
            print("Delete Service(GROUP) :" + group.name)
            delete_servicegroup(group, zapi)
