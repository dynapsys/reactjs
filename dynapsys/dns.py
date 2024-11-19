#!/usr/bin/python3
import json
import subprocess
import logging
import sys
import traceback

def update_cloudflare_dns(domain, cf_token):
    """Update DNS in Cloudflare"""
    try:
        logging.info(f"Updating DNS for domain: {domain}")

        # Extract main domain
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            main_domain = '.'.join(domain_parts[-2:])
            logging.info(f"Subdomain detected. Main domain: {main_domain}")
        else:
            main_domain = domain

        # Get server's public IP
        ip_process = subprocess.Popen(
            ['curl', '-s', 'http://ipv4.icanhazip.com'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        ip_stdout, ip_stderr = ip_process.communicate()

        if ip_process.returncode != 0:
            logging.error(f"Error getting IP: {ip_stderr.decode()}")
            return False

        ip = ip_stdout.decode().strip()
        logging.info(f"Got IP: {ip}")

        # Get Zone ID
        logging.info(f"Getting Zone ID from Cloudflare for domain: {main_domain}")
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
                logging.error(f"Cloudflare API error: {errors}")
                return False

            if not zone_response.get('result', []):
                logging.error(f"Domain {main_domain} not found in Cloudflare")
                return False

            zone_id = zone_response['result'][0]['id']
            logging.info(f"Got Zone ID: {zone_id}")

            # Check existing DNS records
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
                # Update existing record
                record_id = record_response['result'][0]['id']
                logging.info(f"Found existing DNS record {record_id}, updating...")

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
                    logging.error(f"Error updating DNS record: {update_response.get('errors', [])}")
                    return False
            else:
                # Create new record
                logging.info("Creating new DNS record...")
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
                    logging.error(f"Error creating DNS record: {create_response.get('errors', [])}")
                    return False

            logging.info("DNS updated successfully")
            return True

        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON response: {str(e)}\nResponse: {zone_stdout.decode()}")
            return False
        except (IndexError, KeyError) as e:
            logging.error(f"Error in response structure: {str(e)}\nResponse: {zone_stdout.decode()}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            return False

    except Exception as e:
        logging.error(f"Cloudflare DNS update error: {str(e)}\n{traceback.format_exc()}")
        return False

    finally:
        logging.info("DNS update process completed")
