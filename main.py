from telethon import TelegramClient, events
from telethon.sessions import StringSession
from helpers.utils import (
    processMediaGroup,
    get_parsed_msg,
    fileSizeLimit,
    getChatMsgID,
    send_media,
    PROGRESS_BAR
)
from helpers.forward import forward_videos, forward_from_handler
from config import (
    API_ID, API_HASH, SESSION_STRING,
    SOURCE_CHANNEL, TARGET_CHANNEL,
    FORWARD_DELAY_MIN, FORWARD_DELAY_MAX,
    BATCH_SIZE, BATCH_BREAK_MIN, BATCH_BREAK_MAX,  # Add these imports
    DAILY_SLEEP_HOURS, DAILY_BREAK_HOURS
)
import os
from time import time
import asyncio
import random
import time

# Initialize client with StringSession
client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID, 
    API_HASH
)

print("Starting with user session string...")
print("=====================================")
print(f"Source Channel: {SOURCE_CHANNEL}")
print(f"Target Channel: {TARGET_CHANNEL}")
print("=====================================")

# Fix command patterns to be more precise with Telethon syntax
@events.register(events.NewMessage(pattern=r'/start$'))
async def start_cmd(event):
    help_text = """**📥 Channel Manager**
    
Commands:
• `/addsource` - Add source channel (Example: /addsource @channel or -100xxx)
• `/addtarget` - Add target channel
• `/forward` - Forward from source channel
• `/pause` - Pause source channel
• `/resume` - Resume source channel
• `/status` - Show all channels status"""
    await event.reply(help_text)

@events.register(events.NewMessage(pattern='/dl'))
async def download_media(event):
    if len(event.raw_text.split()) < 2:
        await event.reply("Please provide a post URL after the /dl command.")
        return

    post_url = event.raw_text.split()[1]
    try:
        chat_id, message_id = getChatMsgID(post_url)
        message = await client.get_messages(chat_id, ids=message_id)

        # Handle media message
        if message.media:
            progress_message = await event.reply("Starting download...")
            start_time = time()

            if hasattr(message.media, 'document'):
                file_size = message.media.document.size
                if not await fileSizeLimit(file_size, event):
                    return

            # Download media
            media_path = await message.download_media(
                progress_callback=lambda d, t: print(f"Downloaded: {d}/{t} bytes")
            )

            # Send media
            await send_media(
                client,
                event,
                media_path,
                "video" if message.video else "document",
                message.text,
                progress_message,
                start_time
            )

            # Cleanup
            os.remove(media_path)
            await progress_message.delete()

    except Exception as e:
        await event.reply(f"Error: {str(e)}")

# Fix the forward command handler
@events.register(events.NewMessage(pattern=r'/(?:forward|foward)(?:\s+(.*))?'))
async def forward_handler(event):
    try:
        channel_input = event.pattern_match.group(1) if event.pattern_match else None
        if not channel_input and len(event.raw_text.split()) > 1:
            channel_input = event.raw_text.split(maxsplit=1)[1]
            
        if not channel_input:
            await event.reply("Please provide channel ID\nExample: /forward -100xxxxxxxxxxxx")
            return

        status_msg = await event.reply(f"🔍 Looking for channel: {channel_input}")
        
        try:
            # Handle channel ID format
            if channel_input.startswith('-100'):
                chat = await client.get_input_entity(int(channel_input))
            else:
                chat = await client.get_input_entity(channel_input)

            # Use the forward_videos function from forward.py
            await forward_videos(client, chat, TARGET_CHANNEL, status_msg)

        except Exception as e:
            await status_msg.edit(f"❌ Error: {str(e)}\nMake sure you are a member of the channel.")
            print(f"Channel error: {str(e)}")

    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        print(f"Command error: {str(e)}")

