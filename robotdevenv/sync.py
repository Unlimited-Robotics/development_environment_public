import pathlib

from robotdevenv.component import RobotDevComponent as Component
from robotdevenv.robot import RobotDevRobot as Robot
from robotdevenv.singleton import Singleton

from robotdevenv.constants import FOLDER_SRC
from robotdevenv.constants import LOCAL_SRC_PATH


class RobotDevSyncError(Exception): pass


class RobotDevSyncHandler(Singleton):

    def __init__(self,
                component:Component,
                robot:Robot,
            ):
        self.__component = component
        self.__robot = robot


    def sync_to_robot(self):
        print(f'🔁💻 Synchronizing to remote host \'{self.__robot.name}\'...')
        print()

        remote_ws_path = self.__robot.get_host_ws_path()

        # Repositories
        print(f'  ➡️  Creating remote repos path ... ', end='')
        remote_repos_path = remote_ws_path / FOLDER_SRC
        self.__robot.ssh_handler.run_remote(f'mkdir -p {remote_repos_path}')
        print('✅')

        for src_component in self.__component.src:
            print(
                f'  ➡️  Synchronizing {FOLDER_SRC}/{src_component} ... ', end=''
            )
            origin_path:pathlib.Path = LOCAL_SRC_PATH / src_component
            if not origin_path.is_dir():
                raise RobotDevSyncError(
                    f'Source component \'{src_component}\' does not exist. '
                    f'Folder \'{origin_path}\' not found'
                )
            
            self.__robot.ssh_handler.sync_to_remote(
                origin_path=origin_path, 
                destination_path=remote_repos_path,
            )
            
            print('✅')
        
        print()

        
