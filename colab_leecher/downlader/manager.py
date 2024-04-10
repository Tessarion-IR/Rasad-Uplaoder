# copyright 2024 ©Tessarion | https://github.com/Tessarion-IR


import logging
from natsort import natsorted
from datetime import datetime
from asyncio import sleep, get_running_loop
from colab_leecher.downlader.mega import megadl
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from colab_leecher.utility.handler import cancelTask
from colab_leecher.downlader.ytdl import YTDL_Status, get_YT_Name
from colab_leecher.downlader.aria2 import aria2_Download, get_Aria2c_Name
from colab_leecher.utility.helper import isYtdlComplete, keyboard, sysINFO
from colab_leecher.downlader.telegram import TelegramDownload, media_Identifier
from colab_leecher.utility.variables import BOT, Gdrive, Transfer, MSG, Messages, Aria2c, BotTimes
from colab_leecher.downlader.gdrive import (
    build_service,
    g_DownLoad,
    get_Gfolder_size,
    getFileMetadata,
    getIDFromURL,
)


async def downloadManager(source, is_ytdl: bool):
    message = "\n<b>Please Wait...</b> ⏳\n<i>Merging YTDL Video...</i> 🐬"
    BotTimes.task_start = datetime.now()
    if is_ytdl:
        for i, link in enumerate(source):
            await YTDL_Status(link, i + 1)
        try:
            await MSG.status_msg.edit_text(
                text=Messages.task_msg + Messages.status_head + message + sysINFO(),
                reply_markup=keyboard(),
            )
        except Exception:
            pass
        while not isYtdlComplete():
            await sleep(2)
    else:
        for i, link in enumerate(source):
            try:
                if "drive.google.com" in link:
                    await g_DownLoad(link, i + 1)
                elif "t.me" in link:
                    await TelegramDownload(link, i + 1)
                elif "youtube.com" in link or "youtu.be" in link:
                    await YTDL_Status(link, i + 1)
                    try:
                        await MSG.status_msg.edit_text(
                            text=Messages.task_msg
                            + Messages.status_head
                            + message
                            + sysINFO(),
                            reply_markup=keyboard(),
                        )
                    except Exception:
                        pass
                    while not isYtdlComplete():
                        await sleep(2)
                elif "mega.nz" in link:
                    executor = ProcessPoolExecutor()
                    # await loop.run_in_executor(executor, megadl, link, i + 1)
                    await megadl(link, i + 1)
                else:
                    aria2_dn = f"<b>PLEASE WAIT ⌛</b>\n\n__Getting Download Info For__\n\n<code>{link}</code>"
                    try:
                        await MSG.status_msg.edit_text(
                            text=aria2_dn + sysINFO(), reply_markup=keyboard()
                        )
                    except Exception as e1:
                        print(f"متن به‌روزرسانی نشد! زیرا: {e1}")
                    Aria2c.link_info = False
                    await aria2_Download(link, i + 1)
            except Exception as Error:
                await cancelTask(f"خطا در بارگیری: {str(Error)}")
                logging.error(f"خطا در حین دانلود: {Error}")
                return


async def calDownSize(sources):
    global TRANSFER_INFO
    for link in natsorted(sources):
        if "drive.google.com" in link:
            await build_service()
            id = await getIDFromURL(link)
            try:
                meta = getFileMetadata(id)
            except Exception as e:
                if "File not found" in str(e):
                    err = "لینک فایلی که دادی یا وجود نداره یا بهش دسترسی نداری!"
                elif "بازیابی نشد" in str(e):
                    err = "خطای مجوز در گوگل! مطمئن شوید که تولید کرده اید token.pickle !"
                else:
                    err = f"Error in G-API: {e}"
                logging.error(err)
                await cancelTask(err)
            else:
                if meta.get("mimeType") == "application/vnd.google-apps.folder":
                    Transfer.total_down_size += get_Gfolder_size(id)
                else:
                    Transfer.total_down_size += int(meta["size"])
        elif "t.me" in link:
            media, _ = await media_Identifier(link)
            if media is not None:
                size = media.file_size
                Transfer.total_down_size += size
            else:
                logging.error("پیام تلگرام دانلود نشد")
        else:
            pass


async def get_d_name(link: str):
    global Messages, Gdrive
    if len(BOT.Options.custom_name) != 0:
        Messages.download_name = BOT.Options.custom_name
        return
    if "drive.google.com" in link:
        id = await getIDFromURL(link)
        meta = getFileMetadata(id)
        Messages.download_name = meta["name"]
    elif "t.me" in link:
        media, _ = await media_Identifier(link)
        Messages.download_name = media.file_name if hasattr(media, "file_name") else "None"  # type: ignore
    elif "youtube.com" in link or "youtu.be" in link:
        Messages.download_name = await get_YT_Name(link)
    elif "mega.nz" in link:
        Messages.download_name = "نمی دانم 🥲 (در حال تلاش)" # TODO: دریافت نام دانلود از طریق megadl
    else:
        Messages.download_name = get_Aria2c_Name(link)