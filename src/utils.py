import os
import sys
import hashlib

"""
Constants
"""
EXP_STORAGE = '../successful_exploits'

"""
Methods
"""
def load_eval_prompt(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"[!] Error: {file_name} file not found.")
    except Exception as e:
        print(f"[!] An error occurred while reading {file_name}: {e}")

    sys.exit(1)

def store_exploit_string(exploit_string):
    file_name = hashlib.md5(exploit_string.encode()).hexdigest()
    file_path = os.path.join(EXP_STORAGE, file_name)
    
    with open(file_path, 'w') as file:
        file.write(exploit_string)

def print_red(text):
    return f"\033[91m{text}\033[0m"

def print_yellow(text):
    return f"\033[93m{text}\033[0m"

def print_blue(text):
    return f"\033[94m{text}\033[0m"

def print_green(text):
    return f"\033[92m{text}\033[0m"

def print_bold(text):
    return f"\033[1m{text}\033[0m"

def print_underline(text):
    return f"\033[4m{text}\033[0m"