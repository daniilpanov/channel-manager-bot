from config import bot
from commands import init


# ENGINE (commands list)
init()

# START
bot.infinity_polling()
