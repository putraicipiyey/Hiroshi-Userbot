# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

from asyncio import sleep
from os import remove

from telethon.errors import (
    BadRequestError,
    ChatAdminRequiredError,
    ImageProcessFailedError,
    PhotoCropSizeSmallError,
    UserAdminInvalidError,
)
from telethon.errors.rpcerrorlist import MessageTooLongError, UserIdInvalidError
from telethon.tl.functions.channels import (
    EditAdminRequest,
    EditBannedRequest,
    EditPhotoRequest,
)
from telethon.tl.functions.messages import UpdatePinnedMessageRequest
from telethon.tl.types import (
    ChannelParticipantsAdmins,
    ChannelParticipantsBots,
    ChatAdminRights,
    ChatBannedRights,
    MessageEntityMentionName,
    MessageMediaPhoto,
    PeerChat,
)

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP
from userbot.utils import (
    edit_delete,
    edit_or_reply,
    hiro_cmd,
)
from userbot import CMD_HANDLER as cmd
from userbot.events import register

# =================== CONSTANT ===================
PP_TOO_SMOL = "`Gambar Terlalu Kecil`"
PP_ERROR = "`Gagal Memproses Gambar`"
NO_ADMIN = "`Maaf Anda Bukan Admin:)`"
NO_PERM = "`Maaf Anda Tidak Mempunyai Izin!`"
NO_SQL = "`Berjalan Pada Mode Non-SQL`"

CHAT_PP_CHANGED = "`Berhasil Mengubah Profil Grup`"
CHAT_PP_ERROR = (
    "`Ada Masalah Dengan Memperbarui Foto,`"
    "`Mungkin Karna Anda Bukan Admin,`"
    "`Atau Tidak Mempunyai Izin.`"
)
INVALID_MEDIA = "`Media Tidak Valid`"

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=True)

UNMUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)
# ================================================


@hiro_cmd(pattern=r"^\.setgpic$")
@register(pattern=r"^\.csetgpic( -s| -d)$", sudo=True)
async def set_group_photo(event):
    "For changing Group dp"
    flag = (event.pattern_match.group(1)).strip()
    if flag == "-s":
        replymsg = await event.get_reply_message()
        photo = None
        if replymsg and replymsg.media:
            if isinstance(replymsg.media, MessageMediaPhoto):
                photo = await event.client.download_media(message=replymsg.photo)
            elif "image" in replymsg.media.document.mime_type.split("/"):
                photo = await event.client.download_file(replymsg.media.document)
            else:
                return await edit_delete(event, INVALID_MEDIA)
        if photo:
            try:
                await event.client(
                    EditPhotoRequest(
                        event.chat_id, await event.client.upload_file(photo)
                    )
                )
                await edit_delete(event, CHAT_PP_CHANGED)
            except PhotoCropSizeSmallError:
                return await edit_delete(event, PP_TOO_SMOL)
            except ImageProcessFailedError:
                return await edit_delete(event, PP_ERROR)
            except Exception as e:
                return await edit_delete(event, f"**ERROR : **`{str(e)}`")
    else:
        try:
            await event.client(EditPhotoRequest(event.chat_id, InputChatPhotoEmpty()))
        except Exception as e:
            return await edit_delete(event, f"**ERROR : **`{e}`")
        await edit_delete(event, "**Foto Profil Grup Berhasil dihapus.**", 30)


@hiro_cmd(pattern="promote(?:\\s|$)([\\s\\S]*)")
@register(pattern=r"^\.cpromote(?:\s|$)([\s\S]*)", sudo=True)
async def promote(event):
    # Get targeted chat
    chat = await event.get_chat()
    # Grab admin status or creator in a chat
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, also return
    if not admin and not creator:
        return await event.edit(NO_ADMIN)

    new_rights = ChatAdminRights(
        add_admins=False,
        invite_users=True,
        change_info=False,
        ban_users=True,
        delete_messages=True,
        pin_messages=True,
    )

    eventhiro = await edit_or_reply(event, "`Promosikan Pengguna Sebagai Admin... Mohon Menunggu`")
    user, rank = await get_user_from_event(event)
    if not rank:
        rank = "Admin"  # Just in case.
    if not user:
        return

    # Try to promote if current user is admin or creator
    try:
        await event.client(EditAdminRequest(promt.chat_id, user.id, new_rights, rank))
        await edit_delete(eventhiro, "`Berhasil Menambahkan Pengguna Ini Sebagai Admin!`")

    # If Telethon spit BadRequestError, assume
    # we don't have Promote permission
    except BadRequestError:
        return await eventhiro.edit(NO_PERM)

    # Announce to the logging group if we have promoted successfully
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            "#PROMOSI\n"
            f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
            f"GRUP: {promt.chat.title}(`{promt.chat_id}`)",
        )