@events.register(events.NewMessage(pattern=r'/pause(?:\s+(.*))?$'))
async def pause_handler(event):
    try:
        channel_input = event.pattern_match.group(1)
        if not channel_input:
            await event.reply("Please provide channel name/username/ID")
            return
            
        chat = await client.get_entity(channel_input)
        await event.reply(f"✅ Paused forwarding from {chat.title}")
    except Exception as e:
        await event.reply(f"Error: {str(e)}")

@events.register(events.NewMessage(pattern=r'/resume(?:\s+(.*))?$'))
async def resume_handler(event):
    try:
        channel_input = event.pattern_match.group(1)
        if not channel_input:
            await event.reply("Please provide channel name/username/ID")
            return
            
        chat = await client.get_entity(channel_input)
        await event.reply(f"✅ Resumed forwarding from {chat.title}")
    except Exception as e:
        await event.reply(f"Error: {str(e)}")

# Update the status handler to show active/paused state
@events.register(events.NewMessage(pattern=r'/status$'))
async def status_handler(event):
    try:
        status = "📊 Channel Status:\n\n"
        
        status += "📥 Source Channels:\n"
        for channel_id in SOURCE_CHANNEL:
            chat = await client.get_entity(channel_id)
            status += f"- {chat.title}\n"
        
        status += "\n📤 Target Channels:\n"
        for channel_id in TARGET_CHANNEL:
            chat = await client.get_entity(channel_id)
            status += f"- {chat.title}\n"
                
        await event.reply(status)
    except Exception as e:
        await event.reply(f"Error: {str(e)}")

@events.register(events.NewMessage(pattern='/addtarget'))
async def add_target_handler(event):
    try:
        args = event.raw_text.split()
        if len(args) < 2:
            await event.reply("Please provide channel ID or username\nExample: /addtarget @channelname or -100xxx")
            return
            
        channel_input = args[1]
        try:
            # Handle channel ID format
            if channel_input.startswith('-100'):
                # Remove -100 prefix if present
                channel_id = int(channel_input.replace('-100', ''))
                channel = await client.get_entity(int(f"-100{channel_id}"))
            else:
                # Handle username or other format
                channel = await client.get_entity(channel_input)
                
        except ValueError:
            await event.reply("❌ Invalid channel ID format. Try using the channel username instead.")
            return
        except Exception as e:
            await event.reply(f"❌ Could not find channel. Error: {str(e)}\n\nMake sure:\n1. You are a member of the channel\n2. The channel ID/username is correct")
            return
            
        await event.reply(f"✅ Added {channel.title} as target channel!")
    except Exception as e:
        await event.reply(f"Error: {str(e)}")

@events.register(events.NewMessage(pattern='/deletesrt'))
async def delete_srt_handler(event):
    try:
        deleted = 0
        
        status_msg = await event.reply("🔍 Scanning for SRT files...")
        
        for target in TARGET_CHANNEL:
            async for msg in client.iter_messages(target):
                if msg.document and msg.document.mime_type == 'text/srt':
                    await msg.delete()
                    deleted += 1
                    if deleted % 10 == 0:
                        await status_msg.edit(f"Deleted {deleted} SRT files...")
                        
        await status_msg.edit(f"✅ Deleted {deleted} SRT files!")
    except Exception as e:
        await event.reply(f"Error: {str(e)}")

# Add this new handler after other event handlers
@events.register(events.NewMessage(pattern='/addsource'))
async def add_source_handler(event):
    try:
        args = event.raw_text.split()
        if len(args) < 2:
            await event.reply("Please provide channel ID or username\nExample: /addsource @channelname or -100xxx")
            return
            
        channel_input = args[1]
        try:
            # Handle channel ID format
            if channel_input.startswith('-100'):
                # Remove -100 prefix if present
                channel_id = int(channel_input.replace('-100', ''))
                channel = await client.get_entity(int(f"-100{channel_id}"))
            else:
                # Handle username or other format
                channel = await client.get_entity(channel_input)
                
        except ValueError:
            await event.reply("❌ Invalid channel ID format. Try using the channel username instead.")
            return
        except Exception as e:
            await event.reply(f"❌ Could not find channel. Error: {str(e)}\n\nMake sure:\n1. You are a member of the channel\n2. The channel ID/username is correct")
            return
            
        await event.reply(f"✅ Added {channel.title} as source channel!")
    except Exception as e:
        await event.reply(f"Error: {str(e)}")

