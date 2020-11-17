#! /bin/bash
set -eo pipefail
eval $(conda shell.bash hook) activate wikipedia
python - <<'END_SCRIPT'
import bot
from dotenv import load_dotenv

load_dotenv()
bot.go()
END_SCRIPT
echo "$(date): posted"