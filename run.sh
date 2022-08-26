#! /bin/bash
set -eo pipefail
python - <<'END_SCRIPT'
import bot

bot.go()
END_SCRIPT
echo "$(date): posted"
