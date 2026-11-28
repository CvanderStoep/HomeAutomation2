#!/bin/bash
# Maakt een volledige backup van InfluxDB op de Raspberry Pi en zet die in de backupmap
# (OneDrive: "13. Backup scripts") als influx-backup-JJJJ-MM-DD. De Pi blijft gewoon doordraaien (InfluxDB hoeft niet te stoppen).
# Start door te dubbelklikken in Finder (.command opent in Terminal) of via ./backup-influx-from-pi.command
#
# Werkwijze:
#   1. op de Pi: "influx backup" naar /tmp/backup in de container
#   2. die map als tar-stroom via ssh direct naar deze Mac (geen extra kopie op de SD-kaart of in Downloads)
#   3. op de Mac controleren: elk bestand uit het manifest aanwezig, met de juiste grootte en een geldige gzip
#   4. pas als alles klopt krijgt de map zijn definitieve naam; anders blijft er niets halfs achter
#
# Terugzetten op de Mac: restore-influx-on-mac.command

set -u
set -o pipefail

# Pi: eerst de naam (mDNS), anders het vaste IP-adres.
pi_user="pi"
pi_hosts="raspberrypi400.local 192.168.68.131"
ssh_opts="-o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=4"

# Map waarin dit script staat (het project) en de map waar de backups komen.
# De backups (±1 GB per stuk) staan bewust buiten git, in OneDrive.
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
backup_dir="$HOME/Library/CloudStorage/OneDrive-Persoonlijk/Documenten/13. Backup scripts"

partial=""
target=""

# Houd het Terminal-venster open zodat je het resultaat kunt lezen.
finish() {
    printf '\n%s Druk op Enter om dit venster te sluiten.' "$1"
    read -r _
    exit "$2"
}

# Opruimen bij afbreken of fouten: halve download op de Mac en de tijdelijke map in de container.
cleanup() {
    if [ -n "$partial" ] && [ -d "$partial" ]; then
        rm -rf "$partial"
    fi
    if [ -n "$target" ]; then
        ssh $ssh_opts "$target" "sudo docker exec influxdb rm -rf /tmp/backup" 2>/dev/null
    fi
}
trap cleanup EXIT
trap 'printf "\nAfgebroken.\n"; exit 130' INT TERM

pi() {
    ssh $ssh_opts "$target" "$@"
}

printf '== InfluxDB-backup van de Pi naar deze Mac ==\n'

# Zoek de Pi.
for host in $pi_hosts; do
    if ssh $ssh_opts -o BatchMode=yes "$pi_user@$host" true 2>/dev/null; then
        target="$pi_user@$host"
        break
    fi
done
[ -d "$backup_dir" ] || finish "FOUT: backupmap $backup_dir niet gevonden." 1
backup_dir=$(CDPATH= cd -- "$backup_dir" && pwd)

[ -n "$target" ] || finish "FOUT: de Pi is niet bereikbaar via ssh ($pi_hosts)." 1
printf 'Pi gevonden: %s\n' "$target"

# Doelmap: influx-backup-JJJJ-MM-DD, of met tijd erachter als die van vandaag al bestaat.
dest="$backup_dir/influx-backup-$(date +%Y-%m-%d)"
[ -e "$dest" ] && dest="$dest-$(date +%H%M)"
[ -e "$dest" ] && finish "FOUT: $dest bestaat al." 1
partial="$dest.partial"
rm -rf "$partial"
mkdir -p "$partial" || finish "FOUT: kan $partial niet aanmaken." 1

# Stap 1: backup maken in de container (de uitvoer per shard is lang; alleen bij een fout tonen).
printf 'Stap 1: backup maken op de Pi (dit duurt een paar minuten)...\n'
log=$(mktemp)
if ! pi "sudo docker exec influxdb sh -c 'rm -rf /tmp/backup && influx backup /tmp/backup -t \"\$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN\"'" >"$log" 2>&1; then
    tail -n 20 "$log"
    rm -f "$log"
    finish "FOUT: influx backup op de Pi is mislukt." 1
fi
rm -f "$log"

# Stap 2: als tar-stroom direct naar de Mac.
printf 'Stap 2: backup kopieren naar %s...\n' "$dest"
if ! pi "sudo docker exec influxdb tar -C /tmp/backup -cf - ." | tar -C "$partial" -xf -; then
    finish "FOUT: kopieren van de backup is mislukt." 1
fi

# Tijdelijke map in de container meteen opruimen (de trap doet het anders alsnog).
pi "sudo docker exec influxdb rm -rf /tmp/backup"

# Stap 3: controleren tegen het manifest.
printf 'Stap 3: backup controleren...\n'
manifests=$(find "$partial" -maxdepth 1 -name '*.manifest')
[ "$(printf '%s\n' "$manifests" | grep -c .)" -eq 1 ] || finish "FOUT: verwacht precies 1 manifest in de backup." 1

# Het manifest is JSON met per bestand een regel "fileName" gevolgd door een regel "size".
errors=0
count=0
while read -r name size; do
    count=$((count + 1))
    file="$partial/$name"
    if [ ! -f "$file" ]; then
        printf '  ontbreekt: %s\n' "$name"
        errors=$((errors + 1))
    elif [ "$(stat -f %z "$file")" != "$size" ]; then
        printf '  verkeerde grootte: %s\n' "$name"
        errors=$((errors + 1))
    elif ! gzip -t "$file" 2>/dev/null; then
        printf '  beschadigd (gzip): %s\n' "$name"
        errors=$((errors + 1))
    fi
done < <(awk -F'"' '/"fileName"/ {name = $4} /"size"/ && name != "" {gsub(/[^0-9]/, "", $3); print name, $3; name = ""}' "$manifests")

[ "$count" -gt 0 ] || finish "FOUT: geen bestanden gevonden in het manifest." 1
[ "$errors" -eq 0 ] || finish "FOUT: $errors van de $count bestanden kloppen niet; backup niet bewaard." 1

# Stap 4: definitieve naam.
mv "$partial" "$dest" || finish "FOUT: kan $partial niet hernoemen." 1
partial=""

printf '\nGelukt: %s bestanden gecontroleerd, %s in %s\n' "$count" "$(du -sh "$dest" | cut -f1)" "$dest"
printf '\nAlle InfluxDB-backups in deze map:\n'
du -sh "$backup_dir"/influx-backup-* 2>/dev/null | sed "s|$backup_dir/|  |"
printf '\nTerugzetten op de Mac: restore-influx-on-mac.command\n'
finish "Klaar." 0
