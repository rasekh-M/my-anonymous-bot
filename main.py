from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import logging

TOKEN = '8454274411:AAHWKVlmxku60aTnkOFafjMYh9jLrJSgVEg'
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ذخیره داده ها در حافظه (برای ساده بودن)
users = {}  # user_id: username یا user info
admin_id = 7288118092  # آیدی عددی مدیر

forced_channels = {}  # channel_username: invite_link شیشه ای (پیام شیشه‌ای)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    users[user.id] = user.username or str(user.id)
    link = f"https://t.me/{context.bot.username}?start={user.id}"
    update.message.reply_text(f"سلام!\nاین لینک مخصوص شما برای پیام ناشناس:\n{link}")

def start_with_param(update: Update, context: CallbackContext):
    user = update.effective_user
    users[user.id] = user.username or str(user.id)
    args = context.args
    if args:
        target_id = int(args[0])
        update.message.reply_text("حالا می‌تونی ناشناس پیام بدی!")
        context.user_data['target_id'] = target_id
    else:
        update.message.reply_text("سلام! از لینک درست استفاده کن.")

def anonymous_message(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text
    target_id = context.user_data.get('target_id')

    # چک جوین اجباری
    for ch, invite_link in forced_channels.items():
        try:
            member = context.bot.get_chat_member(ch, user.id)
            if member.status not in ['member', 'creator', 'administrator']:
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("عضو کانال شوید", url=invite_link)]]
                )
                update.message.reply_text("برای استفاده، ابتدا عضو کانال شوید:", reply_markup=keyboard)
                return
        except:
            pass

    if not target_id:
        update.message.reply_text("ابتدا لینک را از پنل مدیریت یا /start دریافت کن.")
        return

    try:
        context.bot.send_message(chat_id=target_id, text=f"پیام ناشناس:\n{text}")
        update.message.reply_text("پیام شما ارسال شد.")
        # پیام را به مدیر هم ارسال کن
        context.bot.send_message(chat_id=admin_id, text=f"کاربر {user.id} به {target_id} پیام داد:\n{text}")
    except Exception as e:
        update.message.reply_text(f"ارسال پیام با خطا مواجه شد: {e}")

def send_to_user(update: Update, context: CallbackContext):
    if update.effective_user.id != admin_id:
        update.message.reply_text("شما اجازه ندارید.")
        return

    args = context.args
    if len(args) < 2:
        update.message.reply_text("استفاده: /send user_id متن پیام")
        return
    try:
        target = int(args[0])
        text = ' '.join(args[1:])
        context.bot.send_message(chat_id=target, text=text)
        update.message.reply_text("پیام ارسال شد.")
    except Exception as e:
        update.message.reply_text(f"خطا: {e}")

def add_channel(update: Update, context: CallbackContext):
    if update.effective_user.id != admin_id:
        update.message.reply_text("شما اجازه ندارید.")
        return

    args = context.args
    if len(args) < 2:
        update.message.reply_text("استفاده: /addchannel @channelusername invite_link")
        return
    channel = args[0]
    link = args[1]
    forced_channels[channel] = link
    update.message.reply_text(f"کانال {channel} به لیست جوین اجباری اضافه شد.")

def remove_channel(update: Update, context: CallbackContext):
    if update.effective_user.id != admin_id:
        update.message.reply_text("شما اجازه ندارید.")
        return
    args = context.args
    if len(args) < 1:
        update.message.reply_text("استفاده: /removechannel @channelusername")
        return
    channel = args[0]
    if channel in forced_channels:
        del forced_channels[channel]
        update.message.reply_text(f"کانال {channel} از لیست حذف شد.")
    else:
        update.message.reply_text("کانال در لیست نیست.")

def list_channels(update: Update, context: CallbackContext):
    if update.effective_user.id != admin_id:
        update.message.reply_text("شما اجازه ندارید.")
        return
    if not forced_channels:
        update.message.reply_text("هیچ کانالی در لیست جوین اجباری نیست.")
        return
    text = "کانال‌های جوین اجباری:\n"
    for ch, link in forced_channels.items():
        text += f"{ch} - [عضویت]({link})\n"
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def handle_id_message(update: Update, context: CallbackContext):
    text = update.message.text
    if text.isdigit():
        context.user_data['target_id'] = int(text)
        update.message.reply_text("حالا متن پیام را ارسال کن.")
    else:
        update.message.reply_text("لطفا فقط آیدی عددی وارد کن.")

def error_handler(update: object, context: CallbackContext):
    logger.warning(f"خطا: {context.error}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("send", send_to_user))
    dp.add_handler(CommandHandler("addchannel", add_channel))
    dp.add_handler(CommandHandler("removechannel", remove_channel))
    dp.add_handler(CommandHandler("listchannels", list_channels))
    dp.add_handler(CommandHandler("start", start_with_param, pass_args=True))
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), anonymous_message))
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), handle_id_message))

    dp.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

