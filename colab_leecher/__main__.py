# copyright 2024 ©Tessarion | https://github.com/Tessarion-IR


import logging, os
from pyrogram import filters
from datetime import datetime
from pyrogram.errors import BadRequest
from asyncio import sleep, get_event_loop
from colab_leecher import colab_bot, OWNER
from .utility.task_manager import taskScheduler
from colab_leecher.utility.handler import cancelTask
from .utility.variables import BOT, MSG, BotTimes, Paths
from .utility.helper import isLink, setThumbnail, message_deleter
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

src_request_msg = None


@colab_bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.delete()
    text = "**سلام، 👋🏼 من آپلودر رصد هستم**\n\n◲ من یک ربات قدرتمند در انتقال فایل هستم 🚀\n◲ می توانم فایل ها را از منابع مختلف به تلگرام یا درایو گوگل شما منتقل کنم 🦐"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Repository 🦄", url="https://github.com/Tessarion-IR/Rasad-Uplaoder"
                ),
                InlineKeyboardButton("Support 💝", url="https://t.me/"),
            ],
        ]
    )
    await message.reply_text(text, reply_markup=keyboard)


@colab_bot.on_message(filters.command("colabxr") & filters.private)
async def colabxr(client, message):
    global BOT, src_request_msg
    text = "<b>◲ برای من بفرستید لینک(های) دانلود 🔗»\n◲</b> <i>می توانید چندین لینک را در خطوط جدید وارد کنید و من هر یک از آنها را دانلود خواهم کرد 😉 </i>"
    await message.delete()
    BOT.State.started = True
    if BOT.State.task_going == False:
        src_request_msg = await message.reply_text(text)
    else:
        msg = await message.reply_text(
            "دارم روش کار میکنم ! وایسا تموم شه!!"
        )
        await sleep(15)
        await msg.delete()


async def send_settings(client, message, msg_id, command: bool):
    up_mode = "document" if BOT.Options.stream_upload else "media"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"Set {up_mode.capitalize()}", callback_data=up_mode
                ),
                InlineKeyboardButton("Video Convert", callback_data="video"),
            ],
            [
                InlineKeyboardButton("Caption Font", callback_data="caption"),
                InlineKeyboardButton("Thumbnail", callback_data="thumb"),
            ],
            [
                InlineKeyboardButton("Set Suffix", callback_data="set-suffix"),
                InlineKeyboardButton("Set Prefix", callback_data="set-prefix"),
            ],
            [InlineKeyboardButton("Close ✘", callback_data="close")],
        ]
    )
    text = "**تنظیمات بات ⚙️ »**"
    text += f"\n\n╭⌬ UPLOAD » <i>{BOT.Setting.stream_upload}</i>"
    text += f"\n├⌬ CONVERT » <i>{BOT.Setting.convert_video}</i>"
    text += f"\n├⌬ CAPTION » <i>{BOT.Setting.caption}</i>"
    pr = "None" if BOT.Setting.prefix == "" else "Exists"
    su = "None" if BOT.Setting.suffix == "" else "Exists"
    thmb = "None" if not BOT.Setting.thumbnail else "Exists"
    text += f"\n├⌬ PREFIX » <i>{pr}</i>\n├⌬ SUFFIX » <i>{su}</i>"
    text += f"\n╰⌬ THUMBNAIL » <i>{thmb}</i>"
    try:
        if command:
            await message.reply_text(text=text, reply_markup=keyboard)
        else:
            await colab_bot.edit_message_text(
                chat_id=message.chat.id, message_id=msg_id, text=text, reply_markup=keyboard
            )
    except BadRequest as error:
        logging.error(f"متن اصلاح نشده | {error}")
    except Exception as error:
        logging.error(f"اروراصلاح پیام | {error}")


@colab_bot.on_message(filters.command("settings") & filters.private)
async def settings(client, message):
    if message.chat.id == OWNER:
        await message.delete()
        await send_settings(client, message, message.id, True)


