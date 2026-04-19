#!/usr/bin/env python3
"""Apply Storyworld migrations via Supabase."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import asyncio
from supabase import acreate_client

SQL = (Path(__file__).parent / "001_initial.sql").read_text()

async def main():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    client = await acreate_client(url, key)

    # Try to create buckets
    for bucket_id, public in [("photos", True), ("story-images", True)]:
        try:
            await client.storage.create_bucket(bucket_id, options={"public": public})
            print(f"Created bucket: {bucket_id}")
        except Exception as e:
            msg = str(e)
            if "already exists" in msg.lower() or "duplicate" in msg.lower():
                print(f"Bucket already exists: {bucket_id}")
            else:
                print(f"Bucket {bucket_id} error: {msg}")

    # Try inserting a test row to see if stories table exists
    test_story = {
        "id": "__schema_check__",
        "status": "complete",
        "story_json": '{"test": true}'
    }
    try:
        await client.table("stories").insert(test_story).execute()
        # Clean up test row
        await client.table("stories").delete().eq("id", "__schema_check__").execute()
        print("Table 'stories' already exists and is writable")
    except Exception as e:
        msg = str(e)
        if "does not exist" in msg or "relation" in msg.lower():
            print("Table 'stories' does not exist — needs manual SQL execution")
            print("\nRun this SQL in the Supabase dashboard SQL editor:")
            print(SQL)
        else:
            print(f"Stories table error: {msg}")

asyncio.run(main())
