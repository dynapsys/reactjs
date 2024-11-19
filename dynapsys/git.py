#!/usr/bin/python3
import subprocess
import os
import logging
import sys
import traceback
import re

def is_valid_git_url(url):
    """Check if URL is a valid Git address"""
    git_patterns = [
        r'^https?://github\.com/[\w-]+/[\w.-]+(?:\.git)?$',
        r'^git@github\.com:[\w-]+/[\w.-]+(?:\.git)?$',
        r'^https?://gitlab\.com/[\w-]+/[\w.-]+(?:\.git)?$',
        r'^https?://bitbucket\.org/[\w-]+/[\w.-]+(?:\.git)?$'
    ]
    is_valid = any(re.match(pattern, url) for pattern in git_patterns)
    logging.info(f"Checking git URL: {url} - {'valid' if is_valid else 'invalid'}")
    return is_valid

def check_git_installation():
    """Check if git is installed and available"""
    try:
        version = subprocess.check_output(['git', '--version']).decode().strip()
        logging.info(f"Git version: {version}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Git not found: {str(e)}")
        return False
    except FileNotFoundError:
        logging.error("Git command not found")
        return False

def clone_git_repo(git_url, target_dir):
    """Clone git repository to specified directory"""
    try:
        # Check git installation
        if not check_git_installation():
            raise Exception("Git is not installed")

        logging.info(f"Starting git clone: {git_url} -> {target_dir}")

        # Ensure target directory is empty
        if os.path.exists(target_dir):
            logging.info(f"Removing existing directory: {target_dir}")
            subprocess.run(['rm', '-rf', target_dir], check=True)

        # Create parent directory
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)

        # Check directory permissions
        parent_dir = os.path.dirname(target_dir)
        logging.info(f"Checking permissions for {parent_dir}")
        if not os.access(parent_dir, os.W_OK):
            logging.error(f"No write permission to {parent_dir}")
            raise Exception(f"No write permission to {parent_dir}")

        # Clone with full logging
        logging.info(f"Executing git clone {git_url}")
        process = subprocess.Popen(
            ['git', 'clone', git_url, target_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Read output in real time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logging.info(f"Git output: {output.strip()}")

        # Get stderr after completion
        _, stderr = process.communicate()
        if stderr:
            logging.error(f"Git stderr: {stderr}")

        # Check exit code
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, 'git clone')

        # Check if directory was created and contains files
        if not os.path.exists(target_dir) or not os.listdir(target_dir):
            raise Exception("Git clone completed but directory is empty")

        # Display repository contents
        logging.info(f"Repository contents: {os.listdir(target_dir)}")

        return True

    except subprocess.CalledProcessError as e:
        logging.error(
            f"Git clone failed: {str(e)}\nCommand output: {e.output if hasattr(e, 'output') else 'No output'}")
        return False
    except Exception as e:
        logging.error(f"Error during git clone: {str(e)}\n{traceback.format_exc()}")
        return False
