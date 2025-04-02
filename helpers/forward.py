from telethon import events
from telethon.tl.types import PeerChannel
from config import (
    SOURCE_CHANNEL, TARGET_CHANNEL,
    FORWARD_DELAY_MIN, FORWARD_DELAY_MAX,
    BATCH_SIZE, BATCH_BREAK_MIN, BATCH_BREAK_MAX
)
import asyncio
import random
from time import time

# Video file extensions list
VIDEO_EXTENSIONS = [
    '.mp4', '.mkv', '.webm', '.ts', '.mov', '.avi', 
    '.flv', '.wmv', '.m4v', '.mpeg', '.mpg', '.3gp', 
    '.3g2', '.vob', '.ogv', '.mts', '.m2ts', '.divx',
    '.xvid', '.rmvb', '.asf'
]

def is_video_file(filename):
    """Check if a file is a video based on its extension"""
    return any(filename.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)

async def forward_videos(client, chat, target_channels, status_msg):
    """Main function to handle video forwarding - oldest to newest"""
    try:
        video_count = 0
        videos = []
        
        # Get proper channel ID
        try:
            channel_id = getattr(chat, 'channel_id', None) or getattr(chat, 'id', None)
            if not channel_id:
                channel = await client.get_entity(chat)
                channel_id = channel.id
            
            print(f"\n=== SCANNING CHANNEL {channel_id} ===")
                
        except Exception as e:
            print(f"Channel ID error: {str(e)}")
            await status_msg.edit("❌ Error: Could not get channel ID")
            return False

        # Collect videos
        await status_msg.edit("🔍 Scanning for videos...")
        print("Starting video scan...")
        
        async for msg in client.iter_messages(channel_id, reverse=True):
            if hasattr(msg.media, 'document'):
                if (msg.video or 
                    (msg.document and 
                     hasattr(msg.document, 'mime_type') and 
                     msg.document.mime_type and 
                     msg.document.mime_type.startswith('video/'))):
                    video_count += 1
                    videos.append(msg)
                    if video_count % 20 == 0:
                        print(f"[Scan] Found {video_count} videos...")
                        await status_msg.edit(f"Found {video_count} videos...")

        if not videos:
            await status_msg.edit("❌ No videos found!")
            return False

        # Forward process
        forwarded = 0
        errors = 0
        
        for msg in videos:
            try:
                target = target_channels[0] if isinstance(target_channels, list) else target_channels
                delay = random.uniform(FORWARD_DELAY_MIN, FORWARD_DELAY_MAX)
                await asyncio.sleep(delay)
                
                await client.forward_messages(target, messages=msg)
                forwarded += 1
                
                if forwarded % BATCH_SIZE == 0:
                    break_time = random.uniform(BATCH_BREAK_MIN, BATCH_BREAK_MAX)
                    await status_msg.edit(f"Taking a {int(break_time)}s break...")
                    await asyncio.sleep(break_time)
                
            except Exception as e:
                print(f"Forward error: {str(e)}")
                errors += 1
                continue

        await status_msg.edit(
            f"✅ Forward completed!\n"
            f"Total: {video_count}\n"
            f"Success: {forwarded}\n"
            f"Failed: {errors}"
        )
        return True

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

