from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from Framework import bot
from Framework.helpers.state import *
from Framework.helpers.workflows import get_default_feature_state, get_feature_catalog_for_api, get_selected_feature_labels

# Feature to JAR requirements mapping
# Defines which JAR files are required for each feature
FEATURE_JAR_REQUIREMENTS = {
    "enable_signature_bypass": ["framework.jar", "services.jar", "miui-services.jar"],
    "enable_cn_notification_fix": ["miui-services.jar"],
    "enable_disable_secure_flag": ["services.jar", "miui-services.jar"],
    "enable_kaorios_toolbox": ["framework.jar"],
    "enable_add_gboard": ["miui-services.jar", "miui-framework.jar"],
}


def get_required_jars(features: dict) -> set:
    """Calculate which JARs are required based on selected features."""
    required_jars = set()
    
    if features.get("enable_signature_bypass", False):
        required_jars.update(FEATURE_JAR_REQUIREMENTS["enable_signature_bypass"])
    if features.get("enable_cn_notification_fix", False):
        required_jars.update(FEATURE_JAR_REQUIREMENTS["enable_cn_notification_fix"])
    if features.get("enable_disable_secure_flag", False):
        required_jars.update(FEATURE_JAR_REQUIREMENTS["enable_disable_secure_flag"])
    if features.get("enable_kaorios_toolbox", False):
        required_jars.update(FEATURE_JAR_REQUIREMENTS["enable_kaorios_toolbox"])
    if features.get("enable_add_gboard", False):
        required_jars.update(FEATURE_JAR_REQUIREMENTS["enable_add_gboard"])
    
    # Default to signature bypass if no features selected
    if not required_jars:
        required_jars.update(FEATURE_JAR_REQUIREMENTS["enable_signature_bypass"])
    
    return required_jars


@bot.on_message(filters.private & filters.command("start_patch"))
async def start_patch_command(bot: Client, message: Message, user_id: int = None):
    """Initiates the framework patching conversation."""
    user_id = user_id or message.from_user.id
    # Initialize state and prompt for device codename
    user_states[user_id] = {
        "state": STATE_WAITING_FOR_DEVICE_CODENAME,
        "files": {},
        "device_name": None,
        "device_codename": None,
        "version_name": None,
        "android_version": None,
        "api_level": None,
        "codename_retry_count": 0,
        "software_data": None,
        "features": {
            **get_default_feature_state(),
        }
    }
    await bot.send_message(
        chat_id=message.chat.id,
        text=(
            "🚀 Let's start the framework patching process!\n\n"
            "📱 Please enter your device codename (e.g., rothko, xaga, marble)\n\n"
            "💡 Tip: You can also search by device name if you don't know the codename."
        ),
        reply_to_message_id=message.id if message.from_user.id == user_id else None
    )


@bot.on_callback_query(filters.regex(r"^start_patch$"))
async def start_patch_callback(client: Client, query: CallbackQuery):
    """Handles callback for the start_patch button."""
    await start_patch_command(client, query.message, user_id=query.from_user.id)
    await query.answer()


@bot.on_callback_query(filters.regex(r"^reselect_codename$"))
async def reselect_codename_handler(bot: Client, query: CallbackQuery):
    """Handles reselecting device codename."""
    user_id = query.from_user.id
    if user_id not in user_states:
        await query.answer("Session expired. Use /start_patch to begin.", show_alert=True)
        return

    # Reset to codename selection state
    user_states[user_id]["state"] = STATE_WAITING_FOR_DEVICE_CODENAME
    user_states[user_id]["device_codename"] = None
    user_states[user_id]["device_name"] = None
    user_states[user_id]["software_data"] = None
    user_states[user_id]["codename_retry_count"] = 0
    
    await query.message.edit_text(
        "📱 Please enter your device codename (e.g., rothko, xaga, marble)\n\n"
        "💡 Tip: You can also search by device name if you don't know the codename."
    )
    await query.answer("Codename reset. Enter a new codename.")


@bot.on_callback_query(filters.regex(r"^feature_(signature|cn_notif|secure_flag|kaorios|gboard)$"))
async def feature_toggle_handler(bot: Client, query: CallbackQuery):
    """Handles toggling features on/off."""
    user_id = query.from_user.id
    if user_id not in user_states or user_states[user_id].get("state") != STATE_WAITING_FOR_FEATURES:
        await query.answer("Not expecting feature selection.", show_alert=True)
        return
    
    android_version = user_states[user_id].get("android_version", "15")
    feature_key = None
    for feature in get_feature_catalog_for_api(android_version):
        if feature["callback_data"] == query.data:
            feature_key = feature["state_key"]
            break

    if feature_key:
        # Toggle feature
        user_states[user_id]["features"][feature_key] = not user_states[user_id]["features"][feature_key]
    
    # Update button display
    features = user_states[user_id]["features"]
    buttons = []
    for feature in get_feature_catalog_for_api(android_version):
        state_key = feature["state_key"]
        buttons.append([
            InlineKeyboardButton(
                f"{'✓' if features.get(state_key) else '☐'} {feature['button_label']}",
                callback_data=feature["callback_data"],
            )
        ])

    buttons.append([InlineKeyboardButton("Continue with selected features", callback_data="features_done")])

    await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
    await query.answer(f"Feature {'enabled' if user_states[user_id]['features'][feature_key] else 'disabled'}")


@bot.on_callback_query(filters.regex(r"^features_done$"))
async def features_done_handler(bot: Client, query: CallbackQuery):
    """Handles when user is done selecting features."""
    user_id = query.from_user.id
    if user_id not in user_states or user_states[user_id].get("state") != STATE_WAITING_FOR_FEATURES:
        await query.answer("Not expecting feature confirmation.", show_alert=True)
        return
    
    features = user_states[user_id]["features"]
    
    # Check if at least one feature is selected
    if not any(features.values()):
        await query.answer("⚠ Please select at least one feature!", show_alert=True)
        return
    
    # Build features summary
    selected_features = get_selected_feature_labels(features)
    
    features_text = "\n".join(selected_features)
    
    # Get required JARs based on selected features
    required_jars = get_required_jars(features)
    user_states[user_id]["required_jars"] = required_jars
    
    # Build JAR list message
    jar_list = "\n".join([f"• {jar}" for jar in sorted(required_jars)])
    android_version = str(user_states[user_id].get("android_version", ""))
    legacy_notice = ""
    if android_version in {"13", "14"}:
        legacy_notice = (
            "\n\n⚠️ Legacy notice: Android 13/14 builds are still runnable, "
            "but platform rollout priority is lower than Android 15/16."
        )
    
    user_states[user_id]["state"] = STATE_WAITING_FOR_FILES
    await query.message.edit_text(
        f"✅ Features selected:\n\n{features_text}\n\n"
        f"📦 **Required JAR files ({len(required_jars)}):**\n{jar_list}\n\n"
        "Please send the JAR files listed above."
        f"{legacy_notice}"
    )
    await query.answer("Features confirmed!")
