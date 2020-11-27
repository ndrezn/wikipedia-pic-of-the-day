#! /bin/bash
set -eo pipefail
python - <<'END_SCRIPT'
import bot
from dotenv import load_dotenv

load_dotenv()
bot.go()
END_SCRIPT
echo "$(date): posted" >> /var/log/cron.log 2>&1