async def forward_videos_from_id(client, chat, start_message_id, target_channels, status_msg):
    """Forward videos starting from a specific message ID to newest"""
    try:
        # Get proper channel ID
        try:
            if hasattr(chat, 'channel_id'):
                channel_id = chat.channel_id
            elif hasattr(chat, 'id'):
                channel_id = chat.id
            else:
                channel = await client.get_entity(chat)
                channel_id = channel.id
                
        except Exception as e:
            print(f"Channel ID error: {str(e)}")
            await status_msg.edit("❌ Error: Could not get channel ID")
            return False

        video_count = 0
        videos = []
        
        # First collect all videos from the specified message ID to newest
        await status_msg.edit("🔍 Scanning for videos...")
        async for msg in client.iter_messages(chat, min_id=start_message_id-1):
            if hasattr(msg.media, 'document'):
                if (msg.video or 
                    (msg.document and 
                     hasattr(msg.document, 'mime_type') and 
                     msg.document.mime_type and 
                     msg.document.mime_type.startswith('video/'))):
                    video_count += 1
                    videos.append(msg)
                    if video_count % 10 == 0:
                        await status_msg.edit(f"Found {video_count} videos after message {start_message_id}...")

        if not videos:
            await status_msg.edit("❌ No videos found after this message!")
            return False

        # Sort videos by ID to ensure chronological order
        videos.sort(key=lambda x: x.id)
        
        # Forward settings
        forwarded = 0
        errors = 0
        start_time = time()
        batch_size = 30
        rest_time = 15
        delay = 1.5

        # Forward process
        for msg in videos:
            try:
                if forwarded > 0 and forwarded % batch_size == 0:
                    await status_msg.edit(
                        f"⏸️ Anti-flood pause ({rest_time}s)\n"
                        f"Progress: {(forwarded/video_count)*100:.1f}%\n"
                        f"✅ Done: {forwarded}/{video_count}"
                    )
                    await asyncio.sleep(rest_time)

                for target in target_channels:
                    try:
                        # Forward the message
                        forwarded_msg = await client.forward_messages(
                            target['channel_id'],
                            messages=msg
                        )
                        
                        forwarded += 1
                        
                        if forwarded % 3 == 0:
                            elapsed = time() - start_time
                            speed = forwarded / elapsed if elapsed > 0 else 0
                            eta = ((video_count - forwarded) / speed) if speed > 0 else 0
                            
                            await status_msg.edit(
                                f"📊 {(forwarded/video_count)*100:.1f}%\n"
                                f"✅ {forwarded}/{video_count}\n"
                                f"⏱️ ETA: {int(eta)}s\n"
                                f"📈 {speed:.1f} vid/s"
                            )
                        
                        await asyncio.sleep(delay)
                        
                    except Exception as e:
                        if "420" in str(e):
                            await status_msg.edit(f"⚠️ Hit flood limit, waiting 30s...")
                            await asyncio.sleep(30)
                            delay += 0.5
                        errors += 1
                        continue

            except Exception as e:
                print(f"Error forwarding message: {str(e)}")
                errors += 1
                continue

        # Show final status
        total_time = time() - start_time
        await status_msg.edit(
            f"✅ Forward completed!\n"
            f"📊 Total: {video_count}\n"
            f"✅ Done: {forwarded}\n"
            f"❌ Failed: {errors}\n"
            f"⏱️ Time: {int(total_time)}s"
        )
        return True

    except Exception as e:
        await status_msg.edit(f"❌ Error: {str(e)}")
        print(f"Forward error: {str(e)}")
        return False

async def list_channels(client, message):
    try:
        response = []
        
        response.append("Source channels:")
        response.append(f"- {SOURCE_CHANNEL}")
        
        response.append("\n")
        
        response.append("Target channels:")
        response.append(f"- {TARGET_CHANNEL}")
        
        await message.reply_text("\n".join(response))
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

async def process_video(client, message, target_id):
    """Handle video processing - either forward directly or download and send"""
    try:
        # Try direct forwarding first
        try:
            forwarded_msg = await message.forward(target_id)
            return forwarded_msg
        except Exception as e:
            print(f"Direct forward failed, trying download method: {str(e)}")
            
            # If forwarding fails, download and send
            if not message.video:
                return None
                
            # Check file size
            if not await fileSizeLimit(message.video.file_size, message, "download"):
                return None
                
            # Download video
            progress_message = await message.reply_text("📥 Downloading video...")
            start_time = time()
            
            video_path = f"downloads/{message.video.file_id}.mp4"
            os.makedirs("downloads", exist_ok=True)
            
            await message.download(
                video_path,
                progress=progressArgs("📥 Downloading Progress", progress_message, start_time)
            )
            
            # Send video
            sent_msg = await send_media(
                client,
                message,
                video_path,
                "video",
                message.caption,
                progress_message,
                start_time
            )
            
            # Clean up
            try:
                os.remove(video_path)
                await progress_message.delete()
            except:
                pass
                
            return sent_msg
            
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        return None

async def scan_channels(client, message):
    """Scan user's dialogs and add channels to database"""
    try:
        progress_msg = await message.reply_text("🔍 Scanning your channels...")
        added = []
        
        async for dialog in client.get_dialogs():
            if dialog.chat.type in ["channel", "supergroup"]:
                chat = dialog.chat
                # You can customize this condition to determine source vs target
                is_source = chat.members_count > 1000 if hasattr(chat, 'members_count') else False
                channel_type = "source" if is_source else "target"
                
                try:
                    added.append(f"{chat.title} ({chat.id}) as {channel_type}")
                except Exception as e:
                    print(f"Error adding channel {chat.id}: {str(e)}")
        
        if added:
            await progress_msg.edit_text(f"Added channels:\n" + "\n".join(f"• {x}" for x in added))
        else:
            await progress_msg.edit_text("No new channels found!")
            
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

