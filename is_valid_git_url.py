#!/usr/bin/python3
import logging
import sys

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