@colab_bot.on_message(filters.reply)
async def setPrefix(client, message):
    global BOT, SETTING
    if BOT.State.prefix:
        BOT.Setting.prefix = message.text
        BOT.State.prefix = False

        await send_settings(client, message, message.reply_to_message_id, False)
        await message.delete()
    elif BOT.State.suffix:
        BOT.Setting.suffix = message.text
        BOT.State.suffix = False

        await send_settings(client, message, message.reply_to_message_id, False)
        await message.delete()


@colab_bot.on_message(filters.create(isLink) & ~filters.photo)
async def handle_url(client, message):
    global BOT

    # Reset
    BOT.Options.custom_name = ""
    BOT.Options.zip_pswd = ""
    BOT.Options.unzip_pswd = ""

    if src_request_msg:
        await src_request_msg.delete()
    if BOT.State.task_going == False and BOT.State.started:
        temp_source = message.text.splitlines()

        # Check for arguments in message
        for _ in range(3):
            if temp_source[-1][0] == "[":
                BOT.Options.custom_name = temp_source[-1][1:-1]
                temp_source.pop()
            elif temp_source[-1][0] == "{":
                BOT.Options.zip_pswd = temp_source[-1][1:-1]
                temp_source.pop()
            elif temp_source[-1][0] == "(":
                BOT.Options.unzip_pswd = temp_source[-1][1:-1]
                temp_source.pop()
            else:
                break

        BOT.SOURCE = temp_source
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Leech", callback_data="leech"),
                    InlineKeyboardButton("Mirror", callback_data="mirror"),
                ],
                [InlineKeyboardButton("Dir-Leech", callback_data="dir-leech")],
            ]
        )
        await message.reply_text(
            text="<b>◲ rasad uplaoder Operation MODE را برای این کار فعلی انتخاب کنید 🍳 »</b>",
            reply_markup=keyboard,
            quote=True,
        )
    elif BOT.State.started:
        await message.delete()
        await message.reply_text(
            "<i>دارم روش کار میکنم ! وایسا تموم شه 😣!!</i>"
        )


