# Running with Caddy Server

This guide explains how to serve the React application using Caddy server.

## Prerequisites

1. Install Caddy server:
   ```bash
   # For Ubuntu/Debian
   sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
   sudo apt update
   sudo apt install caddy

   # For RHEL/CentOS/Fedora
   dnf install 'dnf-command(copr)'
   dnf copr enable @caddy/caddy
   dnf install caddy
   ```

## Configuration

1. Create a Caddyfile in your project root:
   ```
   example.com {
       root * /path/to/your/build
       try_files {path} /index.html
       file_server
   }
   ```

   Replace `example.com` with your domain name and `/path/to/your/build` with the actual path to your React build directory.

2. For development with localhost:
   ```
   localhost:3000 {
       root * /path/to/your/build
       try_files {path} /index.html
       file_server
   }
   ```

## Building the React App

1. Build your React application:
   ```bash
   npm run build
   ```

   This will create a `build` directory with optimized production files.

## Running Caddy

1. Start Caddy:
   ```bash
   sudo systemctl start caddy
   ```

2. Enable Caddy to start on boot:
   ```bash
   sudo systemctl enable caddy
   ```

3. Check Caddy status:
   ```bash
   sudo systemctl status caddy
   ```

## Managing Caddy

- Reload Caddy configuration:
  ```bash
  sudo systemctl reload caddy
  ```

- Stop Caddy:
  ```bash
  sudo systemctl stop caddy
  ```

- Restart Caddy:
  ```bash
  sudo systemctl restart caddy
  ```

## Troubleshooting

1. Check Caddy logs:
   ```bash
   sudo journalctl -u caddy
   ```

2. Verify Caddyfile syntax:
   ```bash
   caddy validate
   ```

3. Test configuration:
   ```bash
   caddy run
   ```

## HTTPS

Caddy automatically handles HTTPS certificates using Let's Encrypt. Just make sure:

1. Your domain points to your server
2. Ports 80 and 443 are open
3. Your Caddyfile uses a domain name (not just an IP)

## Additional Configuration

### Reverse Proxy
If you're running the React app on a development server:
```
example.com {
    reverse_proxy localhost:3000
}
```

### Custom Error Pages
```
example.com {
    root * /path/to/your/build
    try_files {path} /index.html
    file_server
    handle_errors {
        rewrite * /error.html
        file_server
    }
}
```

### Compression
Caddy enables Gzip compression by default. For custom compression settings:
```
example.com {
    encode gzip zstd
    root * /path/to/your/build
    try_files {path} /index.html
    file_server
}
```

## Security Headers

Add security headers to your Caddyfile:
```
example.com {
    root * /path/to/your/build
    try_files {path} /index.html
    file_server
    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        Content-Security-Policy "default-src 'self'"
    }
}
