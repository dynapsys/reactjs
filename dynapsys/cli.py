"""Command-line interface for DynaPsys"""
import click
import logging
from typing import Optional
from .deployment import run_server
from .config import config
from .dns import update_cloudflare_dns
from .git import clone_git_repo, is_valid_git_url

@click.group()
@click.option('--debug/--no-debug', default=False, help='Enable debug logging')
def cli(debug: bool) -> None:
    """DynaPsys - Dynamic Python System Deployment Tools"""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler()
        ]
    )

@cli.command()
@click.option('--host', default=config.server_host, help='Server host')
@click.option('--port', default=config.server_port, help='Server port')
@click.option('--ssl/--no-ssl', default=config.enable_ssl, help='Enable SSL')
@click.option('--cert', default=config.ssl_cert_file, help='SSL certificate file')
@click.option('--key', default=config.ssl_key_file, help='SSL key file')
def serve(host: str, port: int, ssl: bool, cert: str, key: str) -> None:
    """Start the deployment server"""
    click.echo(f"Starting server on {host or '0.0.0.0'}:{port}")
    if ssl and cert and key:
        click.echo("SSL enabled")
    run_server(port=port)

@cli.command()
@click.argument('domain')
@click.argument('token')
def dns(domain: str, token: str) -> None:
    """Update DNS records in Cloudflare"""
    click.echo(f"Updating DNS for {domain}")
    if update_cloudflare_dns(domain, token):
        click.echo("DNS updated successfully")
    else:
        click.echo("Failed to update DNS", err=True)
        exit(1)

@cli.command()
@click.argument('url')
@click.argument('target_dir', type=click.Path())
def clone(url: str, target_dir: str) -> None:
    """Clone a git repository"""
    if not is_valid_git_url(url):
        click.echo(f"Invalid git URL: {url}", err=True)
        exit(1)

    click.echo(f"Cloning {url} to {target_dir}")
    if clone_git_repo(url, target_dir):
        click.echo("Repository cloned successfully")
    else:
        click.echo("Failed to clone repository", err=True)
        exit(1)

@cli.command()
def config_info() -> None:
    """Display current configuration"""
    click.echo("Current Configuration:")
    click.echo(f"Log Level: {config.log_level}")
    click.echo(f"Log File: {config.log_file}")
    click.echo(f"Sites Directory: {config.sites_dir}")
    click.echo(f"Server Host: {config.server_host or '0.0.0.0'}")
    click.echo(f"Server Port: {config.server_port}")
    click.echo(f"SSL Enabled: {config.enable_ssl}")
    if config.enable_ssl:
        click.echo(f"SSL Certificate: {config.ssl_cert_file}")
        click.echo(f"SSL Key: {config.ssl_key_file}")
    click.echo(f"PM2 Save on Exit: {config.pm2_save_on_exit}")

@cli.command()
@click.argument('key', required=False)
def get_config(key: Optional[str]) -> None:
    """Get configuration value(s)"""
    if key:
        value = config.get(key)
        if value is not None:
            click.echo(f"{key}={value}")
        else:
            click.echo(f"Configuration key '{key}' not found", err=True)
            exit(1)
    else:
        for k in sorted(config.DEFAULTS.keys()):
            click.echo(f"{k}={config.get(k)}")

def main() -> None:
    """Main entry point for the CLI"""
    cli(auto_envvar_prefix='DYNAPSYS')

if __name__ == '__main__':
    main()