# Modify the video handler to work with user session
async def forward_video(client, message):
    try:
        if not message.video and not (message.document and message.document.mime_type.startswith('video/')):
            return

        if message.chat_id == SOURCE_CHANNEL:
            target_channels = [TARGET_CHANNEL]
            
            for target in target_channels:
                try:
                    forwarded = await client.forward_messages(
                        target,
                        message
                    )
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"Forward error: {str(e)}")
                    continue

    except Exception as e:
        print(f"Error: {str(e)}")

@events.register(events.NewMessage(pattern="/start|/help"))
async def start_command(event):
    help_text = """**Available Commands:**
    
• /scan - Scan all your channels/groups and add to database
• /addsource [channel_id] - Add source channel
• /addtarget [channel_id] - Add target channel
• /list - Show all channels
    
**Note:** Bot will forward all videos from source to target channels automatically.
You don't need to add the bot to any channel since it uses your account."""
    
    await event.reply(help_text)

@events.register(events.NewMessage(pattern="/scan"))
async def scan_command(event):
    await scan_channels(event.client, event.message)

@events.register(events.NewMessage(pattern="/forward|/foward"))
async def forward_command(event):
    print("\n=== FORWARD COMMAND STARTED ===")
    try:
        args = event.message.text.split(None, 1)
        if len(args) < 2:
            await event.reply("Please provide channel name/username/ID")
            return

        channel_input = args[1].strip()
        status_msg = await event.reply(f"🔍 Looking for channel: {channel_input}")

        try:
            chat = await event.client.get_entity(channel_input)
            await status_msg.edit(f"✅ Found channel: {chat.title}\n⏳ Starting video count...")
            
            video_count = 0
            videos = []
            
            # First collect all videos
            async for msg in event.client.iter_messages(chat.id):
                if msg.video:
                    video_count += 1
                    videos.append(msg)
                    if video_count % 50 == 0:  # Update status every 50 videos
                        await status_msg.edit(f"Found {video_count} videos so far...")

            await status_msg.edit(f"📊 Total videos found: {video_count}\n🚀 Starting forward process...")
            
            # Get target channels
            target_channels = [TARGET_CHANNEL]

            # Forward videos with progress and delays
            forwarded = 0
            batch_size = 100  # Forward 100 videos then rest
            rest_time = 45  # Rest for 45 seconds between batches
            delay = 2  # 2 second delay between each forward

            for i, msg in enumerate(videos):
                if msg.video:
                    # Check if we need to take a rest
                    if forwarded > 0 and forwarded % batch_size == 0:
                        await status_msg.edit(f"⏳ Forwarded {forwarded}/{video_count} videos.\n😴 Taking a {rest_time} second break to avoid flooding...")
                        await asyncio.sleep(rest_time)

                    for target in target_channels:
                        try:
                            await msg.forward_to(
                                target
                            )
                            forwarded += 1
                            
                            # Update progress every 10 videos
                            if forwarded % 10 == 0:
                                progress = (forwarded / video_count) * 100
                                await status_msg.edit(
                                    f"⏳ Progress: {progress:.11f}%\n"
                                    f"✅ Forwarded: {forwarded}/{video_count}\n"
                                    f"⏰ Delay: {delay}s between forwards\n"
                                    f"📦 Batch size: {batch_size} with {rest_time}s rest"
                                )
                            
                            await asyncio.sleep(delay)  # Delay between forwards
                            
                        except Exception as e:
                            print(f"Error forwarding: {str(e)}")
                            continue

            await status_msg.edit(
                f"✅ Forward completed!\n"
                f"📊 Total videos: {video_count}\n"
                f"✅ Successfully forwarded: {forwarded}\n"
                f"❌ Failed: {video_count - forwarded}"
            )

        except Exception as e:
            await status_msg.edit(f"❌ Error: {str(e)}")
            print(f"Forward error: {str(e)}")

    except Exception as e:
        print(f"Command error: {str(e)}")
        await event.reply(f"❌ Error: {str(e)}")
    
    print("=== FORWARD COMMAND ENDED ===\n")

