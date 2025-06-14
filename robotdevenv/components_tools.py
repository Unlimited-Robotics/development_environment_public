#!/usr/bin/env python3

import shutil
from pathlib import Path
import re

def create_components_group_form_template(group_name: str) -> None:
    """
    Creates a new component group by copying the template_components_group directory.
    
    Args:
        group_name (str): Name for the new component group
        
    Raises:
        ValueError: If the component name is invalid or already exists
        FileNotFoundError: If the template directory is not found
        Exception: For any other error during the copy process
    """
    # Prevent using template_components_group as the new name
    if group_name == "template_components_group":
        raise ValueError("Cannot use 'template_components_group' as the new component name")

    # Define paths
    src_dir = Path("src")
    template_dir = src_dir / "template_components_group"
    new_component_dir = src_dir / group_name

    # Check if template directory exists
    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found in {template_dir}")

    # Check if new directory already exists
    if new_component_dir.exists():
        raise ValueError(f"A component with name {group_name} already exists")

    # Copy template directory to new directory
    shutil.copytree(template_dir, new_component_dir)


def rename_component(group_name: str, component_name: str, new_component_name: str) -> None:
    """
    Renames a component within a components group.
    
    Args:
        group_name (str): Name of the components group
        component_name (str): Current name of the component
        new_component_name (str): New name for the component
        
    Raises:
        ValueError: If the names are invalid or the new name already exists
        FileNotFoundError: If the component or components group is not found
        Exception: For any other error during the rename process
    """
    # Prevent using template_components_group or template_component
    if group_name == "template_components_group":
        raise ValueError("Cannot rename components in template_components_group")
    if new_component_name == "template_component":
        raise ValueError("Cannot use 'template_component' as the new component name")

    # Define paths
    src_dir = Path("src")
    components_dir = src_dir / group_name / "components"
    old_component_dir = components_dir / component_name
    new_component_dir = components_dir / new_component_name

    # Check if components group exists
    if not components_dir.exists():
        raise FileNotFoundError(f"Components group '{group_name}' not found")

    # Check if old component exists
    if not old_component_dir.exists():
        raise FileNotFoundError(f"Component '{component_name}' not found in {group_name}")

    # Check if new component name already exists
    if new_component_dir.exists():
        raise ValueError(f"A component with name '{new_component_name}' already exists in {group_name}")

    # Check if the YAML file exists
    old_yaml_file = old_component_dir / f"{component_name}.yaml"
    if not old_yaml_file.exists():
        raise FileNotFoundError(f"YAML file '{component_name}.yaml' not found in component directory")

    try:
        # Rename the component directory
        shutil.move(str(old_component_dir), str(new_component_dir))
        
        # Rename the YAML file
        new_yaml_file = new_component_dir / f"{new_component_name}.yaml"
        old_yaml_file = new_component_dir / f"{component_name}.yaml"
        old_yaml_file.rename(new_yaml_file)
    except Exception as e:
        # If something goes wrong, try to revert the changes
        if new_component_dir.exists():
            new_component_dir.rename(old_component_dir)
        raise Exception(f"Error renaming component: {str(e)}")


def create_component_from_template(group_name: str, component_name: str) -> None:
    """
    Creates a new component by copying the template component and renaming it.
    
    Args:
        group_name (str): Name of the components group where the new component will be created
        component_name (str): Name for the new component
        
    Raises:
        ValueError: If the component name is invalid or already exists
        FileNotFoundError: If the template or components group is not found
        Exception: For any other error during the creation process
    """
    # Prevent using template_component as the new name
    if component_name == "template_component":
        raise ValueError("Cannot use 'template_component' as the new component name")

    # Define paths
    src_dir = Path("src")
    template_component_dir = src_dir / "template_components_group" / "components" / "template_component"
    target_components_dir = src_dir / group_name / "components"
    target_component_dir = target_components_dir / "template_component"

    # Check if template component exists
    if not template_component_dir.exists():
        raise FileNotFoundError("Template component not found in template_components_group")

    # Check if components group exists
    if not target_components_dir.exists():
        raise FileNotFoundError(f"Components group '{group_name}' not found")

    # Check if component with new name already exists
    if (target_components_dir / component_name).exists():
        raise ValueError(f"A component with name '{component_name}' already exists in {group_name}")

    try:
        # Copy template component to target location
        shutil.copytree(template_component_dir, target_component_dir)
        
        # Rename the component to the desired name
        rename_component(group_name, "template_component", component_name)
    except Exception as e:
        # If something goes wrong, try to clean up
        if target_component_dir.exists():
            shutil.rmtree(target_component_dir)
        raise Exception(f"Error creating component: {str(e)}")


