from telethon import Button

from userbot import BOTLOG, BOTLOG_CHATID, LOGS, tgbot


async def startupmessage():
    """
    Start up message in telegram logger group
    """
    try:
        if BOTLOG:
            await tgbot.send_file(
                BOTLOG_CHATID,
                "https://telegra.ph/file/040c6a31ae08e75059ccf.jpg",
                caption="š„ **Hiroshi Userbot Has Been Actived**!!\nāāāāāāāāāāāāāāā\nā  **Userbot Version** - 8.0@master\nāāāāāāāāāāāāāāā\nā  **Powered By:** @bombleebas ",
                buttons=[(Button.url("ź±į“į“į“į“Źį“", "https://t.me/hiroshisupport"),)],
            )
    except Exception as e:
        LOGS.error(e)
        return None