@hiro_cmd(pattern="demote(?:\\s|$)([\\s\\S]*)")
@register(pattern=r"^\.cdemote(?:\s|$)([\s\S]*)", sudo=True)
async def demote(event):
    # Admin right check
    chat = await event.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    if not admin and not creator:
        return await dmod.edit(NO_ADMIN)

    # If passing, declare that we're going to demote
    eventkyy = await edit_or_reply(event, "`Sedang Melepas Admin...`")
    rank = "Admin"  # dummy rank, lol.
    user = await get_user_from_event(dmod)
    user = user[0]
    if not user:
        return

    # New rights after demotion
    newrights = ChatAdminRights(
        add_admins=None,
        invite_users=None,
        change_info=None,
        ban_users=None,
        delete_messages=None,
        pin_messages=None,
    )
    # Edit Admin Permission
    try:
        await event.client(EditAdminRequest(event.chat_id, user.id, newrights, rank))

    # If we catch BadRequestError from Telethon
    # Assume we don't have permission to demote
    except BadRequestError:
        return await eventhiro.edit(NO_PERM)
    await edit_delete(eventhiro, "`Berhasil Melepas Pengguna Ini Sebagai Admin!`")

    # Announce to the logging group if we have demoted successfully
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            "#DEMOTE\n"
            f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
            f"GRUP: {dmod.chat.title}(`{dmod.chat_id}`)",
        )


@hiro_cmd(pattern="ban(?:\\s|$)([\\s\\S]*)")
@register(pattern=r"^\.cban(?:\s|$)([\s\S]*)", sudo=True)
async def ban(bon):
    # Here laying the sanity check
    chat = await bon.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not admin and not creator:
        return await edit_or_reply(bon, NO_ADMIN)

    user, reason = await get_user_from_event(bon)
    if not user:
        return

    # Announce that we're going to whack the pest
    hiro = await edit_or_reply(bon, "`Melakukan Banned!`")

    try:
        await bon.client(EditBannedRequest(bon.chat_id, user.id, BANNED_RIGHTS))
    except BadRequestError:
        return await bon.edit(NO_PERM)
    # Helps ban group join spammers more easily
    try:
        reply = await bon.get_reply_message()
        if reply:
            await reply.delete()
    except BadRequestError:
        return await bon.edit(
            "`Saya tidak memiliki hak pesan nuking! Tapi tetap saja dia di banned!`"
        )
    # Delete message and then tell that the command
    # is done gracefully
    # Shout out the ID, so that fedadmins can fban later
    if reason:
        await hiro.edit(
            f"`PENGGUNA:` [{user.first_name}](tg://user?id={user.id})\n`ID:` `{str(user.id)}` Telah Di Banned !!\n`Alasan:` {reason}"
        )
    else:
        await kyy.edit(
            f"`PENGGUNA:` [{user.first_name}](tg://user?id={user.id})\n`ID:` `{str(user.id)}` Telah Di Banned !"
        )
    # Announce to the logging group if we have banned the person
    # successfully!
    if BOTLOG:
        await bon.client.send_message(
            BOTLOG_CHATID,
            "#BAN\n"
            f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
            f"GRUP: {bon.chat.title}(`{bon.chat_id}`)",
        )


