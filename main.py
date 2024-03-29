import os
import threading
import subprocess
import time
import json
import asyncio

import pyrogram
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply, BotCommand

from mdisk import iswin, getinfo, mdow, merge
import mediainfo
from split import TG_SPLIT_SIZE, split_file, get_path_size, ss, temp_channel, isPremmium
from config import ID,HASH,TOKEN,STRING,AUTH,BAN,OWNER,TARGET,LINK
# conifg


# app
TOKEN = TOKEN
HASH = HASH
ID = ID
app = Client("my_bot", api_id=ID, api_hash=HASH, bot_token=TOKEN)

# preiumum
if isPremmium: acc = Client("myacc", api_id=ID, api_hash=HASH, session_string=ss)

# optionals
AUTH=AUTH
AUTHUSER=[5616727536,5910057231,2145093972]

# control
OWNER=OWNER
#OWNER.append(5910057231)
OWNERS = OWNER
TARGET = TARGET
LINK = LINK


# setting commands
cmds = ["start","help","mdisk","thumb","remove","show","change"]
descs = ["Bᴀsɪᴄ Usᴀɢᴇ","Hᴇʟᴘ Mᴇssᴀɢᴇ","Usᴀɢᴇ","Reply to a Image of size less than 200KB to set it as Thumbnail","Remove Thumbnail","Show Thumbnail","Change Upload Mode"]
with app: app.set_bot_commands(BotCommand(cmds[i].lower(),descs[i]) for i in range(len(cmds)))


# formats data
datalist = {}
def adddata(id,mod): datalist[id] = mod
def getdata(id): return datalist.get(id,"D")
def swap(id):
    temp = getdata(id)
    if temp == "V": adddata(id,"D")
    else: adddata(id,"V")
    return getdata(id)


# msgs data
msgsdata = {}
def store(message,info,link): msgsdata[str(message.id)] = [message,info,link]
def get(id): return msgsdata.get(str(id), [None,None,None])


# locks
locks = {}
def setlock(uid,mid): locks[str(uid)] = mid
def getlock(uid): return locks.get(str(uid), None)


# progress tracker
prev = {}
prevtime = {}

# Create a progress bar
def progress_bar(progress):
    bar_length = 12
    filled_length = int(progress / (100/bar_length))
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    return f"[{bar}] {progress:.2f}%"

# format msgs
def getformatmsg(filename,status,procs,size,firsttime=False):
    if firsttime:
        previous_progress = 0
        previous_time = time.time()
    else:
        previous_progress = prev[filename]
        previous_time = prevtime[filename]

    progress = procs / size * 100
    speed = (progress - previous_progress) / (time.time() - previous_time) * 12.4
    prev[filename] = progress
    prevtime[filename] = time.time()

    return f"**{filename}**\n\n\
┌ Status: **{status}**\n\
├ {progress_bar(progress)}\n\
├ Processed: **{procs/1048000:.2f} MB**\n\
├ Total Size: **{size/1048000:.2f} MB**\n\
└ Speed: **{speed:.2f} MB/s**"


# check for user access
"""def checkuser(message):
    if isowner(message): return True
    user_id = str(message.from_user.id)
    if AUTHUSERS and user_id not in AUTHUSERS: return False
    if user_id in BANNEDUSERS: return False
    return True


# check for owner
def isowner(message):
    if str(message.from_user.id) in OWNERS: return True
    return False

"""
# download status
async def status(folder,message,fsize,filename):

    # wait for the folder to create
    while True:
        if os.path.exists(folder + "/vid.mp4.part-Frag0") or os.path.exists(folder + "/vid.mp4.part"):
            break
    
    time.sleep(3)
    while os.path.exists(folder + "/" ):
        if "Status: Merging" in app.get_messages(message.chat.id, message.id).text: return

        if iswin == "0":
            result = subprocess.run(["du", "-hsb", f"{folder}/"], capture_output=True, text=True)
            size = float(str(result.stdout).split()[0])
        else:
            os.system(f"dir /a/s {folder} > tempS-{message.id}.txt")
            size = float(open(f"tempS-{message.id}.txt","r").readlines()[-2].split()[2].replace(",",""))

        try:
            await app.edit_message_text(message.chat.id, message.id, getformatmsg(filename,"Downloading",size,fsize))
            time.sleep(10)
        except:
            time.sleep(5)

    if iswin != "0": os.remove(f"tempS-{message.id}.txt")


