#!/bin/sh
# Kopieert de privé-bestanden (die niet in git staan) van deze Mac naar de Raspberry Pi.
# Start door te dubbelklikken in Finder (.command opent in Terminal) of via ./deploy-private-files.command
#
# Na het kopiëren op de Pi, in de projectmap:
#   git pull && sudo docker compose up --build -d

# Stop bij gebruik van een niet-bestaande variabele (vangt typfouten af).
set -u

# SSH-adres van de Pi en de projectmap daarop (daar staat ook de git-clone).
target="pi@raspberrypi400.local"
remote_dir="/home/pi/HomeAutomation2"

# Map waarin dit script staat, zodat het werkt ongeacht vanuit welke map je het start.
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

deploy() {
    # Bestanden die naar de Pi moeten:
    #   .env               - alle secrets (InfluxDB, Grafana, OpenWeatherMap, Hue IP);
    #                        docker-compose geeft ze als omgevingsvariabelen door
    #   .python_hue        - koppelgegevens van de Hue bridge; wordt in de container gemount
    # docker-compose.yml staat in git en komt via git pull op de Pi.
    files="
.env
.python_hue
"

    # Controleer eerst of alle bestanden bestaan en verzamel hun volledige paden
    # in de argumentenlijst ($@), zodat scp ze in één keer kan kopiëren.
    set --
    for file in $files; do
        path="$script_dir/$file"
        if [ ! -e "$path" ]; then
            printf 'Bestand niet gevonden: %s\n' "$path" >&2
            return 1
        fi
        set -- "$@" "$path"
    done

    # Maak de projectmap aan als die nog niet bestaat; alleen gebruiker pi heeft toegang (700).
    ssh "$target" "mkdir -p '$remote_dir' && chmod 700 '$remote_dir'" || return $?

    # Kopieer alle bestanden in één keer naar de projectmap op de Pi (bestaande worden overschreven).
    scp -r "$@" "$target:$remote_dir/" || return $?

    # Maak de bestanden met secrets alleen leesbaar/schrijfbaar voor gebruiker pi (600).
    ssh "$target" "chmod 600 '$remote_dir/.env' '$remote_dir/.python_hue'" || return $?

    printf 'Bestanden gekopieerd naar %s:%s\n' "$target" "$remote_dir"
}

# Waarschuwing: de bestanden op de Pi (productie) worden overschreven door die van deze Mac.
# Instellingen die alleen op de Pi moeten gelden, horen in een docker-compose.override.yml
# op de Pi zelf; die wordt door dit script en door git niet aangeraakt.
printf 'LET OP: .env en .python_hue op %s worden overschreven\n' "$target"
printf 'door de versies van deze Mac (%s).\n' "$script_dir"
printf 'Doorgaan? [j/N] '
read -r answer
case "$answer" in
    j|J|ja|Ja) ;;
    *)
        printf 'Afgebroken, er is niets gekopieerd. Druk op Enter om dit venster te sluiten.'
        read -r _
        exit 1
        ;;
esac

# Voer de deploy uit en onthoud de exitcode (0 = gelukt).
if deploy; then
    status=0
else
    status=$?
fi

# Houd het Terminal-venster open zodat je het resultaat kunt lezen.
printf '\nKlaar (exitcode %s). Druk op Enter om dit venster te sluiten.' "$status"
read -r _
exit "$status"
