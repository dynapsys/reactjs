#!/usr/bin/python3
import subprocess
import os
import logging
import sys
import traceback

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,  # Zmieniono na DEBUG dla bardziej szczegółowych logów
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('/opt/reactjs/logs/deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


def is_valid_git_url(self, url):
    """Sprawdza czy URL jest poprawnym adresem Git"""
    git_patterns = [
        r'^https?://github\.com/[\w-]+/[\w.-]+(?:\.git)?$',
        r'^git@github\.com:[\w-]+/[\w.-]+(?:\.git)?$',
        r'^https?://gitlab\.com/[\w-]+/[\w.-]+(?:\.git)?$',
        r'^https?://bitbucket\.org/[\w-]+/[\w.-]+(?:\.git)?$'
    ]
    is_valid = any(re.match(pattern, url) for pattern in git_patterns)
    logging.info(f"Sprawdzanie URL git: {url} - {'poprawny' if is_valid else 'niepoprawny'}")
    return is_valid

def clone_git_repo(self, git_url, target_dir):
    """Klonuje repozytorium git do wskazanego katalogu"""
    try:
        # Sprawdź instalację git
        if not self.check_git_installation():
            raise Exception("Git is not installed")

        logging.info(f"Starting git clone: {git_url} -> {target_dir}")

        # Upewnij się, że katalog docelowy jest pusty
        if os.path.exists(target_dir):
            logging.info(f"Removing existing directory: {target_dir}")
            subprocess.run(['rm', '-rf', target_dir], check=True)

        # Tworzenie katalogu nadrzędnego
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)

        # Sprawdź uprawnienia do katalogu
        parent_dir = os.path.dirname(target_dir)
        logging.info(f"Checking permissions for {parent_dir}")
        if not os.access(parent_dir, os.W_OK):
            logging.error(f"No write permission to {parent_dir}")
            raise Exception(f"No write permission to {parent_dir}")

        # Klonowanie z pełnym logowaniem
        logging.info(f"Executing git clone {git_url}")
        process = subprocess.Popen(
            ['git', 'clone', git_url, target_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Czytanie output w czasie rzeczywistym
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logging.info(f"Git output: {output.strip()}")

        # Pobierz stderr po zakończeniu
        _, stderr = process.communicate()
        if stderr:
            logging.error(f"Git stderr: {stderr}")

        # Sprawdź kod wyjścia
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, 'git clone')

        # Sprawdź czy katalog został utworzony i zawiera pliki
        if not os.path.exists(target_dir) or not os.listdir(target_dir):
            raise Exception("Git clone completed but directory is empty")

        # Wyświetl zawartość sklonowanego repozytorium
        logging.info(f"Repository contents: {os.listdir(target_dir)}")

        return True

    except subprocess.CalledProcessError as e:
        logging.error(
            f"Git clone failed: {str(e)}\nCommand output: {e.output if hasattr(e, 'output') else 'No output'}")
        return False
    except Exception as e:
        logging.error(f"Error during git clone: {str(e)}\n{traceback.format_exc()}")
        return False