# upload status
async def upstatus(statusfile,message,filename):
    while True:
        if os.path.exists(statusfile):
            break

    time.sleep(3)      
    while os.path.exists(statusfile):
        with open(statusfile,"r") as upread:
            txt = upread.read().split()
        try:
            await app.edit_message_text(message.chat.id, message.id, getformatmsg(filename,"Uploading",float(txt[0]),float(txt[1])))
            time.sleep(10)
        except:
            time.sleep(5)


# progress writter
def progress(current, total, message):
    with open(f'{message.id}upstatus.txt',"w") as fileup:
        fileup.write(f'{current} {total}')


# format printter
async def formatprint(id,link="",edit=False,call=None, emsg=None):
    
    message,alldata,link = get(id)
    if message is None:
        await app.edit_message_text(call.message.chat.id,call.message.id,"__Expired__")
        return
    m, s = divmod(alldata['duration'], 60)
    h, m = divmod(m, 60)
    format = "Document" if getdata(str(message.from_user.id)) == "D" else "Media/Stream"
    thumb,thum = ("Exists","Remove Thumbnail") if os.path.exists(f'{message.from_user.id}-thumb.jpg') else ("Not Exists","Set Thumbnail")
    text = f'__Filename:__ `{alldata["filename"]}`\n__Link:__ {link}\n\
__Size:__ **{alldata["size"]//1048000} MB**\n__Duration:__ **{h}h{m}m{s}s**\n\
__Resolution:__ **{alldata["width"]}x{alldata["height"]}**\n\
__Format:__ **{format}**\n__Thumbnail:__ **{thumb}**'
    keybord = InlineKeyboardMarkup(
            [   
                [
                    InlineKeyboardButton("Rᴇɴᴀᴍᴇ", callback_data=f'rename {message.id}'),
                    InlineKeyboardButton("Cʜᴀɴɢᴇ Fᴏʀᴍᴀᴛ", callback_data=f'change {message.id}')
                ],
                [ 
                    InlineKeyboardButton("Tʜᴜᴍʙɴᴀɪʟ", callback_data=f'thumb {message.id}'),
                    InlineKeyboardButton("ᴅᴏᴡɴʟᴏᴀᴅ", callback_data=f'down {message.id}') 
                ]
            ])

    if not edit:
        await app.send_message(message.chat.id, text, reply_to_message_id=message.id, reply_markup=keybord)
    else:
        if call:
            await app.edit_message_text(call.message.chat.id,call.message.id, text, reply_markup=keybord)
        else:
            await app.edit_message_text(emsg.chat.id, emsg.reply_to_message.reply_to_message_id, text, reply_markup=keybord)

# handler
async def handlereq(message,link):
    alldata = getinfo(link)

    if alldata.get("size", 0) == 0 or alldata.get("source", None) is None:
        await app.send_message(message.chat.id,f"__Invalid Link : {link}__", reply_to_message_id=message.id)
        return

    store(message,alldata,link)
    formatprint(message.id,link)


# hanldle rename
async def handlereanme(msg,id):
    setlock(msg.from_user.id,None)
    message,alldata,link = get(id)
    alldata['filename'] = msg.text
    store(message,alldata,link)
    formatprint(id,"",True,None,msg)
    await app.delete_messages(msg.chat.id,[msg.id,msg.reply_to_message.id])


# handle thumb
async def handlethumb(msg,id):
    setlock(msg.from_user.id,None)
    formatprint(id,"",True,None,msg)
    await app.delete_messages(msg.chat.id,[msg.id,msg.reply_to_message.id])


# check for memeber present
async def ismemberpresent(id):
    if TARGET == "" or LINK == "": return True
    try:
        await app.get_chat_member(TARGET,id)
        return True
    except: return False
    

# start command
@app.on_message(filters.command(["start"]))
async def echo(bot,message):
    await message.reply_text( f'__Hi {message.from_user.mention}, I am Mdisk Video Downloader, you can watch Downloaded Videos without MX Player.\n\nSend me a link to Start... or click /help to check usage__',reply_to_message_id=message.id,
    reply_markup=InlineKeyboardMarkup([[ InlineKeyboardButton("Sᴏᴜʀᴄᴇ Cᴏᴅᴇ", url="https://t.me/Movie_chamber")]]))