@events.register(events.NewMessage(pattern=r'/forwardfrom\s+https?://t\.me/(?:c/)?(\d+)/(\d+)'))
async def forward_from_handler(event):
    try:
        raw_channel_id, start_message_id = event.pattern_match.groups()
        try:
            # Convert IDs to int
            start_message_id = int(start_message_id)
            channel_id = int(raw_channel_id)  # This is the raw ID from URL
            
            status_msg = await event.reply("🔍 Accessing private channel...")
            
            try:
                # Try direct channel ID first (just add -100 prefix)
                direct_id = int(f"-100{channel_id}")
                try:
                    # Try getting messages using direct ID
                    messages = await event.client.get_messages(direct_id, limit=1)
                    if messages and len(messages) > 0:
                        await status_msg.edit("✅ Channel access verified!")
                        
                        # Get target channels
                        target_channels = [TARGET_CHANNEL]

                        # Start forwarding
                        await forward_videos_from_id(
                            event.client,
                            direct_id,  # Use the direct ID
                            start_message_id,
                            target_channels,
                            status_msg
                        )
                        return

                except Exception as e:
                    print(f"Direct ID failed: {str(e)}")
                    # Continue to next method if this fails

                # If direct ID failed, try with PeerChannel
                peer = PeerChannel(channel_id=direct_id)
                await status_msg.edit("🔄 Trying alternate access method...")
                
                # Verify access
                messages = await event.client.get_messages(peer, limit=1)
                if not messages:
                    await status_msg.edit("❌ Cannot access channel messages")
                    return
                
                # Get target channels
                target_channels = [TARGET_CHANNEL]

                # Forward using peer
                await forward_videos_from_id(
                    event.client,
                    peer,
                    start_message_id,
                    target_channels,
                    status_msg
                )

            except Exception as e:
                await status_msg.edit(
                    f"❌ Error accessing channel:\n{str(e)}\n"
                    f"Channel ID: {channel_id}\n"
                    f"Make sure you are a member of the channel"
                )
                print(f"Channel access error: {str(e)}")

        except ValueError as ve:
            await event.reply(
                "❌ Invalid format. Use:\n"
                "/forwardfrom https://t.me/c/1457047091/21916"
            )
            print(f"Parse error: {str(ve)}")

    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        print(f"Command error: {str(e)}")

@events.register(events.NewMessage(pattern=r'/forwardfrom\s+(-\d+)\s+(\d+)'))
async def forward_from_handler(event):
    try:
        # Extract channel ID and message ID from space-separated format
        channel_input, msg_id = event.text.split()[1:]  # Split into two parts after command
        try:
            # Convert to proper integers
            channel_id = int(channel_input)      # Should be like -1001457047091
            start_message_id = int(msg_id)       # Should be like 21916
            
            status_msg = await event.reply(f"🔍 Accessing channel {channel_id}\nStarting from message: {start_message_id}")
            
            try:
                # Try to get the channel
                chat = await event.client.get_entity(channel_id)
                
                # Verify access
                test_msg = await event.client.get_messages(chat, limit=1)
                if not test_msg:
                    await status_msg.edit("❌ Cannot access channel messages")
                    return

                await status_msg.edit(
                    f"✅ Found channel: {getattr(chat, 'title', str(channel_id))}\n"
                    f"⏳ Starting forward from message {start_message_id}"
                )
                
                # Get target channels
                target_channels = [TARGET_CHANNEL]

                # Start forwarding
                await forward_videos_from_id(
                    event.client,
                    chat,
                    start_message_id,
                    target_channels,
                    status_msg
                )

            except Exception as e:
                await status_msg.edit(
                    f"❌ Error accessing channel:\n{str(e)}\n"
                    f"Channel ID: {channel_id}\n"
                    f"Make sure you are a member of the channel"
                )
                print(f"Channel error: {str(e)}")

        except ValueError as ve:
            await event.reply(
                "❌ Invalid format. Use:\n"
                "/forwardfrom -1001457047091 21916\n"
                "First number is channel ID, second is message ID"
            )
            print(f"Parse error: {str(ve)}")

    except Exception as e:
        await event.reply(
            "❌ Correct format is:\n"
            "/forwardfrom -1001457047091 21916"
        )
        print(f"Command error: {str(e)}")

# Simplified handler for auto-forwarding new videos
async def forward_from_handler(event):
    if event.chat_id in SOURCE_CHANNEL:
        if event.video or (event.document and event.document.mime_type.startswith('video/')):
            target = TARGET_CHANNEL[0]
            try:
                delay = random.uniform(FORWARD_DELAY_MIN, FORWARD_DELAY_MAX)
                await asyncio.sleep(delay)
                await event.forward_to(target)
            except Exception as e:
                print(f"Auto-forward error: {str(e)}")



