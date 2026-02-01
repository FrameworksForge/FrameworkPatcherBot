from pyrogram import Client, filters
from pyrogram.types import Message

from Framework import bot
from Framework.helpers.decorators import owner

USER_COMMANDS = """
**User Commands:**
• /start - Start the bot
• /start_patch - Start patching framework
• /cancel - Cancel current operation
• /ping - Check bot latency
• /help - Show this help message
"""

OWNER_COMMANDS = """
**Owner Commands:**
• /update - Check and pull updates
• /restart - Restart the bot
• /status - View bot system status
• /sh - Execute shell commands
• /logs - View recent logs
• /logfile - Send log file
• /clearlogs - Clear all log files
• /deploy - Run deployment script
"""

@bot.on_message(filters.private & filters.command("help"))
async def help_command_handler(client: Client, message: Message):
    """Handles the /help command and lists available commands."""
    text = "**Available Commands**\n"
    text += USER_COMMANDS
    
    # Check if user is owner
    from Framework import OWNER_ID
    if message.from_user.id == OWNER_ID:
        text += f"\n{OWNER_COMMANDS}"
    
    await message.reply_text(text, quote=True)