@hiro_cmd(pattern="unban(?:\\s|$)([\\s\\S]*)")
@register(pattern=r"^\.cunban(?:\s|$)([\s\S]*)", sudo=True)
async def nothanos(unbon):
    # Here laying the sanity check
    chat = await unbon.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not admin and not creator:
        return await edit_delete(unbon, NO_ADMIN)

    # If everything goes well...
    hiro = await edit_or_reply(unbon, "`Sedang Melakukan Unban...`")

    user = await get_user_from_event(unbon)
    user = user[0]
    if not user:
        return

    try:
        await unbon.client(EditBannedRequest(unbon.chat_id, user.id, UNBAN_RIGHTS))
        await edit_delete(hiro, "```Berhasil Melepas Ban Pengguna!```")

        if BOTLOG:
            await unbon.client.send_message(
                BOTLOG_CHATID,
                "#UNBAN\n"
                f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
                f"GRUP: {unbon.chat.title}(`{unbon.chat_id}`)",
            )
    except UserIdInvalidError:
        await edit_delete(hiro, "`Sepertinya Terjadi Kesalahan!`")


@hiro_cmd(pattern="mute(?: |$)(.*)")
@register(pattern=r"^\.cmute(?: |$)(.*)", sudo=True)
async def spider(spdr):
    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.spam_mute_sql import mute
    except AttributeError:
        return await edit_or_reply(spdr, NO_SQL)

    # Admin or creator check
    chat = await spdr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await edit_or_reply(spdr, NO_ADMIN)
    hiro = await edit_or_reply(spdr, "`Sedang melakukan Mute...`")
    user, reason = await get_user_from_event(spdr)
    if not user:
        return

    self_user = await spdr.client.get_me()

    if user.id == self_user.id:
        return await edit_or_reply(hiro,
                                   "`Tangan Terlalu Pendek, Tidak Bisa Membisukan Diri Sendiri...\n(ヘ･_･)ヘ┳━┳`"
                                   )

    # If everything goes well, do announcing and mute
    await hiro.edit("`Telah Dibisukan!`")
    if mute(spdr.chat_id, user.id) is False:
        return await hiro.edit("`Pengguna Sudah Dibisukan!`")
    else:
        try:
            await spdr.client(EditBannedRequest(spdr.chat_id, user.id, MUTE_RIGHTS))

            # Announce that the function is done
            if reason:
                await hiro.edit(f"**Pengguna Telah Dibisukan!**\n**Alasan:** `{reason}`")
            else:
                await hiro.edit("`Telah Dibisukan!`")

            # Announce to logging group
            if BOTLOG:
                await spdr.client.send_message(
                    BOTLOG_CHATID,
                    "#MUTE\n"
                    f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
                    f"GRUP: {spdr.chat.title}(`{spdr.chat_id}`)",
                )
        except UserIdInvalidError:
            return await edit_delete(hiro, "`Terjadi Kesalahan!`")


@hiro_cmd(pattern="unmute(?: |$)(.*)")
@register(pattern=r"^\.cunmute(?: |$)(.*)", sudo=True)
async def unmoot(unmot):
    # Admin or creator check
    chat = await unmot.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await edit_delete(unmot, NO_ADMIN)

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.spam_mute_sql import unmute
    except AttributeError:
        return await unmot.edit(NO_SQL)

    # If admin or creator, inform the user and start unmuting
    hiro = await edit_or_reply(unmot, "```Melakukan Unmute...```")
    user = await get_user_from_event(unmot)
    user = user[0]
    if not user:
        return

    if unmute(unmot.chat_id, user.id) is False:
        return await edit_delete(unmot, "`Pengguna Sudah Tidak Dibisukan!`")
    else:

        try:
            await unmot.client(EditBannedRequest(unmot.chat_id, user.id, UNBAN_RIGHTS))
            await edit_delete(hiro, "```Berhasil Melakukan Unmute! Pengguna Sudah Tidak Dibisukan```")
        except UserIdInvalidError:
            return await edit_delete(hiro, "`Terjadi Kesalahan!`")

        if BOTLOG:
            await unmot.client.send_message(
                BOTLOG_CHATID,
                "#UNMUTE\n"
                f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
                f"GRUP: {unmot.chat.title}(`{unmot.chat_id}`)",
            )