# Message handler for videos
@events.register(events.NewMessage)
async def video_handler(event):
    try:
        if not event.video and not (event.document and event.document.mime_type and 'video' in event.document.mime_type):
            return

        if event.chat_id in SOURCE_CHANNEL:
            print(f"\n=== NEW VIDEO DETECTED ===")
            print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"From channel: {event.chat_id}")
            print(f"Video title: {event.message.file.name if event.message.file else 'Untitled'}")
            
            for target in TARGET_CHANNEL:
                try:
                    print(f"Forwarding to channel: {target}")
                    print(f"Waiting {FORWARD_DELAY_MIN}-{FORWARD_DELAY_MAX} seconds...")
                    
                    delay = random.uniform(FORWARD_DELAY_MIN, FORWARD_DELAY_MAX)
                    await asyncio.sleep(delay)
                    
                    await client.forward_messages(target, event.message)
                    print("✓ Forward successful!")
                    
                except Exception as e:
                    print(f"❌ Forward error: {str(e)}")
    except Exception as e:
        print(f"❌ Video handler error: {str(e)}")

async def initial_forward(client):
    """Forward all existing videos from source to target channel"""
    try:
        print("\n=== STARTING INITIAL FORWARD ===")
        print(f"Scanning source channel: {SOURCE_CHANNEL[0]}")
        
        video_count = 0
        videos = []
        
        # Collect all existing videos
        async for msg in client.iter_messages(SOURCE_CHANNEL[0], reverse=True):
            if msg.video or (msg.document and msg.document.mime_type and 'video' in msg.document.mime_type):
                video_count += 1
                videos.append(msg)
                if video_count % 20 == 0:
                    print(f"[Scan] Found {video_count} videos...")
        
        if not videos:
            print("No existing videos found")
            return
        
        print(f"\nTotal videos found: {video_count}")
        print("Starting forward process...\n")
        
        # Forward videos with delays and breaks
        forwarded = 0
        for msg in videos:
            try:
                if forwarded > 0 and forwarded % BATCH_SIZE == 0:
                    break_time = random.uniform(BATCH_BREAK_MIN, BATCH_BREAK_MAX)
                    print(f"\nTaking a {int(break_time)}s break after {BATCH_SIZE} forwards...")
                    await asyncio.sleep(break_time)
                
                delay = random.uniform(FORWARD_DELAY_MIN, FORWARD_DELAY_MAX)
                await asyncio.sleep(delay)
                
                await client.forward_messages(TARGET_CHANNEL[0], msg)
                forwarded += 1
                
                # Show counter for every forward
                print(f"Forwarded: {forwarded}/{video_count} videos")
                
            except Exception as e:
                print(f"Error forwarding video {forwarded + 1}: {str(e)}")
                continue
        
        print(f"\n=== INITIAL FORWARD COMPLETE ===")
        print(f"Successfully forwarded: {forwarded}/{video_count} videos")
        
    except Exception as e:
        print(f"Initial forward error: {str(e)}")

async def main():
    print("\n=== INITIALIZATION ===")
    print("Starting services...")
    print("✓ Client initialization complete")
    
    # Start the client
    await client.start()
    print("✓ Client connected successfully!")
    
    # Only forward existing videos, don't monitor for new ones
    await initial_forward(client)
    
    print("\n=== FORWARD COMPLETE ===")
    print("Bot will now exit.")
    
    # Exit after forwarding
    await client.disconnect()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())

