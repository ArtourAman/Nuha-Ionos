import os
from time import time
from pyrogram import enums
from collections import defaultdict
from pyrogram.types import InputMediaPhoto, InputMediaVideo

# Maximum file size limit to 2GB
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # If your telegram account is premium then use 4GB

def chkFileSize(file_size):
    return file_size <= MAX_FILE_SIZE

async def fileSizeLimit(file_size, message, action_type="download"):
    if not chkFileSize(file_size):
        await message.reply(f"The file size exceeds the {MAX_FILE_SIZE / (1024 * 1024 * 1024):.2f}GB limit and cannot be {action_type}ed.")
        return False
    return True

priority = {
    enums.MessageEntityType.BOLD: 1,
    enums.MessageEntityType.ITALIC: 2,
    enums.MessageEntityType.UNDERLINE: 3,
    enums.MessageEntityType.STRIKETHROUGH: 4,
    enums.MessageEntityType.SPOILER: 5,
    enums.MessageEntityType.CODE: 6,
    enums.MessageEntityType.PRE: 7,
    enums.MessageEntityType.TEXT_LINK: 8,
    enums.MessageEntityType.HASHTAG: 9
}

default_priority = 100

async def get_parsed_msg(message_text, entities):
    if not entities:
        return message_text

    entity_dict = defaultdict(list)
    for entity in entities:
        start = entity.offset
        end = entity.offset + entity.length
        entity_dict[(start, end)].append(entity)

    last_end = 0
    result = []
    for (start, end), entities in sorted(entity_dict.items()):
        if start > last_end:
            result.append(message_text[last_end:start])
        formatted_text = message_text[start:end]
        entities.sort(key=lambda x: priority.get(x.type, default_priority), reverse=True)
        for entity in entities:
            if entity.type == enums.MessageEntityType.BOLD:
                formatted_text = f"**{formatted_text}**"
            elif entity.type == enums.MessageEntityType.ITALIC:
                formatted_text = f"__{formatted_text}__"
            elif entity.type == enums.MessageEntityType.UNDERLINE:
                formatted_text = f"--{formatted_text}--"
            elif entity.type == enums.MessageEntityType.STRIKETHROUGH:
                formatted_text = f"~~{formatted_text}~~"
            elif entity.type == enums.MessageEntityType.SPOILER:
                formatted_text = f"||{formatted_text}||"
            elif entity.type == enums.MessageEntityType.CODE:
                formatted_text = f"`{formatted_text}`"
            elif entity.type == enums.MessageEntityType.PRE:
                formatted_text = f"```{formatted_text}```"
            elif entity.type == enums.MessageEntityType.TEXT_LINK:
                formatted_text = f"[{formatted_text}]({entity.url})"
            elif entity.type == enums.MessageEntityType.HASHTAG:
                formatted_text = f"{formatted_text}"

        result.append(formatted_text)
        last_end = end

    if last_end < len(message_text):
        result.append(message_text[last_end:])

    return "".join(result)


# Progress bar template
PROGRESS_BAR = """
Percentage: {percentage:.2f}% | {current}/{total}
Speed: {speed}/s
Estimated Time Left: {est_time} seconds
"""

def progressArgs(action: str, progress_message, start_time):
    return (
        action,
        progress_message,
        start_time,
        PROGRESS_BAR,
        '▓',
        '░'
    )

# Function to extract chat ID and message ID from URL
def getChatMsgID(url: str):
    parts = url.split("/")
    chat_id = int("-100" + parts[-2])
    message_id = int(parts[-1])
    return chat_id, message_id
    
    
# Generate progress bar for downloading/uploading
def progressArgs(action: str, progress_message, start_time):
    return (
        action,
        progress_message,
        start_time,
        PROGRESS_BAR,
        '▓',
        '░'
    )

async def send_media(client, event, media_path, media_type, caption, progress_message, start_time):
    file_size = os.path.getsize(media_path)
    
    if not await fileSizeLimit(file_size, event):
        return

    try:
        if media_type == "video":
            await client.send_file(
                event.chat_id,
                media_path,
                caption=caption,
                progress_callback=lambda d, t: print(f"Uploaded: {d}/{t} bytes")
            )
        elif media_type == "document":
            await client.send_file(
                event.chat_id,
                media_path,
                force_document=True,
                caption=caption,
                progress_callback=lambda d, t: print(f"Uploaded: {d}/{t} bytes")
            )
    except Exception as e:
        await event.reply(f"Upload error: {str(e)}")

async def processMediaGroup(client, chat_id, message_id, target_chat_id):
    messages = await client.get_messages(chat_id, ids=[message_id])
    if messages and messages[0].grouped_id:
        grouped_messages = await client.get_messages(
            chat_id,
            ids=range(message_id-10, message_id+10)
        )
        media_group = [m for m in grouped_messages if m.grouped_id == messages[0].grouped_id]
        
        media = []
        for msg in media_group:
            if msg.photo or msg.video:
                media.append(await msg.download_media())
        
        if media:
            await client.send_file(target_chat_id, media)
            return True
    return False