@register(incoming=True)
async def muter(moot):
    try:
        from userbot.modules.sql_helper.gmute_sql import is_gmuted
        from userbot.modules.sql_helper.spam_mute_sql import is_muted
    except AttributeError:
        return
    muted = is_muted(moot.chat_id)
    gmuted = is_gmuted(moot.sender_id)
    rights = ChatBannedRights(
        until_date=None,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        embed_links=True,
    )
    if muted:
        for i in muted:
            if str(i.sender) == str(moot.sender_id):
                await moot.delete()
                await moot.client(
                    EditBannedRequest(moot.chat_id, moot.sender_id, rights)
                )
    for i in gmuted:
        if i.sender == str(moot.sender_id):
            await moot.delete()


@hiro_cmd(pattern="ungmute(?: |$)(.*)")
@register(pattern=r"^\.cungmute(?: |$)(.*)", sudo=True)
async def ungmoot(un_gmute):
    # Admin or creator check
    chat = await un_gmute.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await edit_delete(un_gmute, NO_ADMIN)

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.gmute_sql import ungmute
    except AttributeError:
        return await edit_or_reply(un_gmute, NO_SQL)
    hiro = await edit_or_reply(un_gmute, "`Sedang melakukan membuka Global Mute...`")
    user = await get_user_from_event(un_gmute)
    user = user[0]
    if not user:
        return

    # If pass, inform and start ungmuting
    await hiro.edit("```Membuka Global Mute Pengguna...```")

    if ungmute(user.id) is False:
        await hiro.edit("`Pengguna Sedang Tidak Di Gmute!`")
    else:
        # Inform about success
        await edit_delete(un_gmute, "```Berhasil! Pengguna Sudah Tidak Lagi Dibisukan```")

        if BOTLOG:
            await un_gmute.client.send_message(
                BOTLOG_CHATID,
                "#UNGMUTE\n"
                f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
                f"GRUP: {un_gmute.chat.title}(`{un_gmute.chat_id}`)",
            )


@hiro_cmd(pattern="gmute(?: |$)(.*)")
@register(pattern=r"^\.cgmute(?: |$)(.*)", sudo=True)
async def gspider(gspdr):
    # Admin or creator check
    chat = await gspdr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await edit_delete(gspdr, NO_ADMIN)

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.gmute_sql import gmute
    except AttributeError:
        return await edit_delete(gspdr, NO_SQL)
    hiro = await edit_or_reply(gspdr, "`Processing...`")
    user, reason = await get_user_from_event(gspdr)
    if not user:
        return

    # If pass, inform and start gmuting
    await hiro.edit("`Pengguna Berhasil Dibisukan!`")
    if gmute(user.id) is False:
        await edit_delete(gspdr, "`Kesalahan! Pengguna Sudah Dibisukan.`")
    else:
        if reason:
            await kyy.edit(f"**Dibisukan Secara Global!**\n**Alasan:** `{reason}`")
        else:
            await gspdr.edit("`Berhasil Membisukan Pengguna Secara Global!`")

        if BOTLOG:
            await gspdr.client.send_message(
                BOTLOG_CHATID,
                "#GLOBALMUTE\n"
                f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
                f"GRUP: {gspdr.chat.title}(`{gspdr.chat_id}`)",
            )


