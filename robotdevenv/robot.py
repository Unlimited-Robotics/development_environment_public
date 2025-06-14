import yaml
import pathlib
import argparse

from robotdevenv.ssh import RobotDevSSHHandler as SSHHandler
from robotdevenv.singleton import Singleton

from robotdevenv.constants import DEV_ENV_PATH
from robotdevenv.constants import REMOTE_HOST_WORKSPACES_FOLDER_NAME
from robotdevenv.constants import FILE_ROBOTS_PATH


LOCALHOST_DEFAULT_PLATFORM = 'x86_64'


class RobotDevRobotError(Exception): pass


class RobotDevRobot(Singleton):

    def __init__(self, 
                parser:argparse.ArgumentParser = None,
                name:str = None,
            ):
        if parser is not None:
            parser.add_argument('-r', '--robot', type=str, required=True)
            args = dict(parser.parse_known_args()[0]._get_kwargs())
            name = args['robot']
        elif name == None:
            raise RobotDevRobotError(
                'Either \'name\' or \'parser\' argument must be defined.'
            )

        is_local = (name=='localhost')

        if is_local:
            platform = LOCALHOST_DEFAULT_PLATFORM
        else:
            try:
                with open(FILE_ROBOTS_PATH, 'r') as file:
                    robots_host_info = yaml.safe_load(file)
            except FileNotFoundError:
                raise RobotDevRobotError(
                    f'File \'{FILE_ROBOTS_PATH}\' not found.'
                )
            
            try:
                robot_host_info = robots_host_info[name]
            except KeyError:
                raise RobotDevRobotError(
                    f'Robot \'{name}\' not found in file '
                    f'\'{FILE_ROBOTS_PATH}\'.'
                )
            
            try:
                platform = robot_host_info['platform']
            except KeyError as field:
                raise RobotDevRobotError(
                    f'Field \'{field}\' not found for robot \'{name}\' in '
                    f'file \'{FILE_ROBOTS_PATH}\'.'
                )
        
        # Public attributes
        self.ssh_handler = SSHHandler(name)
        self.name = name
        self.is_local = is_local
        self.platform = platform


    def get_remote_home(self) -> pathlib.Path:
        command_output:str = self.ssh_handler.run_remote(
            command='echo \'$HOME\'',
            get_output=True,
        )
        command_output = command_output.replace('\n','')
        return pathlib.Path(command_output)
    
    
    def get_default_ws_name(self):
        return 'devel'


    def get_host_ws_path(self):
        if self.is_local:
            return DEV_ENV_PATH
        else:
            return self.get_remote_home() / \
                   REMOTE_HOST_WORKSPACES_FOLDER_NAME / \
                   self.get_default_ws_name()
