#!/bin/bash
# Zet een InfluxDB-backup van de Pi volledig terug in Docker op deze Mac en start InfluxDB + Grafana.
# Alleen influxdb en grafana draaien op de Mac; realtimemonitoring niet (de Pi blijft productie).
# Start door te dubbelklikken in Finder, of via de terminal:
#   ./restore-influx-on-mac.command                      -> nieuwste influx-backup-* in de backupmap
#   ./restore-influx-on-mac.command influx-backup-2026-11-27  -> een specifieke backup
#
# Werkwijze:
#   1. influxdb en grafana starten met docker-compose.yml en .env uit dit project
#   2. veiligheidskopie van wat nu in InfluxDB op de Mac staat (in ~/InfluxDB-veiligheidskopie)
#   3. "influx restore --full": alles op de Mac wordt vervangen door de backup (ook tokens en gebruikers)
#   4. controle: per measurement het aantal punten en het laatste tijdstip, uitgerekend op de Mac
#      (bewust niet op de Pi: een query over alle jaren overbelast de Pi)
#
# Het admin-token na de restore is dat van de Pi. Mac en Pi gebruiken dezelfde .env, dus dat klopt vanzelf.

set -u
set -o pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_dir="$script_dir"
# De backups (±1 GB per stuk) staan bewust buiten git, in OneDrive.
backup_dir="$HOME/Library/CloudStorage/OneDrive-Persoonlijk/Documenten/13. Backup scripts"
safety_root="$HOME/InfluxDB-veiligheidskopie"

restore_started=""

finish() {
    printf '\n%s Druk op Enter om dit venster te sluiten.' "$1"
    read -r _
    exit "$2"
}

# Opruimen in de container, ook bij fouten.
cleanup() {
    if [ -n "$restore_started" ]; then
        docker exec influxdb rm -rf /tmp/restore /tmp/mac-backup 2>/dev/null
    fi
}
trap cleanup EXIT
trap 'printf "\nAfgebroken.\n"; exit 130' INT TERM

# Docker in de Mac-shell: Docker Desktop zet docker niet altijd in het PATH van een .command.
export PATH="$PATH:/usr/local/bin:/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin"

compose() {
    docker compose --project-directory "$project_dir" -f "$project_dir/docker-compose.yml" "$@"
}

# Flux-query in de container; uitvoer als CSV zonder annotaties.
flux() {
    docker exec influxdb sh -c 'influx query --raw -t "$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN" "$1"' sh "$1"
}

# Zet Flux-CSV om naar "kolom1  kolom2" op basis van de kolomnamen in de kop.
csv_columns() {
    awk -F',' -v a="$1" -v b="$2" '
        /^#/ || NF < 2 { next }
        /,result,table,/ { for (i = 1; i <= NF; i++) { gsub(/\r/, "", $i); col[$i] = i }; next }
        { gsub(/\r/, ""); printf "  %-20s %s\n", $col[a], $col[b] }'
}

printf '== InfluxDB-backup terugzetten op deze Mac ==\n'

