#!/usr/bin/env python3
from .banner import displaySetup,art,operationArt
from .colors import *
from .osint import Osint
from time import sleep
import webbrowser

class MainProgram():
    def __init__(self):
        self._continue = True
        self._operation = None
        self._steamKey = 'https://steamcommunity.com/dev/apikey'
        self._path = "./settings/steamKey.txt"
        self.osint = Osint()
        
    def run(self):
        print(art)
        while self._continue:
            try:
                print(operationArt)
                op_value = int(input(f"{BL}${RS} Select operation: ").strip())
                self.inputOperation(op_value)
                self.handle_operation()
            except:
                print(f"{BR}[{RD}x{BR}]{RS}{RD} Invalid option, please select one of the options.{RS}")
    def handle_operation(self):
        op = self._operation
        if op == 0:
            self.scan_target()
        elif op == 1:
            self.setup_key()
        elif op == 2:
            self.exit_program()
    def setup_key(self):
        print(displaySetup)
        print(f"   your key is: {GR}{self.osint._token}{RS}")
        sleep(2)
        webbrowser.open(self._steamKey)
        key = input(F"{BL}${RS} Paste your steam KEY: ").strip()
        if len(key):
            self.osint.setToken(key)
            print(f"\n{BR}[{GR}✓{BR}] {GR}Key saved successfully.{RS}")

    def scan_target(self):
        print(f"\n EXAMPLE: steamcommunity.com/id/{GR}xxxx{RS} <-")
        steam_id = input(F"\n{BL}${RS} TARGET ID: ").strip()
        self.osint.scanProfile(steam_id)
        self.osint.showFriends()
        self.osint.clearList()
    def inputOperation(self, value):
        operationValidation = [0,1,2]
        if(value in operationValidation):
            self._operation = value
        else:
            print(self.stylesProgram(" Operation invalid", "error"))
    def exit_program(self):
        self._continue = False

def main():
    program = MainProgram()
    program.run()


if __name__ == "__main__":
    main() 