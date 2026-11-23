"""
Full Feature Video Recorder for Voice AI Doctor Appointment Assistant.
Records a 2-minute comprehensive demo covering all app features and syncs
with the full high-definition audio soundtrack (full_soundtrack.wav).
"""

import asyncio
import os
import json
import subprocess
import time
from playwright.async_api import async_playwright

async def run_feature_recording():
    os.makedirs("demo_full_recording", exist_ok=True)

    with open("audio_markers.json", "r") as f:
        markers = json.load(f)

    start_time = None

    async def wait_until_target(target_sec):
        nonlocal start_time
        elapsed = time.time() - start_time
        remaining = target_sec - elapsed
        if remaining > 0:
            await asyncio.sleep(remaining)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]
        )

        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir="demo_full_recording/",
            record_video_size={"width": 1440, "height": 900}
        )

        page = await context.new_page()

        print(">> Loading Dashboard at http://localhost:8000...")
        await page.goto("http://localhost:8000", wait_until="networkidle")

        start_time = time.time()

        # 0s - 4s: Showcase full dashboard features
        print(">> Feature showcase: Filtering specialties...")
        await page.get_by_role("button", name="Cardiology", exact=True).click()
        await asyncio.sleep(1.2)
        await page.get_by_role("button", name="Dermatology", exact=True).click()
        await asyncio.sleep(1.2)
        await page.get_by_role("button", name="All", exact=True).click()
        await asyncio.sleep(0.8)

        # 4.0s: Launch Voice Call (Try Call)
        await wait_until_target(4.0)
        print(">> Clicking 'Try Call' to open phone modal...")
        await page.click('button:has-text("Try Call")')

        # 8.65s: Receptionist starts greeting (ai_1)
        await wait_until_target(markers["ai_1"])
        print(">> AI Greeting playing...")

        # 22.02s: Caller checks Dr. Jenkins availability (caller_1)
        await wait_until_target(markers["caller_1"])
        print(">> Caller: Check Dr. Jenkins availability...")
        await page.click('button:has-text("Check Dr. Jenkins")')

        # 26.18s: AI replies with slots (ai_2)
        await wait_until_target(markers["ai_2"])
        print(">> AI: Offering available slots...")

        # 37.08s: Caller chooses 10:30 AM (caller_2)
        await wait_until_target(markers["caller_2"])
        print(">> Caller: Book 10:30 AM...")
        await page.click('button:has-text("Book 10:30 AM")')

        # 41.45s: AI asks for phone number (ai_3)
        await wait_until_target(markers["ai_3"])
        print(">> AI: Asking for phone number...")

        # 49.62s: Caller speaks phone number (caller_3)
        await wait_until_target(markers["caller_3"])
        print(">> Caller: My phone number is 9876543210...")
        await page.click('button:has-text("Give Phone Number")')

        # 55.03s: AI reads back phone number to confirm (ai_4)
        await wait_until_target(markers["ai_4"])
        print(">> AI: Reading back phone number for confirmation rule...")

        # 63.86s: Caller confirms number (caller_4)
        await wait_until_target(markers["caller_4"])
        print(">> Caller: Yes, that is correct...")
        await page.click('button:has-text("Confirm Number")')

        # 67.11s: AI confirms booking (ai_5) - In-Phone Card visible
        await wait_until_target(markers["ai_5"])
        print(">> AI: Booking confirmed! In-phone card appears...")

        # 81.71s: Caller initiates cancellation (caller_5)
        await wait_until_target(markers["caller_5"])
        print(">> Caller: Cancel appointment...")
        await page.click('button:has-text("Cancel Appointment")')

        # 86.63s: AI asks for phone number (ai_6)
        await wait_until_target(markers["ai_6"])
        print(">> AI: Asking for cancellation phone number...")

        # 93.81s: Caller provides phone number (caller_6)
        await wait_until_target(markers["caller_6"])
        print(">> Caller: It is 9876543210...")
        await page.click('button:has-text("Give Phone Number")')

        # 98.69s: AI confirms phone number for cancellation (ai_7)
        await wait_until_target(markers["ai_7"])
        print(">> AI: Reading back phone number before cancellation...")

        # 108.73s: Caller confirms cancellation (caller_7)
        await wait_until_target(markers["caller_7"])
        print(">> Caller: Yes, please cancel it...")
        await page.click('button:has-text("Confirm Number")')

        # 111.98s: AI confirms cancellation (ai_8)
        await wait_until_target(markers["ai_8"])
        print(">> AI: Appointment cancelled successfully...")

        # 118.41s: Caller says goodbye (caller_8)
        await wait_until_target(markers["caller_8"])
        print(">> Caller: Goodbye...")

        # 124.16s: AI says farewell (ai_9)
        await wait_until_target(markers["ai_9"])
        print(">> AI: Farewell...")

        # 127.5s: Hang up call
        await wait_until_target(127.5)
        print(">> Hanging up call...")
        try:
            await page.click('button[title="End Call"]')
        except Exception:
            pass
        await asyncio.sleep(1.0)

        # 129.0s: Minimize phone modal to show live dashboard updates
        print(">> Minimizing phone to showcase live dashboard updates...")
        try:
            await page.click('button[title="Minimize Phone"]')
        except Exception:
            pass
        await asyncio.sleep(0.5)

        # Smooth scroll down to Live Appointments Record
        await page.evaluate("window.scrollBy({ top: 480, behavior: 'smooth' })")
        await wait_until_target(134.5)

        print(">> Closing recording context...")
        await context.close()
        await browser.close()

    # Find recorded webm
    recorded_webms = [
        os.path.join("demo_full_recording", f)
        for f in os.listdir("demo_full_recording") if f.endswith(".webm")
    ]
    if not recorded_webms:
        print("Error: No recorded webm found!")
        return

    raw_video = max(recorded_webms, key=os.path.getmtime)
    output_mp4 = "demo_video.mp4"
    audio_wav = "full_soundtrack.wav"

    print(f">> Muxing video ({raw_video}) and audio ({audio_wav}) into {output_mp4} with ffmpeg...")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", raw_video,
        "-i", audio_wav,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "medium",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_mp4
    ]

    subprocess.run(ffmpeg_cmd, check=True)
    print(f">> SUCCESS! High-Definition Video with Full Spoken Audio generated at: {output_mp4}")

if __name__ == "__main__":
    asyncio.run(run_feature_recording())
