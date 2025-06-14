import colorama

def error(msg:str):
    print(f'{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} {msg}')

def warning(msg:str):
    print(f'{colorama.Fore.YELLOW}WARNING:{colorama.Style.RESET_ALL} {msg}')

def success(msg:str):
    print(f'{colorama.Fore.GREEN}SUCCESS:{colorama.Style.RESET_ALL} {msg}')

def info(msg:str):
    print(f'{colorama.Fore.GREEN}{msg}{colorama.Style.RESET_ALL}')

def info_error(msg:str):
    print(f'{colorama.Fore.RED}{msg}{colorama.Style.RESET_ALL}')

def abort(msg:str):
    print()
    print(f'{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} {msg}')
    print()
    exit()
