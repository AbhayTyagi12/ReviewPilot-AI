import subprocess


def run(user_input):
    subprocess.call("echo " + user_input, shell=True)
    return eval(user_input)