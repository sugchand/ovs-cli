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
from collections import deque

# The global stack for context handling.
gbl_token_stack = []
cmd_input = ""
cur_dic = [ovs_cmd]

global OVS_CLI_HISTORY_SIZE
# The history stack holds the command history.
# The size of history is limited to OVS_CLI_HISTORY_SIZE
# Each element in the deque holds a list with members
# token_stack, cmd_input and cur_dic.
cmd_history_stack = deque(maxlen = OVS_CLI_HISTORY_SIZE)
# The index of current element in history. Reset it to -1 if its points to
# nothing.
cmd_history_index = -1

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

# Add the current command to the history for the future use.
# the token_stack, current_dic and cmd string stored in history.
def add_cmd_to_history():
    global cmd_history_stack
    global cmd_history_index
    if not cmd_input:
        return
    cmd_history_stack.append([cmd_input, cur_dic, gbl_token_stack])
    cmd_history_index = len(cmd_history_stack)

def load_prevcmd_from_history():
    global cmd_history_stack
    global cmd_history_index
    global cmd_input
    global cur_dic
    global gbl_token_stack

    if cmd_history_index <= 0:
        # Nothing to load, return
        return False

    cmd_history_index -= 1
    curr_cmdset = cmd_history_stack[cmd_history_index]
    cmd_input = curr_cmdset[0] # the command string.
    cur_dic = curr_cmdset[1]
    gbl_token_stack = curr_cmdset[2]
    return True

def load_nxtcmd_from_history():
    global cmd_history_stack
    global cmd_history_index
    global cmd_input
    global cur_dic
    global gbl_token_stack

    if cmd_history_index >= len(cmd_history_stack) - 1:
        # Nothing to load, return
        return False
    cmd_history_index += 1
    curr_cmdset = cmd_history_stack[cmd_history_index]
    cmd_input = curr_cmdset[0]
    cur_dic = curr_cmdset[1]
    gbl_token_stack = curr_cmdset[2]
    return True

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
    if(mask_len):
        sys.stdout.write("{}".format(mask_char) * mask_len)
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

def process_escape_chars():
    # Process the up and down arrow
    # Up and down arrows are combination of 3 ascci values
    # Up : 0x1B, 0x5B, 0x41(27, 91, 65)
    # Down 0x1B, 0x5B, 0x42(27, 91, 66)
    global cmd_input
    old_cmd = cmd_input
    ch_byte = ord(getch())
    if ch_byte != 0x5B:
        return
    ch_byte = ord(getch())
    if ch_byte == 0x41: #Up arrow, get previous command from history.
        res = load_prevcmd_from_history()
    elif ch_byte == 0x42: #Down arrow, get next command from the history.
        res = load_nxtcmd_from_history()
    if res:
        # The command is loaded successfully from history, Clean the terminal.
        print_mask(OVS_CLI_CMD_PROMPT, mask_len=len(old_cmd))

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

    cmd_env = os.environ.copy()
    if OVS_BIN_PATH:
        cmd_env["PATH"] = OVS_BIN_PATH + ":" + cmd_env["PATH"]
    if OVS_SUDO_CMD:
        #Need to run command in sudo mode.
        cmd = OVS_SUDO_CMD + " env PATH=$PATH:" + OVS_BIN_PATH + " " + cmd
    exec_cmd = cmd.split()
    exec_cmd = filter(None, exec_cmd)
    try:
        print("\n")
        out = subprocess.Popen(exec_cmd, env = cmd_env)
        out.wait()
        return out.returncode
    except Exception as e:
        raise e

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

        if ch_byte == 0x1B: # Escape character, Read more characters to process.
            process_escape_chars()
            continue
        elif ch_byte == 0x20:  #Space handling.
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
                res = do_execute_cmd(cmd_input)
            except Exception as e:
                print("\nInvalid command[%s]..\n" % e)
            finally:
                add_cmd_to_history() # Add the command to the cmd history.
                clean_cli()
                print_mask(OVS_CLI_CMD_PROMPT, mask_len=0)
            continue
        elif ch_byte < 0x20 or ch_byte > 0x7E: # Special characters
            exit()

        #ch = ch.decode("utf-8")
        cmd_input = cmd_input + ch
