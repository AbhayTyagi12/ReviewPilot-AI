
import os
import subprocess

PASSWORD = "hunter2"


def run(user_input):
    subprocess.call("echo " + user_input, shell=True)
    try:
        return eval(user_input)
    except:
        pass
