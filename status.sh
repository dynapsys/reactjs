#!/bin/bash

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funkcja wyświetlająca pomoc
show_help() {
    echo -e "${BLUE}Użycie:${NC}"
    echo -e "  $0 [opcje]"
    echo -e "\n${BLUE}Opcje:${NC}"
    echo -e "  -a, --all          Pokaż wszystkie logi"
    echo -e "  -d, --deployment   Pokaż logi deploymentu"
    echo -e "  -s, --service      Pokaż logi usługi systemd"
    echo -e "  -p, --pm2          Pokaż logi PM2"
    echo -e "  -c, --caddy        Pokaż logi Caddy"
    echo -e "  -n, --lines N      Liczba linii (domyślnie 50)"
    echo -e "  -f, --follow       Śledź logi w czasie rzeczywistym"
    echo -e "  -h, --help         Pokaż tę pomoc"
    echo -e "\n${BLUE}Przykłady:${NC}"
    echo -e "  $0 -a              # Pokaż wszystkie logi"
    echo -e "  $0 -d -f           # Śledź logi deploymentu"
    echo -e "  $0 -p -n 100       # Pokaż 100 ostatnich linii logów PM2"
}

# Domyślne wartości
LINES=50
FOLLOW=false
SHOW_ALL=false
SHOW_DEPLOYMENT=false
SHOW_SERVICE=false
SHOW_PM2=false
SHOW_CADDY=false

# Parsowanie argumentów
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--all)
            SHOW_ALL=true
            shift
            ;;
        -d|--deployment)
            SHOW_DEPLOYMENT=true
            shift
            ;;
        -s|--service)
            SHOW_SERVICE=true
            shift
            ;;
        -p|--pm2)
            SHOW_PM2=true
            shift
            ;;
        -c|--caddy)
            SHOW_CADDY=true
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        *)
            echo "Nieznana opcja: $1"
            show_help
            exit 1
            ;;
    esac
done

# Jeśli nie wybrano żadnej opcji, pokaż wszystko
if [[ "$SHOW_ALL" == "false" && "$SHOW_DEPLOYMENT" == "false" && \
      "$SHOW_SERVICE" == "false" && "$SHOW_PM2" == "false" && \
      "$SHOW_CADDY" == "false" ]]; then
    SHOW_ALL=true
fi

# Funkcja wyświetlająca logi z timestampem
show_logs() {
    local file=$1
    local type=$2
    if [[ -f "$file" ]]; then
        echo -e "\n${YELLOW}=== $type Logs ===${NC}"
        if [[ "$FOLLOW" == "true" ]]; then
            tail -f -n "$LINES" "$file" | while read -r line; do
                echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $line"
            done
        else
            tail -n "$LINES" "$file" | while read -r line; do
                echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $line"
            done
        fi
    else
        echo -e "${RED}Plik logów $file nie istnieje${NC}"
    fi
}

# Funkcja sprawdzająca status usług
check_services() {
    echo -e "\n${YELLOW}=== Status Usług ===${NC}"

    # Sprawdź status reactjs
    echo -e "\n${BLUE}ReactJS Service:${NC}"
    systemctl status reactjs --no-pager || true

    # Sprawdź status Caddy
    echo -e "\n${BLUE}Caddy Service:${NC}"
    systemctl status caddy --no-pager || true

    # Sprawdź procesy PM2
    echo -e "\n${BLUE}PM2 Processes:${NC}"
    pm2 list || true
}

# Wyświetlanie logów
if [[ "$SHOW_ALL" == "true" ]] || [[ "$SHOW_DEPLOYMENT" == "true" ]]; then
    show_logs "/opt/reactjs/logs/deployment.log" "Deployment"
fi

if [[ "$SHOW_ALL" == "true" ]] || [[ "$SHOW_SERVICE" == "true" ]]; then
    echo -e "\n${YELLOW}=== Service Logs ===${NC}"
    if [[ "$FOLLOW" == "true" ]]; then
        journalctl -u reactjs -f -n "$LINES" --no-pager
    else
        journalctl -u reactjs -n "$LINES" --no-pager
    fi
fi

if [[ "$SHOW_ALL" == "true" ]] || [[ "$SHOW_PM2" == "true" ]]; then
    echo -e "\n${YELLOW}=== PM2 Logs ===${NC}"
    pm2 logs --lines "$LINES" --nostream
    if [[ "$FOLLOW" == "true" ]]; then
        pm2 logs
    fi
fi

if [[ "$SHOW_ALL" == "true" ]] || [[ "$SHOW_CADDY" == "true" ]]; then
    show_logs "/var/log/caddy/access.log" "Caddy Access"
fi

# Sprawdź status usług
check_services

# Jeśli włączono śledzenie, wyświetl informację o zatrzymaniu
if [[ "$FOLLOW" == "true" ]]; then
    echo -e "\n${YELLOW}Naciśnij Ctrl+C aby zatrzymać śledzenie logów${NC}"
    # Trzymaj skrypt uruchomiony
    tail -f /dev/null
fi