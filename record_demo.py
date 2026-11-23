"""
Script to record a high-definition demo video of the full booking flow:
1. Opens Dashboard at http://localhost:8000
2. Launches Voice Assistant ("Try Call")
3. Checks Dr. Sarah Jenkins' availability
4. Selects 10:30 AM slot
5. Provides phone number 9876543210
6. Agent reads back phone number to confirm
7. User confirms number
8. In-phone booking card appears with appointment details
9. Ends call and highlights new row in Live Appointments Record table
10. Saves recorded video to demo_video.mp4
"""

import asyncio
import os
import shutil
import subprocess
from playwright.async_api import async_playwright

async def record():
    os.makedirs("demo_recording", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]
        )

        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir="demo_recording/",
            record_video_size={"width": 1440, "height": 900}
        )

        page = await context.new_page()

        print("1. Navigating to Dashboard...")
        await page.goto("http://localhost:8000", wait_until="networkidle")
        await asyncio.sleep(2.5)

        print("2. Starting Voice Call...")
        # Click "Try Call" button in header
        await page.click('button:has-text("Try Call")')
        # Wait for telephone ring & connect
        await asyncio.sleep(3.5)

        print("3. Asking for Dr. Jenkins availability...")
        # Click shortcut "🩺 Check Dr. Jenkins"
        await page.click('button:has-text("Check Dr. Jenkins")')
        await asyncio.sleep(3.0)

        print("4. Selecting 10:30 AM slot...")
        # Click shortcut "📅 Book 10:30 AM"
        await page.click('button:has-text("Book 10:30 AM")')
        await asyncio.sleep(3.0)

        print("5. Speaking phone number...")
        # Click shortcut "📱 Give Phone Number"
        await page.click('button:has-text("Give Phone Number")')
        # Wait for agent to read back phone number to confirm
        await asyncio.sleep(3.5)

        print("6. Confirming phone number...")
        # Click "✅ Confirm Number"
        await page.click('button:has-text("Confirm Number")')
        # Wait for in-phone confirmation card to appear
        await asyncio.sleep(4.5)

        print("7. Hanging up call...")
        # Click red end call button (has title "End Call")
        try:
            await page.click('button[title="End Call"]')
        except Exception:
            pass
        await asyncio.sleep(2.0)

        print("8. Viewing updated dashboard...")
        # Close phone modal to show table
        try:
            await page.click('button[title="Minimize Phone"]')
        except Exception:
            pass
        await asyncio.sleep(1.0)

        # Scroll to Live Appointments Record
        await page.evaluate("window.scrollBy({ top: 500, behavior: 'smooth' })")
        await asyncio.sleep(4.0)

        print("9. Finishing recording...")
        await context.close()
        await browser.close()

    # Find the recorded video file
    video_files = [os.path.join("demo_recording", f) for f in os.listdir("demo_recording") if f.endswith(".webm")]
    if video_files:
        src_video = video_files[0]
        output_mp4 = "demo_video.mp4"
        print(f"Converting {src_video} to {output_mp4} using ffmpeg...")

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", src_video,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "22",
            "-preset", "fast",
            output_mp4
        ]
        try:
            subprocess.run(ffmpeg_cmd, check=True)
            print(f">> SUCCESS: {output_mp4} created successfully!")
        except Exception as e:
            # Fallback copy if ffmpeg fails
            shutil.copy(src_video, "demo_video.webm")
            print(f"Saved as demo_video.webm: {e}")

if __name__ == "__main__":
    asyncio.run(record())
