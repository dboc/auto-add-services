### About me
 I am developer as hobby. For me automate boring stuff is a pleasure, no more operational work :)
 > "Live as if you were to die tomorrow. Learn as if you were to live forever" Mahatma Gandhi.

### Donate
 if you like the project and it help you, you could give me some reward for that.

|Donate via PayPal| Top Donation   | Lastest Donation   |
|---|---|---|
|[![](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=PCTDXQTW2H59G&source=url) |  -  |  -  |


# auto-add-services

> Zabbix Script - Sync IT Service with Trigger contain a TAG_NAME.

Creating IT Services in Zabbix could be exausting in an envirroment with many Hosts and Triggers.\
This Script allow you to manage the creation of IT Services automatically based on Triggers TAG NAME.\
The services are created hierarchically in 3 levels.\
The first level correspond to Host Group that has Hosts with Triggers contain a certain TAG NAME . The second level correspond to Hosts that has Triggers with a certain TAG NAME. Finally, the third level is services that correspond to Triggerrs.
The Hierarchy is like that:

- HOST_GROUP_NAME |GroupID=#ID|
  - HOST_NAME |HostID=#ID|
    - TRIGGER_NAME

![Hierarchy_sample](/hierarquia.png)

## How It Works

The script scan all HOST_GROUP defined in config file then scan all host that has certain trigger with certain TAG_NAME.\
These triggers that have a TAG_NAME will be added to calculate the SLA. 
So the TAG_NAME has to be add in trigger, example:

![Trigger_Sample](/trigger_tag.png)\
The above trigger was configurated to has "SLA" TAG_NAME, also is needed to configure in auto-add-services the variable TAG_NAME as "SLA"\
After execute the script the IT Services will be like that:

![Hierarchy_sample](/hierarquia.png)


## Requirements
 - python2 or python3
 - zabbix-api

## Installation
```
yum install rpm-python-4.11.3-35.el7.x86_64
yum install python2-pip-8.1.2-8.el7.noarch
pip install zabbix-api
git clone https://github.com/dboc/auto-add-services.git ./somedirectory
```
## Config

The config file has two collumns separated with ";" and its mandatory.\
The first column is the name of group host.\
The second is the algorithm used to calc SLA, possible values are:\
 0 - do not calculate;\
 1 - problem, if at least one child has a problem;\
 2 - problem, if all children have problems.

Example of config file:
```
GROUP_NAME_A;1
GROUP_NAME_B;1
GROUP_NAME_C;2
GROUP_NAME_D;2
```

## Usage example

The config file has to be in the same directory of script with the name "config".

Modify the follow variables in auto-add-services.py to fit your needs.
```python
# Parameters
SERVER = "http://127.0.0.1" # Your Zabbix IP
USERNAME = "your_username"
PASSWORD = "your_pass"
TAG_NAME = "SLA"
```

After that you could execute the script

```
./somedirectory/auto-add-services.py
```

## Release History

* 0.1
    * Initial code

## Contributing

1. Fork it (<https://github.com/dboc/auto-add-services/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request