@hiro_cmd(pattern="zombies(?: |$)(.*)")
async def rm_deletedacc(show):

    con = show.pattern_match.group(1).lower()
    del_u = 0
    del_status = "`Tidak Menemukan Akun Terhapus Di Grup Ini`"

    if con != "clean":
        await show.edit("`Mencari Akun Hantu/Terhapus/Zombie...`")
        async for user in show.client.iter_participants(show.chat_id):

            if user.deleted:
                del_u += 1
                await sleep(1)
        if del_u > 0:
            del_status = (
                f"`Menemukan` **{del_u}** `Akun Hantu/Terhapus/Zombie Dalam Grup Ini,"
                "\nBersihkan Itu Menggunakan Perintah .zombies clean`")
        return await show.edit(del_status)

    # Here laying the sanity check
    chat = await show.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not admin and not creator:
        return await show.edit("`Mohon Maaf, Bukan Admin Disini!`")

    await show.edit("`Menghapus Akun Terhapus...\nMohon Menunggu Sedang Dalam Proses`")
    del_u = 0
    del_a = 0

    async for user in show.client.iter_participants(show.chat_id):
        if user.deleted:
            try:
                await show.client(
                    EditBannedRequest(show.chat_id, user.id, BANNED_RIGHTS)
                )
            except ChatAdminRequiredError:
                return await show.edit("`Tidak Memiliki Izin Banned Dalam Grup Ini`")
            except UserAdminInvalidError:
                del_u -= 1
                del_a += 1
            await show.client(EditBannedRequest(show.chat_id, user.id, UNBAN_RIGHTS))
            del_u += 1

    if del_u > 0:
        del_status = f"`Membersihkan` **{del_u}** `Akun Terhapus`"

    if del_a > 0:
        del_status = (
            f"Membersihkan **{del_u}** Akun Terhapus "
            f"\n**{del_a}** `Admin Akun Terhapus Tidak Bisa Dihapus.`"
        )
    await show.edit(del_status)
    await sleep(2)
    await show.delete()

    if BOTLOG:
        await show.client.send_message(
            BOTLOG_CHATID,
            "#MEMBERSIHKAN\n"
            f"Membersihkan **{del_u}** Akun Terhapus!"
            f"\nGRUP: {show.chat.title}(`{show.chat_id}`)",
        )


@hiro_cmd(pattern="admins$")
async def get_admin(show):
    info = await show.client.get_entity(show.chat_id)
    title = info.title if info.title else "Grup Ini"
    mentions = f"<b>✥ Daftar Admin Grup {title}:</b> \n"
    try:
        async for user in show.client.iter_participants(
            show.chat_id, filter=ChannelParticipantsAdmins
        ):
            if not user.deleted:
                link = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
                mentions += f"\n➤ {link}"
            else:
                mentions += f"\nAkun Terhapus <code>{user.id}</code>"
    except ChatAdminRequiredError as err:
        mentions += " " + str(err) + "\n"
    await show.edit(mentions, parse_mode="html")


@hiro_cmd(pattern="pin( loud|$)")
@register(pattern=r"^\.cpin( loud|$)", sudo=True)
async def pin(msg):
    # Admin or creator check
    chat = await msg.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await edit_delete(msg, NO_ADMIN)

    to_pin = msg.reply_to_msg_id

    if not to_pin:
        return await edit_delete(msg, "`Mohon Balas Ke Pesan Untuk Melakukan Pin.`")

    options = msg.pattern_match.group(1)

    is_silent = True

    if options.lower() == "loud":
        is_silent = False

    try:
        await msg.client(UpdatePinnedMessageRequest(msg.to_id, to_pin, is_silent))
    except BadRequestError:
        return await edit_delete(msg, NO_PERM)

    await edit_delete(msg, "`Berhasil Melakukan Pinned!`")

    user = await get_user_from_id(msg.from_id, msg)

    if BOTLOG:
        await msg.client.send_message(
            BOTLOG_CHATID,
            "#PIN\n"
            f"ADMIN: [{user.first_name}](tg://user?id={user.id})\n"
            f"GRUP: {msg.chat.title}(`{msg.chat_id}`)\n"
            f"NOTIF: {not is_silent}",
        )


@hiro_cmd(pattern="kick(?: |$)(.*)")
@register(pattern=r"^\.ckick(?: |$)(.*)", sudo=True)
async def kick(usr):
    # Admin or creator check
    chat = await usr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await edit_delete(usr, NO_ADMIN)

    user, reason = await get_user_from_event(usr)
    if not user:
        return await edit_delete(usr, "`Tidak Dapat Menemukan Pengguna.`")

    xnxx = await edit_delete(usr, "`Melakukan Kick....`")

    try:
        await usr.client.kick_participant(usr.chat_id, user.id)
        await sleep(0.5)
    except Exception as e:
        return await edit_delete(usr, NO_PERM + f"\n{str(e)}")

    if reason:
        await xnxx.edit(
            f"[{user.first_name}](tg://user?id={user.id}) **Telah Dikick Dari Grup**\n**Alasan:** `{reason}`"
        )
    else:
        await xnxx.edit(f"[{user.first_name}](tg://user?id={user.id}) **Telah Dikick Dari Grup**")
        await sleep(5)
        await usr.delete()

    if BOTLOG:
        await usr.client.send_message(
            BOTLOG_CHATID,
            "#KICK\n"
            f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
            f"GRUP: {usr.chat.title}(`{usr.chat_id}`)\n",
        )


