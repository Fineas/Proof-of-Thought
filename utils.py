import os
import sys
import hashlib

"""
Constants
"""
EXP_STORAGE = './successful_exploits'

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