from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from Framework import bot
from Framework.helpers.decorators import owner
from Framework.helpers.owner_id import OWNER_ID

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

def _get_help_text(user_id: int) -> str:
    text = "**Available Commands**\n"
    text += USER_COMMANDS
    
    # Check if user is owner
    if user_id in OWNER_ID:
        text += f"\n{OWNER_COMMANDS}"
    
    text += "\n\n**Find more information here:**\n• [GitHub Organization](https://github.com/FrameworksForge)"
    return text

@bot.on_message(filters.private & filters.command("help"))
async def help_command_handler(client: Client, message: Message):
    """Handles the /help command and lists available commands."""
    text = _get_help_text(message.from_user.id)
    await message.reply_text(text, quote=True, disable_web_page_preview=True)

@bot.on_callback_query(filters.regex(r"^help$"))
async def help_callback(client: Client, query: CallbackQuery):
    """Handles callback for the help button."""
    text = _get_help_text(query.from_user.id)
    await query.message.edit_text(text, disable_web_page_preview=True)
    await query.answer()
