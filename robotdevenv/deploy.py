import os
import re
import yaml
import lxml
import json
import lxml.etree
import argparse
import paramiko
from pathlib import Path

from robotdevenv.singleton import Singleton
from robotdevenv.git import RobotDevRepositoryHandler as RepositoryHandler
from robotdevenv.robot import RobotDevRobot as Robot
from robotdevenv.component import RobotDevComponent as Component
from robotdevenv.docker import RobotDevDockerHandler as DockerHandler
from robotdevenv.docker import BuildImageType
from robotdevenv.component import RobotDevComponentNotPlatform

from robotdevenv.constants import LOCAL_SRC_PATH
from robotdevenv.constants import FOLDER_COMPONENTS
from robotdevenv.constants import FILE_ROBOTS_PATH
from robotdevenv.constants import DEPLOY_DEFAULT_BUILDING_HOST


class RobotDevDeployError(Exception):
    pass


class RobotDevDeployHandler(Singleton):

    def __init__(self,
                 parser: argparse.ArgumentParser,
                 ):
        parser: argparse.ArgumentParser = argparse.ArgumentParser()
        parser.add_argument('--repo', type=str, required=True)
        parser.add_argument('-s', '--skip-repo-steps', action='store_true')

        args = dict(parser.parse_known_args()[0]._get_kwargs())
        repo_name = args['repo']

        repo_path = LOCAL_SRC_PATH / repo_name
        manifest_path = repo_path / 'manifest.yaml'
        components_path = repo_path / FOLDER_COMPONENTS
        repo = RepositoryHandler(repo_path)

        self.dependencies_versions: dict = {}
        self.manifest: dict = {}

        # Public attributes
        self.repo_name = repo_name
        self.skip_repo_steps = args['skip_repo_steps']
        self.last_version: str = None
        self.new_version: str = None
        self.build_host: str = None
        self.robot = None
        self.repo_path = repo_path
        self.manifest_path = manifest_path
        self.components_path = components_path
        self.repo = repo
        self.robot: Robot = None
        self.components: list[Component] = []
        self.docker_handlers: list[DockerHandler] = []
        self.components_paths: list[Path] = []

    def deploy(self) -> None:

        self.read_manifest()

        print(f'🔁  Retrieving \'{self.repo_name}\' repository information...')
        self.repo.fetch()

        # Main repository asserts
        print(f'🤨  Checking \'{self.repo_name}\' repository status...')
        self.repo.assert_deploy_branch()
        self.repo.assert_no_local_changes()
        self.repo.assert_branch_updated()

        if not self.skip_repo_steps:
            self.repo.assert_no_pointing_to_tag()
            self.last_tag_same_as_manifest()
            self.last_version = str(self.repo.get_last_tag())
            print(f'✅  Main repository \'{self.repo_name}\' asserts OK.')
            print()

            self.process_dependencies()

            print(
                f'🏅 Last version \'{self.repo.repo_name}\': '
                f'{self.repo.get_last_tag()}'
            )
            print()

            self.ask_new_version()
            self.assert_version_order()

            print(f'🔼 Update versions in repository files...')
            print()

            self.update_manifest()
            self.update_packages_xml()

            print(f'🔼 Update repo...')
            print()

            self.repo.create_commit(self.new_version)
            self.repo.create_tag(self.new_version)
            self.repo.push_repository()

            print()

        print(f'🛢️ Building docker images...')

        self.components_paths = self.get_components_paths()
        if self.components_paths:
            self.ask_building_host()
            self.create_build_artifacts()
            self.build_components()
            self.push_components()

        print('🎉🎉 Deploy Process Completed! 🎉🎉')

    def last_tag_same_as_manifest(self) -> None:
        manifest: dict = {}
        version_manifest: str = ''

        # Get manifest file in the repo folder
        try:
            with open(self.manifest_path, 'r') as file:
                manifest = yaml.safe_load(file)
        except FileNotFoundError:
            raise RobotDevDeployError(
                f'Manifest of repo \'{self.repo_name}\' not found.'
            )

        # Get manifest version
        version_manifest = str(manifest['version'])
        if version_manifest == None:
            raise RobotDevDeployError(
                f'File \'{self.manifest_path}\' does not have \'version\' key.'
            )

        # Check version from manifest file is the same as the last tag
        last_tag: str = self.repo.get_last_tag().name
        if version_manifest != last_tag:
            raise RobotDevDeployError(
                f'The last tag \'{last_tag}\' is not the same as '
                f'\'{version_manifest}\' in the manisfest.yaml file.'
            )

    def process_dependencies(self) -> None:

        components_paths: list = self.get_components_paths()
        deps: set[str] = self.get_deps(components_paths)

        if not deps:
            return

        print()
        print(f'⚙️  Processing dependencies...')
        print()

        deps_repos = self.get_deps_repos(deps)
        self.__fetch_dependency_repo(deps_repos)
        self.__check_in_main_branch(deps_repos)
        self.__check_changes_whitout_commit(deps_repos)
        self.__check_pointing_to_tag(deps_repos)

        for repo in deps_repos:
            self.dependencies_versions[repo.repo_name] = str(
                repo.get_last_tag())

        print()

    # Browse through the components folder and get all folders

    def get_components_paths(self) -> list:
        if not self.components_path.is_dir():
            return []
        path = Path(self.components_path)
        folder_list = [folder for folder in path.iterdir()
                       if folder.is_dir()]
        return folder_list

    # Get src dependencies from yaml files. Return a list dependencies without duplicates
    def get_deps(self,
                 components_paths: list,
                 ) -> list:

        src_dependencies_list: set[str] = set()  # A set to avoid duplicates

        for component_path in components_paths:
            desc_path = component_path / f'{component_path.name}.yaml'
            data: dict = yaml.safe_load(open(desc_path, 'r'))
            if 'src' not in data:
                continue
            for dependency in data['src']:
                src_dependencies_list.add(dependency)

        # Remove the current repository from the list
        if self.repo_path.name in src_dependencies_list:
            src_dependencies_list.remove(self.repo_path.name)

        return src_dependencies_list

    def get_deps_repos(self, list_dependencies: set) -> list:
        repo_dependencies_list: list = []
        for dependency in list_dependencies:
            LOCAL_PATH_REPOSITORY = LOCAL_SRC_PATH / dependency
            repo_dependency = RepositoryHandler(LOCAL_PATH_REPOSITORY)
            repo_dependencies_list.append(repo_dependency)
        return repo_dependencies_list

    def __fetch_dependency_repo(self, repo_dependencies_list: list[RepositoryHandler]) -> None:

        print(f'🔻  Fetching dependency repositories...')

        for repo in repo_dependencies_list:
            repo.fetch()

    def __check_in_main_branch(self, repo_dependencies_list: list[RepositoryHandler]) -> None:

        print(f'🔵  Check dependencies in main branch...')

        for repo in repo_dependencies_list:
            print(f'    📦 Check if {repo.repo_name} is in main branch!')
            repo.assert_deploy_branch()

    def __check_changes_whitout_commit(self, repo_dependencies_list: list[RepositoryHandler]) -> None:

        print(f'🟠  Check changes without commit...')

        for repo in repo_dependencies_list:
            repo.assert_no_local_changes()

    def __check_pointing_to_tag(self, repo_dependencies_list: list[RepositoryHandler]) -> None:

        print(f'🟡  Check dependencies pointing to tag...')

        for repo in repo_dependencies_list:
            print(f'    📦 Check if {repo.repo_name} is pointing to a Tag!')
            repo.assert_pointing_to_tag()

    def ask_new_version(self) -> None:
        new_version: str = input(f'🎹 Please type the new version: ')
        print()
        pattern = r'^(\d+)\.(\d+)(\.beta)?$'
        coincidence = re.match(pattern, new_version)

        if coincidence is None:
            raise RobotDevDeployError(
                'Version format is not valid. The format should be X.X(.beta)')
        else:
            self.new_version = new_version

    def get_version_tuple(self, version: str) -> tuple[int, int, bool]:

        pattern = r'^(\d+)\.(\d+)(\.beta)?$'

        coincidence = re.match(pattern, version)

        if coincidence is None:
            raise RobotDevDeployError(
                'Last version format is not valid. It must be X.X(.beta).'
            )

        return (
            int(coincidence.group(1)),  # major
            int(coincidence.group(2)),  # minor
            coincidence.group(3),       # tag
        )

    def assert_version_order(self) -> None:
        last_version_tuple = self.get_version_tuple(self.last_version)

        expected_versions = [
            f'{last_version_tuple[0]}.{last_version_tuple[1]+1}',
            f'{last_version_tuple[0]}.{last_version_tuple[1]+1}.beta',
            f'{last_version_tuple[0]+1}.0.beta',  # <- Warning [2]
        ]

        if self.new_version not in expected_versions:
            raise RobotDevDeployError('New version order is not valid.')

        if self.new_version == expected_versions[2]:
            answer: str = input(
                'Are you sure you want to deploy this mayor version? (y/N): '
            )
            if answer.lower() != 'y':
                print()
                print('😵 Aborted')
                print()
                exit()

    def read_manifest(self) -> None:
        # Get manifest file in the repo folder
        try:
            with open(self.manifest_path, 'r') as file:
                self.manifest = yaml.safe_load(file)
        except FileNotFoundError:
            raise RobotDevDeployError(
                f'File \'{self.manifest_path}\' not found.'
            )

    def update_manifest(self) -> None:

        # Update manifest version
        self.manifest['version'] = self.new_version

        self.manifest['depedencies'] = self.dependencies_versions

        with open(self.manifest_path, 'w') as file:
            yaml.dump(self.manifest, file)

    def update_packages_xml(self) -> None:

        path = Path(self.repo_path)

        # Get list of package xml files
        list_path_packages_xml_files: list = []
        for folder in path.iterdir():
            if folder.is_dir() and not folder.name.endswith('.git') and \
                    not folder.name.startswith('components') and \
                    not folder.name.startswith('.vscode') and \
                    not folder.name.startswith('.github'):
                file_path = folder / 'package.xml'
                if not file_path.exists():
                    print(f'File \'{file_path}\' not found.')
                    continue
                list_path_packages_xml_files.append(folder / 'package.xml')

        if len(list_path_packages_xml_files) == 0:
            return

        for file in list_path_packages_xml_files:
            parser = lxml.etree.XMLParser(remove_blank_text=True)
            tree = lxml.etree.parse(file, parser)
            root = tree.getroot()

            version_tag = root.find('version')
            if version_tag is not None:
                xml_new_version = self.new_version.replace('.beta', '')
                xml_new_version += '.0'
                version_tag.text = xml_new_version
                xml_str = lxml.etree.tostring(tree, pretty_print=True,
                                              xml_declaration=True,
                                              encoding='utf-8'
                                              ).decode("utf-8")

                xml_str = xml_str.replace(" encoding='utf-8'", '').strip()

                with open(file, 'w') as f:
                    f.write(xml_str)

    def ask_building_host(self):

        try:
            with open(FILE_ROBOTS_PATH, 'r') as file:
                robots_host_info: dict = yaml.safe_load(file)
        except FileNotFoundError:
            raise RobotDevDeployError(
                f'File \'{FILE_ROBOTS_PATH}\' not found.'
            )

        available_hosts = list(robots_host_info.keys())
        available_hosts.sort()
        available_hosts.insert(0, 'localhost')

        print()
        print(f'🕹️  Available hosts:')
        print()
        for host in available_hosts:
            print(f'  - {host}')

        print()
        build_host: str = input(
            '🎹 Please enter the name of the building host '
            f'[{DEPLOY_DEFAULT_BUILDING_HOST}]: '
        )

        if not build_host:
            build_host = DEPLOY_DEFAULT_BUILDING_HOST

        if (build_host != 'localhost') and (build_host not in available_hosts):
            raise RobotDevDeployError(f'Host {build_host} not found.')

        self.build_host = build_host

        # ssh = paramiko.SSHClient()
        # ssh.load_system_host_keys()

        # ssh_config = paramiko.SSHConfig()
        # user_config_file = os.path.expanduser("~/.ssh/config")

        # with open(user_config_file) as f:
        #     ssh_config.parse(f)

        # config = ssh_config.lookup(build_host)

        # if config is not None:
        #     try:
        #         host = config.get("hostname")
        #         user = config.get("user")
        #         ssh.connect(hostname=host, username=user)
        #         print(f'     🟢 Host {build_host}, {host} available!')
        #         ssh.close()
        #     except paramiko.ssh_exception.NoValidConnectionsError:
        #         raise RobotDevDeployError(
        #             f'❌ Unable to connect to host {build_host}. Host: {host}, User: {user}')
        #     except paramiko.ssh_exception.AuthenticationException:
        #         raise RobotDevDeployError(
        #             f'❌ Authentication failed for host {build_host}. Exiting...')
        #     except paramiko.ssh_exception.PasswordRequiredException:
        #         raise RobotDevDeployError(
        #             f'❌ Password required for host {build_host}. Exiting...')
        #     except Exception:
        #         raise RobotDevDeployError(
        #             f'❌ Host {build_host} not found. Exiting...')
        #     finally:
        #         ssh.close()

    def __get_ssh_hosts(self) -> list[str]:
        # print(f'🔑  Get ssh hosts...')

        ssh_config = paramiko.SSHConfig()
        try:
            user_config_file = os.path.expanduser("~/.ssh/config")
            with open(user_config_file) as f:
                ssh_config.parse(f)

        except Exception:
            raise RobotDevDeployError(
                '❌ SSH config file not found. Exiting...')

        # Getting hosts from the config file
        hosts: list[str] = [
            host for host in ssh_config.get_hostnames()]

        # Removing wildcards
        hosts = [host for host in hosts if '*' not in host]

        return hosts

    def create_build_artifacts(self):
        self.robot = Robot(name=self.build_host)
        self.components = []
        self.docker_handlers = []

        print(f'🧩 Collecting components:')
        print()

        for component_path in self.components_paths:
            component_name = component_path.name
            print(f'  - {component_name}: ', end='')
            try:
                self.components.append(Component(
                    full_name=f'{self.repo_name}/{component_path.name}',
                    robot=self.robot,
                ))
                self.docker_handlers.append(DockerHandler(
                    component=self.components[-1], robot=self.robot
                ))
                print('✅ OK.')
            except RobotDevComponentNotPlatform:
                print(
                    '❌ Not dockerfile for platform '
                    f'\'{self.robot.platform}\'.'
                )
                continue
        print()

    def build_components(self):
        print(f'🛠️ Building components...')
        print()

        for docker_handler in self.docker_handlers:
            component = docker_handler.component
            print()
            print(f'🧩 Component: \'{component.full_name}\'')
            print()
            print(f'  Development image...')
            print()
            docker_handler.build_image(BuildImageType.DEVEL)
            print(f'  Production image...')
            print()

            metadata = {
                'REPO_NAME': self.repo_name,
                'COMPONENT_NAME': component.name,
                'REPO_METADATA': json.dumps(self.manifest),
                'COMPONENT_METADATA': json.dumps(component.component_desc),
            }

            docker_handler.build_image(BuildImageType.PROD, metadata)
        print()

    def push_components(self):
        print(f'⬆️  Pushing components...')
        print()

        for docker_handler in self.docker_handlers:
            component = docker_handler.component
            print()
            print(f'🧩 Component: \'{component.full_name}\'')
            print()
            print(f'  Development image...')
            print()
            docker_handler.push_image(BuildImageType.DEVEL)
            print()
            print(f'  Production image...')
            print()
            docker_handler.push_image(BuildImageType.PROD)
        print()
