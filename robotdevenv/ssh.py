import pathlib
import subprocess

from robotdevenv.singleton import Singleton


class RobotDevSSHError(Exception): pass
class RobotDevRSyncError(Exception): pass


class RobotDevSSHHandler(Singleton):

    def __init__(self,
                host_alias:str,
            ):
        self.__host_alias = host_alias


    def run_remote(self,
                command:str,
                get_output:bool=False,
                print_output:bool=False,
                force_bash:bool=False,
            ):
        local_command = f'ssh {self.__host_alias} '
        
        if force_bash:
            local_command += f'"bash -c \\"{command}\\""'
        else:
            local_command += command

        process = subprocess.run(
            local_command,
            shell=True,
            capture_output=True,
            text=True,
        )
        
        if process.returncode != 0:
            raise RobotDevSSHError(process.stderr)

        if print_output:
            print(process.stdout)

        if get_output:
            return process.stdout
            

    def sync_to_remote(self,
                origin_path:pathlib.Path,
                destination_path:pathlib.Path,
            ):
        rsync_command = (
            'rsync '
            '--checksum --archive --verbose --stats --delete '
            f'{origin_path} '
            f'{self.__host_alias}:{destination_path}'
        )
        res = subprocess.run(
                rsync_command, shell=True, capture_output=True, text=True
            )
        if res.returncode!=0:
            raise RobotDevRSyncError(res.stderr)
