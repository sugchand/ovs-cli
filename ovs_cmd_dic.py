'''
Created on 16 Mar 2017

@author: sugesh
'''

'''
The list has to be in token : [sub_cmd_dic, help string, optional].
'''

ofprototracesub_cmd = {
                       "-generate" : [None, "generate", False]
                       }

ofprototracebr_cmd = {
                      "<[in_port=<PORT-NO>,dl_src=<SRC-MAC,dl_dst=<DST-MAC>]>":
                      [ofprototracesub_cmd, "flow details", False]
                      }

ofprototrace_cmd = {
                    "<BRIDGE-NAME>" : [ofprototracebr_cmd, "Bridge name", False]
                    }

ovsappctl_cmd = {
                 "ofproto/trace" : [ofprototrace_cmd, "Trace the OF flow", False],
                "dpctl/dump-flows" : [None, "Show datapath flows", False],
                "dpctl/show" : [None, "Show datapath port and config", False]
                }

ovsvsctl_cmd = {
                "show" : [None, "Show ovs-vswitchd configuration", False]
                }

ovs_cmd = {
           "ovs-vsctl" : [ovsvsctl_cmd, "Configured ovs-vswitchd.", False],
           "ovs-appctl" : [ovsappctl_cmd, "OVS run time command options.", False]
           }