# help command
@app.on_message(filters.command(["help"]))
async def help(bot, message):
    helpmessage = """__**/start** - basic usage
**/help** -
** /download - send mdisk link to download 
**/mdisk mdisklink** - usage
**/thumb** - reply to a image document of size less than 200KB to set it as Thumbnail ( you can also send image as a photo to set it as Thumbnail automatically )
**/remove** - remove Thumbnail
**/show** - show Thumbnail
**/change** - change upload mode ( default mode is Document )__"""
    await message.reply_text( helpmessage, reply_to_message_id=message.id)

"""
# auth command
@app.on_message(filters.command(["auth","unauth"]) &OWNER)
def auth(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    try: userid = str(message.reply_to_message.forward_from.id)
    except:
        try: userid = message.text.split("auth ")[1]
        except:
            app.send_message(message.chat.id, '__Invalid Format, use like this\n/auth 123456 or just reply command to a forwarded message of a user__',reply_to_message_id=message.id)
            return

    if "unauth" in message.text and userid in AUTHUSERS: AUTHUSERS.remove(userid)
    elif "unauth" not in message.text and userid not in AUTHUSERS: AUTHUSERS.append(userid)

    AUTH = " ".join(AUTHUSER)
  

    if "unauth" in message.text: app.send_message(message.chat.id, f'__UnAuth Sucessful for **{userid}**\nuse /members to see the updated list__',reply_to_message_id=message.id)      
    else: app.send_message(message.chat.id, f'__Auth Sucessful for **{userid}**\nuse /members to see the updated list__',reply_to_message_id=message.id)        

# ban command
@app.on_message(filters.command(["ban","unban"]))
async def ban(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    user_id=message.from_user.id
    if user_id not in AUTHUSER:
        return await message.reply_text(f" ʜᴇʏ {message.from_user.mention} ɪ ᴀᴍ sᴏʀʀʏ ,ᴅᴜᴇ ᴛᴏ ᴀᴘɪ ʟɪᴍɪᴛᴀᴛɪᴏɴ ᴜ ᴄᴀɴ`ᴛ ᴜsᴇ ᴍᴇ ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ғᴏʀ ᴜɴᴍɪʟᴛᴇᴅ ᴀᴄᴄᴇss ",reply_markup=InlineKeyboardMarkup(X))
    

    try: userid = str(message.reply_to_message.forward_from.id)
    except:
        try: userid = message.text.split("ban ")[1]
        except:
            app.send_message(message.chat.id, '__Invalid Format, use like this\n/ban 123456 or just reply command to a forwarded message of a user__',reply_to_message_id=message.id)
            return

    if "unban" in message.text and userid in BANNEDUSERS: BANNEDUSERS.remove(userid)
    elif "unban" not in message.text and userid not in BANNEDUSERS: BANNEDUSERS.append(userid)

    BAN = " ".join(BANNEDUSERS)
    

    if "unban" in message.text: app.send_message(message.chat.id, f'__UnBan Sucessful for **{userid}**\nuse /members to see the updated list__',reply_to_message_id=message.id)      
    else: app.send_message(message.chat.id, f'__Ban Sucessful for **{userid}**\nuse /members to see the updated list__',reply_to_message_id=message.id)
"""

