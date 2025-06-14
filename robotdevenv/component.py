import yaml
import argparse
from enum import IntEnum

from robotdevenv.robot import RobotDevRobot as Robot

from robotdevenv.constants import CONTAINER_NAME_TEMPLATE
from robotdevenv.constants import ROBOT_GENERIC_PERSISTENT_DATA_PATH
from robotdevenv.constants import ROBOT_COMPONENT_STATIC_DATA_PATH
from robotdevenv.constants import ROBOT_COMPONENT_PERSISTENT_DATA_PATH
from robotdevenv.constants import ROBOT_BUILD_PATH
from robotdevenv.constants import ROBOT_SRC_PATH
from robotdevenv.constants import FOLDER_SRC
from robotdevenv.constants import FOLDER_BUILD
from robotdevenv.constants import FOLDER_GENERIC_PERSISTENT_DATA
from robotdevenv.constants import FOLDER_COMPONENT_STATIC_DATA
from robotdevenv.constants import FOLDER_COMPONENT_PERSISTENT_DATA
from robotdevenv.constants import LOCAL_SRC_PATH
from robotdevenv.constants import GLOBAL_BASE_PATH


class RobotDevComponentError(Exception): pass
class RobotDevComponentNotPlatform(RobotDevComponentError): pass


class BuildImageType(IntEnum):
    DEVEL = 0
    PROD = 1


class RobotDevComponent:

    def __init__(self, 
                parser:argparse.ArgumentParser=None,
                full_name:str=None,
                robot:Robot=None,
                checks:bool=True,
            ):
        if parser is not None:
            parser.add_argument('-c', '--component', type=str, required=True)
            args = dict(parser.parse_known_args()[0]._get_kwargs())
            full_name = args['component']
        elif full_name is None:
            raise RobotDevComponentError(
                'Either \'full_name\' or \'parser\' argument must be defined.'
            )

        try:
            repo_name, name = full_name.split('/')
        except ValueError:
            raise RobotDevComponentError(
                f'Invalid component name \'{full_name}\'. It must have '
                'the format \'<repo>/<component>\'.'
            )
        
        repo_path = LOCAL_SRC_PATH / repo_name
        local_path = repo_path / 'components' / name

        if checks:
            component_desc_path = local_path / f'{name}.yaml'
            try:
                with open(component_desc_path, 'r') as file:
                    component_desc = yaml.safe_load(file)
            except FileNotFoundError:
                raise RobotDevComponentError(
                    f'Component description file \'{component_desc_path}\' not found.'
                )
        
        if checks:
            repo_manifest_path = repo_path / 'manifest.yaml'
            try:
                with open(repo_manifest_path, 'r') as file:
                    repo_manifest = yaml.safe_load(file)
            except FileNotFoundError:
                raise RobotDevComponentError(
                    f'Repository manifest file \'{repo_manifest_path}\' not found.'
                )
        else:
            component_desc = {}
        
        if checks:
            version_prod = repo_manifest['version']
            version_dev = version_prod.replace('.beta','') + '.dev'
        else:
            version_prod = None
            version_dev = None

        src = component_desc.get('src', [])
        ros_pkgs = component_desc.get('ros_pkgs', [])
        display = component_desc.get('display', False)
        sound = component_desc.get('sound', False)
        devices = component_desc.get('devices', False)
        nvidia = component_desc.get('nvidia', False)
        system = component_desc.get('system', False)
        config = component_desc.get('config', False)
        greengrass = component_desc.get('greengrass', False)
        extra_component_flags = component_desc.get('extra-docker-flags', {})

        if checks:
            dockerfile_path = local_path / 'dockerfiles' / \
                f'{robot.platform}.dockerfile'
            if not dockerfile_path.is_file():
                raise RobotDevComponentNotPlatform(
                    f'Dockerfile: \'{dockerfile_path}\' not found.'
                )
        else:
            dockerfile_path = None
        
        if checks:
            dockerfile_prod_path = local_path / 'dockerfiles' / \
                f'{robot.platform}.prod.dockerfile'
            if not dockerfile_prod_path.is_file():
                dockerfile_prod_path = None
        else:
            dockerfile_prod_path = None

        image_name_base = f'{".".join(repo_name.split("_", 2))}.{name}:{robot.platform}'
        if checks:
            image_name_dev = f'{image_name_base}.{version_dev}'
            image_name_prod = f'{image_name_base}.{version_prod}'
        else:
            image_name_dev = None
            image_name_prod = None

        repo = None
        # if checks:
        #     repo = RepoHandler(repo_path)
        #     try:
        #         repo.assert_deploy_branch()
        #         repo.assert_no_local_changes()
        #         repo.assert_pointing_to_tag()
        #     except RobotDevGitError:
        #         image_name_dev += '.changes'
        # else:
        #     repo = None

        container_name = CONTAINER_NAME_TEMPLATE.format(
            repo=repo_name,
            component=name,
        )

        host_path = \
            robot.get_host_ws_path() / FOLDER_SRC / repo_name / 'components' / name

        # Private attributes
        self.robot = robot

        # Public attributes
        self.full_name = full_name
        self.repo_name = repo_name
        self.name = name
        self.local_path = local_path
        self.host_path = host_path
        self.version_dev = version_dev
        self.version_prod = version_prod
        self.component_desc = component_desc
        self.repo_manifest = repo_manifest
        self.src = src
        self.ros_pkgs = ros_pkgs
        self.display = display
        self.sound = sound
        self.nvidia = nvidia
        self.system = system
        self.config = config
        self.greengrass = greengrass
        self.extra_component_flags = extra_component_flags
        self.devices = devices
        self.dockerfile_path = dockerfile_path
        self.dockerfile_prod_path = dockerfile_prod_path
        self.image_name_base = image_name_base
        self.image_name_dev = image_name_dev
        self.image_name_prod = image_name_prod
        self.container_name = container_name


    def get_volumes(self,
                build_type=BuildImageType.DEVEL,
            ):

        host_ws_path = self.robot.get_host_ws_path()

        ## General build folder
        dir_host_build_base = host_ws_path / FOLDER_BUILD / self.full_name
        ## Generic persistent data folder
        dir_host_generic_persistent_data = GLOBAL_BASE_PATH / FOLDER_GENERIC_PERSISTENT_DATA
        ## Component static data folder
        dir_host_component_static_data = self.host_path / FOLDER_COMPONENT_STATIC_DATA
        ## Component persistent data folder
        dir_host_component_persistent_data = GLOBAL_BASE_PATH / FOLDER_COMPONENT_PERSISTENT_DATA / self.name

        volumes = []

        if(build_type==BuildImageType.DEVEL):
            volumes.append((dir_host_build_base, ROBOT_BUILD_PATH))

        volumes.append((dir_host_generic_persistent_data, ROBOT_GENERIC_PERSISTENT_DATA_PATH))

        if(build_type==BuildImageType.DEVEL):
            volumes.append((dir_host_component_static_data, ROBOT_COMPONENT_STATIC_DATA_PATH, 'ro'))

        volumes.append((dir_host_component_persistent_data, ROBOT_COMPONENT_PERSISTENT_DATA_PATH))

        if self.src and build_type==BuildImageType.DEVEL:
            for src_component in self.src:
                dir_host_src_component = host_ws_path / 'src' / src_component
                volumes.append(
                    (dir_host_src_component, f'{ROBOT_SRC_PATH}/{src_component}', 'ro'),
                )   
        
        return volumes
