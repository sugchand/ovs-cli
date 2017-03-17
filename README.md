# OVS-CLI

This is an attempt to give physical swith alike command line interpreter for
OVS-DPDK. One of the hardest problem with OVS-DPDK is its debuggability.
There are plenty of commands implemented in OVS-DPDK to find performance and
functionality issues. Most of these commands are not known to the customers due to the limited documentation, complex command structure, difficult to remember.

It is not possible to type any ovs command without refering to its documentation
or the guide from Internet. The solution trying to collate all the relevant
debug commands under one umbrella for ease of use.

**NOTE :: ONLY DEBUG COMMANDS ARE SUPPORTED. SHOULD NOT USE FOR OVS CONFIG**

## Prerequisite
* It is expected that the OVS must be installed and running in the system to
use the cli framework. The ovs-cli can be operated on OVS that is located
in a custom file path. In order to support this, The path variables in ovs_cmd_dic should be updated with relevant OVS bin directory information.

## How to run
* Run from the terminal by

    `./ovs_cli.py`