@colab_bot.on_callback_query()
async def handle_options(client, callback_query):
    global BOT

    if callback_query.data in ["leech", "mirror", "dir-leech"]:
        BOT.Mode.mode = callback_query.data
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Normal", callback_data="normal")],
                [
                    InlineKeyboardButton("Zip", callback_data="zip"),
                    InlineKeyboardButton("Unzip", callback_data="unzip"),
                    InlineKeyboardButton("UnDoubleZip", callback_data="undzip"),
                ],
            ]
        )
        await callback_query.message.edit_text(
            f"<b>◲ بهم بگو کدوم مدل  {BOT.Mode.mode} رو میخوای 🍕» </b>",
            reply_markup=keyboard,
        )
    elif callback_query.data in ["normal", "zip", "unzip", "undzip"]:
        BOT.Mode.type = callback_query.data
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Yes", callback_data="ytdl-true"),
                    InlineKeyboardButton("No", callback_data="ytdl-false"),
                ],
            ]
        )
        await callback_query.message.edit_text(
            "<b>◲ این لینک یوتیوبه ? 🧐</b>", reply_markup=keyboard
        )
    elif callback_query.data == "video":
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Convert", callback_data="convert-true"),
                    InlineKeyboardButton(
                        "Don't Convert", callback_data="convert-false"
                    ),
                ],
                [
                    InlineKeyboardButton("To » Mp4", callback_data="mp4"),
                    InlineKeyboardButton("To » Mkv", callback_data="mkv"),
                ],
                [
                    InlineKeyboardButton("High Quality", callback_data="q-High"),
                    InlineKeyboardButton("Low Quality", callback_data="q-Low"),
                ],
                [InlineKeyboardButton("Back ⏎", callback_data="back")],
            ]
        )
        await callback_query.message.edit_text(
            f"گزینه مورد نظر خود را انتخاب کنید ⚙️ »\n\n╭⌬ CONVERT » <code>{BOT.Setting.convert_video}</code>\n├⌬ OUTPUT FORMAT » <code>{BOT.Options.video_out}</code>\n╰⌬ OUTPUT QUALITY » <code>{BOT.Setting.convert_quality}</code>",
            reply_markup=keyboard,
        )
    elif callback_query.data == "caption":
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Monospace", callback_data="code-Monospace"),
                    InlineKeyboardButton("Bold", callback_data="b-Bold"),
                ],
                [
                    InlineKeyboardButton("Italic", callback_data="i-Italic"),
                    InlineKeyboardButton("Underlined", callback_data="u-Underlined"),
                ],
                [InlineKeyboardButton("Regular", callback_data="p-Regular")],
            ]
        )
        await callback_query.message.edit_text(
            "فونت استایل کپشن رو انتخاب کن »\n\n⌬ <code>Monospace</code>\n⌬ Regular\n⌬ <b>Bold</b>\n⌬ <i>Italic</i>\n⌬ <u>Underlined</u>",
            reply_markup=keyboard,
        )
    elif callback_query.data == "thumb":
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Delete Thumbnail", callback_data="del-thumb"),
                ],
                [
                    InlineKeyboardButton("Go Back ⏎", callback_data="back"),
                ],
            ]
        )
        thmb_ = "None" if not BOT.Setting.thumbnail else "Exists"
        await callback_query.message.edit_text(
            f"تنظیمات تصویر کوچک خود را انتخاب کنید »\n\n⌬ Thumbnail » {thmb_}\n⌬ یک تصویر ارسال کنید تا به عنوان تصویر کوچک شما تنظیم شود",
            reply_markup=keyboard,
        )
    elif callback_query.data == "del-thumb":
        if BOT.Setting.thumbnail:
            os.remove(Paths.THMB_PATH)
        BOT.Setting.thumbnail = False
        await send_settings(
            client, callback_query.message, callback_query.message.id, False
        )
    elif callback_query.data == "set-prefix":
        await callback_query.message.edit_text(
            "با پاسخ دادن به این پیام، یک متن برای تنظیم به عنوان پیشوند ارسال کنید »"
        )
        BOT.State.prefix = True
    elif callback_query.data == "set-suffix":
        await callback_query.message.edit_text(
            "با پاسخ دادن به این پیام، یک متن برای تنظیم به عنوان پیشوند ارسال کنید »"
        )
        BOT.State.suffix = True
    elif callback_query.data in [
        "code-Monospace",
        "p-Regular",
        "b-Bold",
        "i-Italic",
        "u-Underlined",
    ]:
        res = callback_query.data.split("-")
        BOT.Options.caption = res[0]
        BOT.Setting.caption = res[1]
        await send_settings(
            client, callback_query.message, callback_query.message.id, False
        )
    elif callback_query.data in ["convert-true", "convert-false", "mp4", "mkv", "q-High", "q-Low"]:
        if callback_query.data in ["convert-true", "convert-false"]:
            BOT.Options.convert_video = (
                True if callback_query.data == "convert-true" else False
            )
            BOT.Setting.convert_video = (
                "Yes" if callback_query.data == "convert-true" else "No"
            )
        elif callback_query.data in ["q-High", "q-Low"] :
            BOT.Setting.convert_quality = callback_query.data.split("-")[-1]
            BOT.Options.convert_quality = True if BOT.Setting.convert_quality == "High" else False
            await send_settings(
            client, callback_query.message, callback_query.message.id, False
        )
        else:
            BOT.Options.video_out = callback_query.data
        await send_settings(
            client, callback_query.message, callback_query.message.id, False
        )
    elif callback_query.data in ["media", "document"]:
        BOT.Options.stream_upload = True if callback_query.data == "media" else False
        BOT.Setting.stream_upload = (
            "Media" if callback_query.data == "media" else "Document"
        )
        await send_settings(
            client, callback_query.message, callback_query.message.id, False
        )

    elif callback_query.data == "close":
        await callback_query.message.delete()
    elif callback_query.data == "back":
        await send_settings(
            client, callback_query.message, callback_query.message.id, False
        )

    # @main Triggering Actual Leech Functions
    elif callback_query.data in ["ytdl-true", "ytdl-false"]:
        BOT.Mode.ytdl = True if callback_query.data == "ytdl-true" else False
        await callback_query.message.delete()
        await colab_bot.delete_messages(
            chat_id=callback_query.message.chat.id,
            message_ids=callback_query.message.reply_to_message_id,
        )
        MSG.status_msg = await colab_bot.send_message(
            chat_id=OWNER,
            text="#STARTING_TASK\n\n**شروع کار تا چند ثانیه دیگه...🦐**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("انصراف ❌", callback_data="cancel")],
                ]
            ),
        )
        BOT.State.task_going = True
        BOT.State.started = False
        BotTimes.start_time = datetime.now()
        event_loop = get_event_loop()
        BOT.TASK = event_loop.create_task(taskScheduler())  # type: ignore
        await BOT.TASK
        BOT.State.task_going = False

    # If user Wants to Stop The Task
    elif callback_query.data == "cancel":
        await cancelTask("User Cancelled !")