@hiro_cmd(pattern="users$")
async def get_users(show):
    info = await show.client.get_entity(show.chat_id)
    title = info.title if info.title else "Grup Ini"
    mentions = "Pengguna Di {}: \n".format(title)
    try:
        if not show.pattern_match.group(1):
            async for user in show.client.iter_participants(show.chat_id):
                if not user.deleted:
                    mentions += (
                        f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
                else:
                    mentions += f"\nAkun Terhapus `{user.id}`"
        else:
            searchq = show.pattern_match.group(1)
            async for user in show.client.iter_participants(
                show.chat_id, search=f"{searchq}"
            ):
                if not user.deleted:
                    mentions += (
                        f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
                else:
                    mentions += f"\nAkun Terhapus `{user.id}`"
    except ChatAdminRequiredError as err:
        mentions += " " + str(err) + "\n"
    try:
        await show.edit(mentions)
    except MessageTooLongError:
        await show.edit("Grup Ini Terlalu Besar Mengunggah Daftar Pengguna Sebagai File.")
        file = open("daftarpengguna.txt", "w+")
        file.write(mentions)
        file.close()
        await show.client.send_file(
            show.chat_id,
            "daftarpengguna.txt",
            caption="Pengguna Dalam Grup {}".format(title),
            reply_to=show.id,
        )
        remove("daftarpengguna.txt")


async def get_user_from_event(event):
    args = event.pattern_match.group(1).split(" ", 1)
    extra = None
    if event.reply_to_msg_id and len(args) != 2:
        previous_message = await event.get_reply_message()
        user_obj = await event.client.get_entity(previous_message.from_id)
        extra = event.pattern_match.group(1)
    elif args:
        user = args[0]
        if len(args) == 2:
            extra = args[1]

        if user.isnumeric():
            user = int(user)

        if not user:
            return await event.edit("`Ketik Username Atau Balas Ke Pengguna!`")

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(
                    probable_user_mention_entity,
                    MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                user_obj = await event.client.get_entity(user_id)
                return user_obj
        try:
            user_obj = await event.client.get_entity(user)
        except (TypeError, ValueError) as err:
            return await event.edit(str(err))

    return user_obj, extra


async def get_user_from_id(user, event):
    if isinstance(user, str):
        user = int(user)

    try:
        user_obj = await event.client.get_entity(user)
    except (TypeError, ValueError) as err:
        return await event.edit(str(err))

    return user_obj


@hiro_cmd(pattern="userdel$")
async def get_usersdel(show):
    info = await show.client.get_entity(show.chat_id)
    title = info.title if info.title else "Grup Ini"
    mentions = "Akun Terhapus Di {}: \n".format(title)
    try:
        if not show.pattern_match.group(1):
            async for user in show.client.iter_participants(show.chat_id):
                if not user.deleted:
                    mentions += (
                        f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
        #       else:
        #                mentions += f"\nAkun Terhapus `{user.id}`"
        else:
            searchq = show.pattern_match.group(1)
            async for user in show.client.iter_participants(
                show.chat_id, search=f"{searchq}"
            ):
                if not user.deleted:
                    mentions += (
                        f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
        #       else:
    #              mentions += f"\nAkun Terhapus `{user.id}`"
    except ChatAdminRequiredError as err:
        mentions += " " + str(err) + "\n"
    try:
        await show.edit(mentions)
    except MessageTooLongError:
        await show.edit(
            "Grup Ini Terlalu Besar, Mengunggah Daftar Akun Terhapus Sebagai File."
        )
        file = open("daftarpengguna.txt", "w+")
        file.write(mentions)
        file.close()
        await show.client.send_file(
            show.chat_id,
            "daftarpengguna.txt",
            caption="Daftar Pengguna {}".format(title),
            reply_to=show.id,
        )
        remove("daftarpengguna.txt")


async def get_userdel_from_event(event):
    args = event.pattern_match.group(1).split(" ", 1)
    extra = None
    if event.reply_to_msg_id and len(args) != 2:
        previous_message = await event.get_reply_message()
        user_obj = await event.client.get_entity(previous_message.from_id)
        extra = event.pattern_match.group(1)
    elif args:
        user = args[0]
        if len(args) == 2:
            extra = args[1]

        if user.isnumeric():
            user = int(user)

        if not user:
            return await event.edit("`Ketik username Atau Reply Ke Pengguna!`")

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(
                    probable_user_mention_entity,
                    MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                user_obj = await event.client.get_entity(user_id)
                return user_obj
        try:
            user_obj = await event.client.get_entity(user)
        except (TypeError, ValueError) as err:
            return await event.edit(str(err))

    return user_obj, extra


async def get_userdel_from_id(user, event):
    if isinstance(user, str):
        user = int(user)

    try:
        user_obj = await event.client.get_entity(user)
    except (TypeError, ValueError) as err:
        return await event.edit(str(err))

    return user_obj


@hiro_cmd(pattern="bots$")
async def get_bots(show):
    info = await show.client.get_entity(show.chat_id)
    title = info.title if info.title else "Grup Ini"
    mentions = f"<b>Daftar Bot Di {title}:</b>\n"
    try:
        if isinstance(show.to_id, PeerChat):
            return await show.edit("`Saya mendengar bahwa hanya Supergrup yang dapat memiliki bot`")
        else:
            async for user in show.client.iter_participants(
                show.chat_id, filter=ChannelParticipantsBots
            ):
                if not user.deleted:
                    link = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
                    userid = f"<code>{user.id}</code>"
                    mentions += f"\n{link} {userid}"
                else:
                    mentions += f"\nBot Terhapus <code>{user.id}</code>"
    except ChatAdminRequiredError as err:
        mentions += " " + str(err) + "\n"
    try:
        await show.edit(mentions, parse_mode="html")
    except MessageTooLongError:
        await show.edit("Terlalu Banyak Bot Di Grup Ini, Mengunggah Daftar Bot Sebagai File.")
        file = open("botlist.txt", "w+")
        file.write(mentions)
        file.close()
        await show.client.send_file(
            show.chat_id,
            "botlist.txt",
            caption="Daftar Bot Di {}".format(title),
            reply_to=show.id,
        )
        remove("botlist.txt")


CMD_HELP.update(
    {
        "admin": f"𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}promote` <username/balas ke pesan> <nama title (optional)>"
        "\n↳ : Mempromosikan member sebagai admin."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}demote` <username/balas ke pesan>"
        "\n↳ : Menurunkan admin sebagai member."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}ban` <username/balas ke pesan> <alasan (optional)>"
        "\n↳ : Memblokir Seseorang."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}unban <username/reply>`"
        "\n↳ : Menghapus Blokir."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}mute` <username/balas ke pesan> <alasan (optional)>"
        "\n↳ : Membisukan Seseorang Di Grup, Bisa Ke Admin Juga."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}unmute` <username/balas ke pesan>"
        "\n↳ : Membuka bisu orang yang dibisukan."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}gmute` <username/balas ke pesan> <alasan (optional)>"
        "\n↳ : Membisukan ke semua grup yang kamu punya sebagai admin."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}ungmute` <username/reply>"
        "\n↳ : Reply someone's message with `.ungmute` to remove them from the gmuted list."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}zombies`"
        "\n↳ : Untuk mencari akun terhapus dalam grup."
        f"Gunakan `{cmd}zombies clean` untuk menghapus Akun Terhapus dari grup."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}all`"
        "\n↳ : Tag semua member dalam grup."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}admins`"
        "\n↳ : Melihat daftar admin di grup."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}bots`"
        "\n↳ : Melihat daftar bot dalam grup."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}users` Atau >`{cmd}users` <nama member>"
        "\n↳ : Mendapatkan daftar pengguna daam grup."
        f"\n\n𝘾𝙤𝙢𝙢𝙖𝙣𝙙: `{cmd}setgpic` <balas ke gambar>"
        "\n↳ : Mengganti foto profil grup."})
