#! /usr/bin/python3
# -*- coding: utf8 -*-
# author : "Sugesh Chandran"
# Command token dictionary set.

'''
The list has to be in token : [sub_cmd_dic, help string, optional].

'''

ofprototracesub_cmd = {
                       "-generate" : [None, "generate", False]
                       }

ofprototracebr_cmd = {
                      "<[in_port=PORTNO,dl_src=SRCMAC,dl_dst=DSTMAC]>":
                      [ofprototracesub_cmd, "flow details", False]
                      }

ofprototrace_cmd = {
                    "<BRIDGENAME>" : [ofprototracebr_cmd, "Bridge name", False]
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