@colab_bot.on_message(filters.photo & filters.private)
async def handle_image(client, message):
    msg = await message.reply_text("<i>تلاش برای ذخیره تصویر کوچک...</i>")
    success = await setThumbnail(message)
    if success:
        await msg.edit_text("**تصویر کوچک با موفقیت تغییر کرد ✅**")
        await message.delete()
    else:
        await msg.edit_text(
            "🥲 **نمی‌توان تصویر کوچک را تنظیم کرد، لطفاً دوباره امتحان کنید!**", quote=True
        )
    await sleep(15)
    await message_deleter(message, msg)


@colab_bot.on_message(filters.command("setname") & filters.private)
async def custom_name(client, message):
    global BOT
    if len(message.command) != 2:
        msg = await message.reply_text(
            "Send\n/setname <code>custom_fileame.extension</code>\nبرای تنظیم نام فایل سفارشی 📛",
            quote=True,
        )
    else:
        BOT.Options.custom_name = message.command[1]
        msg = await message.reply_text(
            "نام دلخواه ست شد !", quote=True
        )

    await sleep(15)
    await message_deleter(message, msg)


@colab_bot.on_message(filters.command("zipaswd") & filters.private)
async def zip_pswd(client, message):
    global BOT
    if len(message.command) != 2:
        msg = await message.reply_text(
            "Send\n/zipaswd <code>password</code>\nبرای تنظیم رمز عبور برای فایل فشرده خروجی. 🔐",
            quote=True,
        )
    else:
        BOT.Options.zip_pswd = message.command[1]
        msg = await message.reply_text(
            "فایل زیپ رمز گزاری شد !", quote=True
        )

    await sleep(15)
    await message_deleter(message, msg)


@colab_bot.on_message(filters.command("unzipaswd") & filters.private)
async def unzip_pswd(client, message):
    global BOT
    if len(message.command) != 2:
        msg = await message.reply_text(
            "Send\n/unzipaswd <code>password</code>\nبرای تنظیم رمز عبور برای استخراج آرشیو. 🔓",
            quote=True,
        )
    else:
        BOT.Options.unzip_pswd = message.command[1]
        msg = await message.reply_text(
            "ان زیپ موفقیت آمیز بود !", quote=True
        )

    await sleep(15)
    await message_deleter(message, msg)


@colab_bot.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    msg = await message.reply_text(
        "Send /start To Check If I am alive 🤨\n\nSend /colabxr and follow prompts to start transloading 🚀\n\nSend /settings to edit bot settings ⚙️\n\nSend /setname To Set Custom File Name 📛\n\nSend /zipaswd To Set Password For Zip File 🔐\n\nSend /unzipaswd To Set Password to Extract Archives 🔓\n\n⚠️ **You can ALWAYS SEND an image To Set it as THUMBNAIL for your files 🌄**",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Instructions 📖",
                        url="https://github.com/Tessarion-IR",
                    ),
                ],
                [
                    InlineKeyboardButton(  # Opens a web URL
                        "Channel 📣",
                        url="https://t.me/",
                    ),
                    InlineKeyboardButton(  # Opens a web URL
                        "Group 💬",
                        url="https://t.me/",
                    ),
                ],
            ]
        ),
    )
    await sleep(15)
    await message_deleter(message, msg)


logging.info("آپلودر رصد شروع کرد!")
colab_bot.run()
