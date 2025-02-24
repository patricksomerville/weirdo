import asyncio
import schedule
import time
from datetime import datetime
from video_pipeline import VideoPipeline

async def generate_daily_newsreel():
    """Generate the daily weird news video."""
    print(f"\n=== Starting Daily Newsreel Generation at {datetime.now().isoformat()} ===")
    pipeline = VideoPipeline()
    try:
        output_path = await pipeline.generate_daily_video()
        print(f"Daily newsreel completed successfully. Video saved to: {output_path}")
    except Exception as e:
        print(f"Error generating daily newsreel: {str(e)}")

def run_scheduler():
    """Run the scheduler to generate videos daily."""
    # Schedule the job to run at 6 AM every day
    schedule.every().day.at("06:00").do(lambda: asyncio.run(generate_daily_newsreel()))
    
    # Also run it immediately when starting the scheduler
    asyncio.run(generate_daily_newsreel())
    
    print("\nScheduler is running. Will generate new videos daily at 6 AM.")
    print("Press Ctrl+C to stop.")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nScheduler stopped by user.")
            break
        except Exception as e:
            print(f"Scheduler error: {str(e)}")
            # Wait a bit before retrying
            time.sleep(300)

if __name__ == "__main__":
    run_scheduler()