# Welke backup?
if [ $# -ge 1 ]; then
    case "$1" in
        /*) backup="$1" ;;
        *)  backup="$backup_dir/$1" ;;
    esac
else
    backup=$(find "$backup_dir" -maxdepth 1 -type d -name 'influx-backup-*' ! -name '*.partial' | sort | tail -n 1)
fi
[ -n "$backup" ] && [ -d "$backup" ] || finish "FOUT: geen backupmap gevonden." 1
backup=$(CDPATH= cd -- "$backup" && pwd)
manifest=$(find "$backup" -maxdepth 1 -name '*.manifest' | head -n 1)
[ -n "$manifest" ] || finish "FOUT: geen manifest in $backup; is dit een influx backup?" 1

# Tijdstip van de backup uit de bestandsnaam (bijv. 20261127T143000Z.manifest).
stamp=$(basename "$manifest" .manifest)
backup_time=$(printf '%s' "$stamp" | sed -E 's/^([0-9]{4})([0-9]{2})([0-9]{2})T([0-9]{2})([0-9]{2})([0-9]{2})Z$/\1-\2-\3T\4:\5:\6Z/')

[ -f "$project_dir/docker-compose.yml" ] || finish "FOUT: $project_dir/docker-compose.yml niet gevonden." 1
[ -f "$project_dir/.env" ] || finish "FOUT: $project_dir/.env niet gevonden." 1
docker info >/dev/null 2>&1 || finish "FOUT: Docker draait niet. Start Docker Desktop en probeer opnieuw." 1

printf 'Backup:  %s\n' "$backup"
printf 'Gestart: %s (UTC)\n\n' "$backup_time"
printf 'LET OP: alle InfluxDB-data op deze Mac wordt vervangen door deze backup.\n'
printf 'Er wordt eerst een veiligheidskopie gemaakt in %s.\n' "$safety_root"
printf 'Doorgaan? [j/N] '
read -r answer
case "$answer" in
    j|J|ja|Ja) ;;
    *) finish "Afgebroken, er is niets gewijzigd." 1 ;;
esac

# Stap 1: influxdb en grafana starten (het netwerk ha_network is "external" en moet bestaan).
printf '\nStap 1: InfluxDB en Grafana starten...\n'
docker network inspect ha_network >/dev/null 2>&1 || docker network create ha_network >/dev/null \
    || finish "FOUT: kan het Docker-netwerk ha_network niet aanmaken." 1
compose up -d --wait influxdb grafana || finish "FOUT: starten van influxdb/grafana is mislukt." 1

# realtimemonitoring hoort niet op de Mac te draaien; staat hij er toch, dan stoppen.
if [ "$(docker inspect -f '{{.State.Running}}' realtimemonitoring 2>/dev/null)" = "true" ]; then
    printf '  realtimemonitoring draait op de Mac; wordt gestopt (de Pi verzamelt de data).\n'
    docker stop realtimemonitoring >/dev/null
fi

restore_started="yes"

# Stap 2: veiligheidskopie van de huidige Mac-data.
safety="$safety_root/mac-$(date +%Y-%m-%d_%H%M%S)"
printf 'Stap 2: veiligheidskopie maken in %s...\n' "$safety"
mkdir -p "$safety_root" || finish "FOUT: kan $safety_root niet aanmaken." 1
log=$(mktemp)
if ! docker exec influxdb sh -c 'rm -rf /tmp/mac-backup && influx backup /tmp/mac-backup -t "$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN"' >"$log" 2>&1; then
    tail -n 20 "$log"
    rm -f "$log"
    finish "FOUT: veiligheidskopie mislukt; er is niets teruggezet." 1
fi
rm -f "$log"
docker cp influxdb:/tmp/mac-backup "$safety" >/dev/null || finish "FOUT: veiligheidskopie kopieren mislukt; er is niets teruggezet." 1

# Stap 3: volledige restore.
printf 'Stap 3: backup terugzetten (dit duurt een paar minuten)...\n'
docker exec influxdb rm -rf /tmp/restore
docker cp "$backup" influxdb:/tmp/restore >/dev/null || finish "FOUT: backup naar de container kopieren mislukt." 1
log=$(mktemp)
if ! docker exec influxdb sh -c 'influx restore /tmp/restore --full -t "$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN"' >"$log" 2>&1; then
    tail -n 20 "$log"
    rm -f "$log"
    finish "FOUT: influx restore mislukt. Veiligheidskopie: $safety" 1
fi
rm -f "$log"
docker exec influxdb rm -rf /tmp/restore /tmp/mac-backup

# Stap 4: controle op de Mac.
printf 'Stap 4: controleren...\n'
bucket=$(docker exec influxdb sh -c 'printf %s "$DOCKER_INFLUXDB_INIT_BUCKET"')
docker exec influxdb sh -c 'influx bucket list -t "$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN"' \
    || finish "FOUT: bucket list mislukt; klopt het token in .env met dat van de Pi?" 1

printf '\nAantal punten per measurement:\n'
flux "from(bucket: \"$bucket\") |> range(start: 0) |> count() |> group(columns: [\"_measurement\"]) |> sum() |> keep(columns: [\"_measurement\", \"_value\"])" \
    | csv_columns _measurement _value

printf '\nLaatste punt per measurement (backup gestart %s; kan iets later zijn):\n' "$backup_time"
flux "from(bucket: \"$bucket\") |> range(start: 0) |> last() |> keep(columns: [\"_measurement\", \"_time\"]) |> group(columns: [\"_measurement\"]) |> max(column: \"_time\")" \
    | csv_columns _measurement _time

printf '\nGrafana op deze Mac: http://localhost:3000 (dashboard en datasource komen uit git).\n'
printf 'Oude veiligheidskopieen staan in %s; verwijder die zelf als je ze niet meer nodig hebt.\n' "$safety_root"
finish "Klaar." 0
