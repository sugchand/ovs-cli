#! /usr/bin/python3
# -*- coding: utf8 -*-
# author : "Sugesh Chandran"
# CLI framework for easy access of ovs debug commands.

import sys, tty, termios
from ovs_cmd_dic import *
import platform
import argparse
import subprocess
import os

# The global stack for context handling.
gbl_token_stack = []
cmd_input = ""
cur_dic = [ovs_cmd]

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    except:
        print("Failed to read the char")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def push_tokenlist(token_list):
    global gbl_token_stack
    if token_list:
        gbl_token_stack.append(token_list)
        return True
    return False

# Pop the tokenlist from stack, return the default value id stack is empty
def pop_tokenlist(default_tokenlist):
    global gbl_token_stack
    if not gbl_token_stack:
        return default_tokenlist
    return gbl_token_stack.pop()

def print_banner():
    string1 = "                         OVS-CLI                         "
    print("*" * (len(string1) + 4))
    print("*", string1, "*")
    print("*" * (len(string1) + 4))

def print_mask(string, mask_len = 1, mask_char = ' '):
    sys.stdout.write("%s" % string)
    sys.stdout.write("%c" * mask_len % mask_char)
    sys.stdout.flush()

def print_cmd_list(cmd_diclist):
    print("\n")
    if not cmd_diclist:
        return
    for cmd_dic in cmd_diclist:
        for key, value in cmd_dic.items():
            print("   %s         %s" %(key, value[1]))
    print("\n")

def is_token_string(token_key):
    if token_key.startswith('<') and token_key.endswith('>'):
        return True
    return False

'''
Return list of dictionary sublist that has string literal as key.
'''
def find_string_tokens(token_dic):
    token_sublist = []
    for key, data in token_dic.items():
        if not is_token_string(key):
            continue
        token_sublist.append(data[0])
    return token_sublist

def process_token(cmd_input, token_dic):
    last_token = cmd_input.strip()
    token_index = last_token.rfind(' ')
    if token_index == -1:
        last_token = cmd_input
    else:
        last_token = last_token[token_index:]
    last_token = last_token.strip()
    if last_token not in token_dic.keys():
        #the token doesnt match with any key when its a arbitrary string.
        # it is possible that there are multiple arbitrary string in the list.
        # Lets consider sublist from all string pattern.
        token_sublist = find_string_tokens(token_dic)
        return [False, token_sublist]
    token_data = token_dic.get(last_token, None)
    if token_data == None or token_data[0] == None:
        return [False, []]
    return [True, [token_data[0]]]

def process_tokensublist(cmd_input, token_diclist):
    token_sublist = []
    token_strlist = []
    for token_dic in token_diclist:
        [ret, tkn_list] = process_token(cmd_input, token_dic)
        if ret:
            token_sublist = token_sublist + tkn_list
            return token_sublist
        else:
            # Can be a string match, So lets populate in different list.
            token_strlist = token_strlist + tkn_list
    return token_strlist

def clean_cli():
    global gbl_token_stack
    global cmd_input
    global cur_dic
    gbl_token_stack = []
    cmd_input = ""
    cur_dic = [ovs_cmd]

def do_execute_cmd(cmd):
    global OVS_SUDO_CMD
    global OVS_BIN_PATH

    if not cmd:
        return True
    exec_cmd = []
    exec_cmd.append(cmd)
    if OVS_SUDO_CMD:
        #Need to run command in sudo mode.
        ovs_sudo = OVS_SUDO_CMD.split()
    exec_cmd = ovs_sudo + exec_cmd

    exec_cmd = filter(None, exec_cmd)
    if OVS_BIN_PATH:
        cmd_env = os.environ.copy()
        cmd_env["PATH"] = OVS_BIN_PATH + ":" + cmd_env["PATH"]
    try:
        out = subprocess.Popen(exec_cmd, env = cmd_env)
    except Exception as e:
        raise e
    out.wait()

def parse_pgm_args():
    global OVS_BIN_PATH
    global OVS_SUDO_CMD

    parser = argparse.ArgumentParser(description="ovs-cli    :"
                                     "    CLI for OVS Debugging")
    parser.add_argument('-p','--path', help='Absolute path to OVS binary files, seperated by :',
                        type=str, default="",dest="path",required=False)
    parser.add_argument('-s','--sudo', help='Execute commands in sudo',
                        action="store_true", dest="sudo_run", default=False,
                        required=False)
    args = parser.parse_args()
    if args.path:
        OVS_BIN_PATH = args.path
    if args.sudo_run:
        OVS_SUDO_CMD = "sudo -E"

if __name__ == '__main__':
    if platform.system() != 'Linux':
        print("OVS-CLI supports only on Linux " +
                                     "platform for now")
        exit(1)
    global OVS_CLI_CMD_PROMPT

    parse_pgm_args()
    print_banner()
    OVS_CLI_CMD_PROMPT = "\r " + OVS_CLI_CMD_PROMPT + " "

    while(1) :
        # Reading the character as bytes.
        sys.stdout.write("%s%s" % (OVS_CLI_CMD_PROMPT, cmd_input))
        sys.stdout.flush()
        ch = getch()
        ch_byte = ord(ch)

        #print(ch_byte)
        if ch_byte == 0x20: #Space handling.
            token_sublist = process_tokensublist(cmd_input, cur_dic)
            if not token_sublist:
                # Failed to find the token, cannot do anything.
                continue
            push_tokenlist(cur_dic) # Push to the stack for future reference.
            cur_dic = token_sublist
        elif ch_byte == 0x9 or ch_byte == 0x3F: # Tab/? handling.
            print_cmd_list(cur_dic)
            continue
        elif ch_byte == 0x7F: #Backspace,DEL handling
            if cmd_input:
                if cmd_input.endswith(' '):
                    cur_dic = pop_tokenlist([ovs_cmd])
                cmd_input = cmd_input[:-1]
                # Mask the deleted one 
                #sys.stdout.write("\r ovs-cli# %s " % (cmd_input))
                #sys.stdout.flush()
                print_mask(OVS_CLI_CMD_PROMPT + cmd_input)
            continue
        elif ch_byte == 0xD: # New line
            try:
                do_execute_cmd(cmd_input)
            except:
                print("\nInvalid command..\n")
            else:
                clean_cli()
            continue
        elif ch_byte < 0x20 or ch_byte > 0x7E: # Special characters
            exit()

        #ch = ch.decode("utf-8")
        cmd_input = cmd_input + ch
