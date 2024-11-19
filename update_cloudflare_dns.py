#!/usr/bin/python3
import json
import subprocess
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

def update_cloudflare_dns(self, domain, cf_token):
    """Aktualizuje DNS w Cloudflare"""
    try:
        logging.info(f"Aktualizacja DNS dla domeny: {domain}")

        # Wyciągnij główną domenę
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            main_domain = '.'.join(domain_parts[-2:])
            logging.info(f"Subdomena wykryta. Główna domena: {main_domain}")
        else:
            main_domain = domain

        # Pobierz publiczny IP serwera
        ip_process = subprocess.Popen(
            ['curl', '-s', 'http://ipv4.icanhazip.com'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        ip_stdout, ip_stderr = ip_process.communicate()

        if ip_process.returncode != 0:
            logging.error(f"Błąd pobierania IP: {ip_stderr.decode()}")
            return False

        ip = ip_stdout.decode().strip()
        logging.info(f"Pobrano IP: {ip}")

        # Pobierz Zone ID
        logging.info(f"Pobieranie Zone ID z Cloudflare dla domeny: {main_domain}")
        zone_cmd = [
            'curl', '-s', '-X', 'GET',
            f'https://api.cloudflare.com/client/v4/zones?name={main_domain}',
            '-H', f'Authorization: Bearer {cf_token}',
            '-H', 'Content-Type: application/json'
        ]
        zone_process = subprocess.Popen(zone_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        zone_stdout, zone_stderr = zone_process.communicate()

        try:
            zone_response = json.loads(zone_stdout.decode())

            if not zone_response.get('success', False):
                errors = zone_response.get('errors', [])
                logging.error(f"Błąd API Cloudflare: {errors}")
                return False

            if not zone_response.get('result', []):
                logging.error(f"Nie znaleziono domeny {main_domain} w Cloudflare")
                return False

            zone_id = zone_response['result'][0]['id']
            logging.info(f"Pobrano Zone ID: {zone_id}")

            # Sprawdź istniejące rekordy DNS
            existing_record_cmd = [
                'curl', '-s', '-X', 'GET',
                f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name={domain}',
                '-H', f'Authorization: Bearer {cf_token}',
                '-H', 'Content-Type: application/json'
            ]

            record_process = subprocess.Popen(existing_record_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            record_stdout, record_stderr = record_process.communicate()
            record_response = json.loads(record_stdout.decode())

            dns_data = {
                'type': 'A',
                'name': domain,
                'content': ip,
                'ttl': 1,
                'proxied': True
            }

            if record_response.get('result', []):
                # Aktualizuj istniejący rekord
                record_id = record_response['result'][0]['id']
                logging.info(f"Znaleziono istniejący rekord DNS {record_id}, aktualizacja...")

                update_cmd = [
                    'curl', '-s', '-X', 'PUT',
                    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}',
                    '-H', f'Authorization: Bearer {cf_token}',
                    '-H', 'Content-Type: application/json',
                    '-d', json.dumps(dns_data)
                ]

                update_process = subprocess.Popen(update_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                update_stdout, update_stderr = update_process.communicate()
                update_response = json.loads(update_stdout.decode())

                if not update_response.get('success', False):
                    logging.error(f"Błąd aktualizacji rekordu DNS: {update_response.get('errors', [])}")
                    return False
            else:
                # Utwórz nowy rekord
                logging.info("Tworzenie nowego rekordu DNS...")
                create_cmd = [
                    'curl', '-s', '-X', 'POST',
                    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
                    '-H', f'Authorization: Bearer {cf_token}',
                    '-H', 'Content-Type: application/json',
                    '-d', json.dumps(dns_data)
                ]

                create_process = subprocess.Popen(create_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                create_stdout, create_stderr = create_process.communicate()
                create_response = json.loads(create_stdout.decode())

                if not create_response.get('success', False):
                    logging.error(f"Błąd tworzenia rekordu DNS: {create_response.get('errors', [])}")
                    return False

            logging.info("DNS zaktualizowany pomyślnie")
            return True

        except json.JSONDecodeError as e:
            logging.error(f"Błąd parsowania odpowiedzi JSON: {str(e)}\nResponse: {zone_stdout.decode()}")
            return False
        except (IndexError, KeyError) as e:
            logging.error(f"Błąd w strukturze odpowiedzi: {str(e)}\nResponse: {zone_stdout.decode()}")
            return False
        except Exception as e:
            logging.error(f"Nieoczekiwany błąd: {str(e)}\n{traceback.format_exc()}")
            return False

    except Exception as e:
        logging.error(f"Cloudflare DNS update error: {str(e)}\n{traceback.format_exc()}")
        return False

    finally:
        logging.info("Zakończono proces aktualizacji DNS")