# members command
@app.on_message(filters.command(["members"]) &OWNER)
def members(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    
    

    owners = app.get_users(OWNER)
    auths = app.get_users(AUTHUSER)
    bans = app.get_users(BANNEDUSERS)

    app.send_message(message.chat.id,
    '**--OWNERS--**\n\n__' + (''.join([f"@{x.username} - `{x.id}`\n" for x in owners]) if len(owners)!= 0 else "__No Owners__") + "__\n" + 
    '**--AUTH USERS--**\n\n__' + (''.join([f"@{x.username} - `{x.id}`\n" for x in auths]) if len(auths)!= 0 else "__No Auth Users__") + "__\n" + 
    '**--BANNED USERS--**\n\n__' + (''.join([f"@{x.username} - `{x.id}`\n" for x in bans]) if len(bans)!= 0 else "__No Banned Users__") + "__",
    reply_to_message_id=message.id)


# callback
@app.on_callback_query()
async def handle(client: pyrogram.client.Client, call: pyrogram.types.CallbackQuery):

    if call.from_user.id != call.message.reply_to_message.from_user.id: return

    if not ismemberpresent(call.from_user.id):
        await app.send_message(call.message.chat.id, '__You are not a member of our Chat\nJoin and Retry__',reply_to_message_id=call.message.id,
        reply_markup=InlineKeyboardMarkup([[ InlineKeyboardButton("Join", url=LINK)]]))
        return

    data = call.data.split()[0]

    if  data == "down":
        downld = threading.Thread(target=lambda:startdown(call),daemon=True)
        downld.start()
    
    elif data == "change":
        swap(str(call.from_user.id))
        formatprint(call.data.split()[-1],"",True,call)

    elif data == "rename":
        id = int(call.data.split()[-1])
        if get(id)[0] is None: app.edit_message_text(call.message.chat.id,call.message.id,"__Expired__")
        else:
            setlock(call.from_user.id,id)
            await app.send_message(call.message.chat.id, f"**{call.from_user.mention}** send me new Filename", reply_to_message_id=call.message.id, reply_markup=ForceReply(selective=True, placeholder="Filename..."))

    elif data == "thumb":
        if os.path.exists(f'{call.from_user.id}-thumb.jpg'):
            os.remove(f'{call.from_user.id}-thumb.jpg')
            formatprint(call.data.split()[-1],"",True,call)
        else:
            id = int(call.data.split()[-1])
            if get(id)[0] is None: app.edit_message_text(call.message.chat.id,call.message.id,"__Expired__")
            else:
                setlock(call.from_user.id,id)
                await app.send_message(call.message.chat.id, f"**{call.from_user.mention}** send a Image", reply_to_message_id=call.message.id, reply_markup=ForceReply(selective=True, placeholder="Image..."))


# start process
def startdown(call):

    msg = call.message
    message,alldata,link = get(call.data.split()[-1])

    if message is None:
        app.edit_message_text(msg.chat.id, msg.id,"__Expired__")
        return

    # checking link and download with progress thread
    app.edit_message_text(msg.chat.id, msg.id, getformatmsg(alldata['filename'],"Downloading",0,alldata['size'],True))
    sta = threading.Thread(target=lambda:status(str(message.id),msg,alldata['size'],alldata['filename']),daemon=True)
    sta.start()

    # checking link and download
    file,check,filename = mdow(alldata,message)

    if file == None:
        app.edit_message_text(msg.chat.id, msg.id,f"__Invalid Link : {link}__")
        return

    # checking if its a link returned
    if check == -1:
        app.edit_message_text(msg.chat.id, msg.id,f"__Can't Download File but here is the Download Link : {alldata['download']} \n\n {alldata['source']}__")
        os.rmdir(str(message.id))
        return

    # merginig
    app.edit_message_text(message.chat.id, msg.id, getformatmsg(filename,"Merging",0,alldata['size'],True))
    file,check,filename = merge(message,file,check,filename)

    # checking size
    size = get_path_size(file)
    if(size > TG_SPLIT_SIZE):
        app.edit_message_text(message.chat.id, msg.id, getformatmsg(filename,"Spliting",0,alldata['size'],True))
        flist = split_file(file,size,file,".", TG_SPLIT_SIZE)
        os.remove(file) 
    else: flist = [file]

    app.edit_message_text(message.chat.id, msg.id, getformatmsg(filename,"Uploading",0,alldata['size'],True))
    i = 1

    # checking thumbline
    if not os.path.exists(f'{message.from_user.id}-thumb.jpg'): thumbfile = None
    else: thumbfile = f'{message.from_user.id}-thumb.jpg'

    # upload thread
    upsta = threading.Thread(target=lambda:upstatus(f'{message.id}upstatus.txt',msg,alldata['filename']),daemon=True)
    upsta.start()
    info = getdata(str(message.from_user.id))

    # uploading
    for ele in flist:

        # checking file existence
        if not os.path.exists(ele):
            app.send_message(message.chat.id,"__Error in Merging File__",reply_to_message_id=message.id)
            return
            
        # check if it's multi part
        if len(flist) == 1:
            partt = ""
        else:
            partt = f"__**part {i}**__\n"
            i = i + 1

        # actuall upload
        if info == "V":
            thumb,duration,width,height = mediainfo.allinfo(ele,thumbfile)
            if not isPremmium : app.send_video(message.chat.id, video=ele, caption=f"{partt}**{filename}**", thumb=thumb, duration=duration, height=height, width=width, reply_to_message_id=message.id, progress=progress, progress_args=[message])
            else:
                with acc: tmsg = acc.send_video(temp_channel, video=ele, caption=f"{partt}**{filename}**", thumb=thumb, duration=duration, height=height, width=width, progress=progress, progress_args=[message])
                app.copy_message(message.chat.id, temp_channel, tmsg.id, reply_to_message_id=message.id)
            if "-thumb.jpg" not in thumb: os.remove(thumb)
        else:
            if not isPremmium : app.send_document(message.chat.id, document=ele, caption=f"{partt}**{filename}**", thumb=thumbfile, force_document=True, reply_to_message_id=message.id, progress=progress, progress_args=[message])
            else:
                with acc: tmsg = acc.send_document(temp_channel, document=ele, thumb=thumbfile, caption=f"{partt}**{filename}**", force_document=True, progress=progress, progress_args=[message])
                app.copy_message(message.chat.id, temp_channel, tmsg.id, reply_to_message_id=message.id)
       
        # deleting uploaded file
        os.remove(ele)
        
    # checking if restriction is removed    
    if check == 0:
        app.send_message(message.chat.id,"__Can't remove the **restriction**, you have to use **MX player** to play this **video**\n\nThis happens because either the **file** length is **too small** or **video** doesn't have separate **audio layer**__",reply_to_message_id=message.id)
    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
    app.delete_messages(message.chat.id,message_ids=[msg.id])


# mdisk command
@app.on_message(filters.command(["mdisk"]))
async def mdiskdown(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    user_id=message.from_user.id
    if user_id not in AUTHUSER:
        return await message.reply_text(f" ʜᴇʏ {message.from_user.mention} ɪ ᴀᴍ sᴏʀʀʏ ,ᴅᴜᴇ ᴛᴏ ᴀᴘɪ ʟɪᴍɪᴛᴀᴛɪᴏɴ ᴜ ᴄᴀɴ`ᴛ ᴜsᴇ ᴍᴇ ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ғᴏʀ ᴜɴᴍɪʟᴛᴇᴅ ᴀᴄᴄᴇss  Contact @DamnDevansh")
    

    if not ismemberpresent(message.from_user.id):
        await app.send_message(message.chat.id, '__You are not a member of our Chat\nJoin and Retry__',reply_to_message_id=message.id,
        reply_markup=InlineKeyboardMarkup([[ InlineKeyboardButton("Join", url=LINK)]]))
        return

    try: link = message.reply_to_message.text
    except:
        try: link = message.text.split("mdisk ")[1]
        except:
            await app.send_message(message.chat.id, '__Invalid Format, use like this\n/mdisk https://mdisk.me/xxxxx\nor just send a link without command__',reply_to_message_id=message.id)
            return

    if "https://mdisk.me/" in link: handlereq(message,link)
    else: await app.send_message(message.chat.id, '__Send only MDisk Link with command followed by the link__',reply_to_message_id=message.id)


# thumb command
@app.on_message(filters.command(["thumb"]))
async def thumb(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    
    user_id=message.from_user.id
    if user_id not in AUTHUSER:
        return await message.reply_text(f" ʜᴇʏ {message.from_user.mention} ɪ ᴀᴍ sᴏʀʀʏ ,ᴅᴜᴇ ᴛᴏ ᴀᴘɪ ʟɪᴍɪᴛᴀᴛɪᴏɴ ᴜ ᴄᴀɴ`ᴛ ᴜsᴇ ᴍᴇ ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ғᴏʀ ᴜɴᴍɪʟᴛᴇᴅ ᴀᴄᴄᴇss ",reply_markup=InlineKeyboardMarkup(X))
    

    try:
        if int(message.reply_to_message.document.file_size) > 200000:
            await app.send_message(message.chat.id, '__Thumbline size allowed is < 200 KB__',reply_to_message_id=message.id)
            return

        msg = await app.get_messages(message.chat.id, int(message.reply_to_message.id))
        file =await app.download_media(msg)
        os.rename(file,f'{message.from_user.id}-thumb.jpg')
        await app.send_message(message.chat.id, '__Thumbnail is Set__',reply_to_message_id=message.id)

    except:
        await app.send_message(message.chat.id, '__reply /thumb to a image document of size less than 200KB__',reply_to_message_id=message.id)


# show thumb command
@app.on_message(filters.command(["show"]))
async def showthumb(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    
    user_id=message.from_user.id
    if user_id not in AUTHUSER:
        return await message.reply_text(f" ʜᴇʏ {message.from_user.mention} ɪ ᴀᴍ sᴏʀʀʏ ,ᴅᴜᴇ ᴛᴏ ᴀᴘɪ ʟɪᴍɪᴛᴀᴛɪᴏɴ ᴜ ᴄᴀɴ`ᴛ ᴜsᴇ ᴍᴇ ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ғᴏʀ ᴜɴᴍɪʟᴛᴇᴅ ᴀᴄᴄᴇss ",reply_markup=InlineKeyboardMarkup(X))
    
    
    if os.path.exists(f'{message.from_user.id}-thumb.jpg'):
        await app.send_photo(message.chat.id,photo=f'{message.from_user.id}-thumb.jpg',reply_to_message_id=message.id)
    else:
        await app.send_message(message.chat.id, '__Thumbnail is not Set__',reply_to_message_id=message.id)


# remove thumbline command
@app.on_message(filters.command(["remove"]))
async def removethumb(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    
    user_id=message.from_user.id
    if user_id not in AUTHUSER:
        return await message.reply_text(f" ʜᴇʏ {message.from_user.mention} ɪ ᴀᴍ sᴏʀʀʏ ,You have to pay for it contact  in support chat @Devil_Bots_Support" )
        
    
    if os.path.exists(f'{message.from_user.id}-thumb.jpg'):
        os.remove(f'{message.from_user.id}-thumb.jpg')
        await app.send_message(message.chat.id, '__Thumbnail is Removed__',reply_to_message_id=message.id)
    else:
        await app.send_message(message.chat.id, '__Thumbnail is not Set__',reply_to_message_id=message.id)


# thumbline
@app.on_message(filters.photo)
async def ptumb(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    
    user_id=message.from_user.id
    if user_id not in AUTHUSER:
        return await message.reply_text(f" ʜᴇʏ {message.from_user.mention} ɪ ᴀᴍ sᴏʀʀʏ ,ᴅᴜᴇ ᴛᴏ ᴀᴘɪ ʟɪᴍɪᴛᴀᴛɪᴏɴ ᴜ ᴄᴀɴ`ᴛ ᴜsᴇ ᴍᴇ ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ғᴏʀ ᴜɴᴍɪʟᴛᴇᴅ ᴀᴄᴄᴇss ",reply_markup=InlineKeyboardMarkup(X))
    
    
    file = await app.download_media(message)
    os.rename(file,f'{message.from_user.id}-thumb.jpg')

    id = getlock(message.from_user.id)
    if id: handlethumb(message,id)
    else:await app.send_message(message.chat.id, '__Thumbnail is Set__',reply_to_message_id=message.id)
    

# change mode
@app.on_message(filters.command(["change"]))
async def change(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    
    user_id=message.from_user.id
    if user_id not in AUTH:
        return await message.reply_text(f" ʜᴇʏ {message.from_user.mention} ɪ ᴀᴍ sᴏʀʀʏ ,You have to pay for it contact  in support chat @Devil_Bots_Support" )
        
    
    info = getdata(str(message.from_user.id))
    swap(str(message.from_user.id))
    if info == "V":
        await app.send_message(message.chat.id, '__Mode changed from **Video** format to **Document** format__',reply_to_message_id=message.id)
    else:
        await app.send_message(message.chat.id, '__Mode changed from **Document** format to **Video** format__',reply_to_message_id=message.id)
    

# mdisk link in text
@app.on_message(filters.command("download"))
async def mdisktext(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    
    if isPremmium and message.chat.id == temp_channel: return

    user_id=message.from_user.id
    if user_id not in AUTHUSER:
        return await message.reply_text(f" ʜᴇʏ {message.from_user.mention} ɪ ᴀᴍ sᴏʀʀʏ ,You have to pay for it contact  in support chat @Devil_Bots_Support" )
        
    if not ismemberpresent(message.from_user.id):
        await app.send_message(message.chat.id, '__You are not a member of our Chat\nJoin and Retry__',reply_to_message_id=message.id,
        reply_markup=InlineKeyboardMarkup([[ InlineKeyboardButton("Join", url=LINK)]]))
        return

  #  if message.text[0] == "/":
  #      await app.send_message(message.chat.id, '__see /help__',reply_to_message_id=message.id)
  #      return

    id = getlock(message.from_user.id)
    if id:
        handlereanme(message,id)
        return

    if "https://mdisk.me/" in message.text:
        links = message.text.split(' ',1)[1]
        handlereq(message,links)
    else:
        await app.send_message(message.chat.id, '__Send only MDisk Link__ \n **Usage**/download Mdisk link',reply_to_message_id=message.id)


# polling
app.run()