def rename_package_rclpy(group_name: str, package_name: str, new_package_name: str) -> None:
    """
    Renames an rclpy package and all its references.
    
    Args:
        group_name (str): Name of the group containing the package
        package_name (str): Current name of the package
        new_package_name (str): New name for the package
        
    Raises:
        ValueError: If the names are invalid or the new name already exists
        FileNotFoundError: If the package or required files are not found
        Exception: For any other error during the rename process
    """
    # Define paths
    src_dir = Path("src")
    old_package_dir = src_dir / group_name / package_name
    new_package_dir = src_dir / group_name / new_package_name

    # Check if package exists and is an rclpy package
    if not old_package_dir.exists():
        raise FileNotFoundError(f"Package '{package_name}' not found in {group_name}")
    
    if not (old_package_dir / "setup.py").exists():
        raise ValueError(f"Package '{package_name}' is not an rclpy package (setup.py not found)")

    # Check if new package name already exists
    if new_package_dir.exists():
        raise ValueError(f"A package with name '{new_package_name}' already exists in {group_name}")

    try:
        # 1. Rename the main package directory
        shutil.move(str(old_package_dir), str(new_package_dir))

        # 2. Rename the inner package directory
        inner_old_dir = new_package_dir / package_name
        inner_new_dir = new_package_dir / new_package_name
        if inner_old_dir.exists():
            shutil.move(str(inner_old_dir), str(inner_new_dir))

        # 3. Rename the resource file
        resource_dir = new_package_dir / "resource"
        if resource_dir.exists():
            old_resource_file = resource_dir / package_name
            new_resource_file = resource_dir / new_package_name
            if old_resource_file.exists():
                shutil.move(str(old_resource_file), str(new_resource_file))

        # 4. Update references in configuration files
        files_to_update = ["package.xml", "setup.cfg", "setup.py"]
        for file_name in files_to_update:
            file_path = new_package_dir / file_name
            if file_path.exists():
                # Read the file content
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Replace all occurrences of the package name
                new_content = re.sub(
                    re.escape(package_name),
                    new_package_name,
                    content
                )
                
                # Write the updated content back
                with open(file_path, 'w') as f:
                    f.write(new_content)

    except Exception as e:
        # If something goes wrong, try to revert the changes
        if new_package_dir.exists():
            shutil.move(str(new_package_dir), str(old_package_dir))
        raise Exception(f"Error renaming package: {str(e)}")


def create_package_rclpy(group_name: str, package_name: str) -> None:
    """
    Creates a new rclpy package by copying the template package and renaming it.
    
    Args:
        group_name (str): Name of the group where the new package will be created
        package_name (str): Name for the new package
        
    Raises:
        ValueError: If the package name is invalid or already exists
        FileNotFoundError: If the template package is not found
        Exception: For any other error during the creation process
    """
    # Prevent using template names
    if group_name == "template_components_group":
        raise ValueError("Cannot use 'template_components_group' as the group name")
    if package_name == "template_raya_package":
        raise ValueError("Cannot use 'template_raya_package' as the package name")

    # Define paths
    src_dir = Path("src")
    template_package_dir = src_dir / "template_components_group" / "template_raya_package"
    target_package_dir = src_dir / group_name / "template_raya_package"

    # Check if template package exists
    if not template_package_dir.exists():
        raise FileNotFoundError("Template package not found in template_components_group")

    # Check if group exists
    if not (src_dir / group_name).exists():
        raise FileNotFoundError(f"Group '{group_name}' not found")

    # Check if package with new name already exists
    if (src_dir / group_name / package_name).exists():
        raise ValueError(f"A package with name '{package_name}' already exists in {group_name}")

    try:
        # Copy template package to target location
        shutil.copytree(template_package_dir, target_package_dir)
        
        # Rename the package to the desired name
        rename_package_rclpy(group_name, "template_raya_package", package_name)
    except Exception as e:
        # If something goes wrong, try to clean up
        if target_package_dir.exists():
            shutil.rmtree(target_package_dir)
        raise Exception(f"Error creating package: {str(e)}") 