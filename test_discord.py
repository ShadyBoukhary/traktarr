#!/usr/bin/env python3
"""
Test script for Discord notifications.

To test Discord notifications:
1. Create a Discord webhook in your server:
   - Go to your Discord server settings
   - Navigate to Integrations → Webhooks
   - Click "New Webhook"
   - Copy the webhook URL

2. Run this script with your webhook URL:
   python test_discord.py "YOUR_WEBHOOK_URL_HERE"

3. Check your Discord channel for the test message.
"""

import sys
from notifications.discord import Discord

def test_discord_notification(webhook_url):
    """Test Discord notification with the provided webhook URL."""
    print("Testing Discord notification...")
    
    # Create Discord notification instance
    discord = Discord(
        webhook_url=webhook_url,
        username="Traktarr Test",
        avatar_url="https://github.com/l3uddz/traktarr/raw/master/assets/logo.svg"
    )
    
    # Send test message
    result = discord.send(message="🎬 **Traktarr Discord Test**\n\nThis is a test message from Traktarr to verify Discord notifications are working correctly!\n\n✅ If you see this message, Discord notifications are properly configured.")
    
    if result:
        print("✅ Discord notification sent successfully!")
        print("Check your Discord channel for the test message.")
    else:
        print("❌ Failed to send Discord notification.")
        print("Please check your webhook URL and try again.")
    
    return result

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_discord.py <discord_webhook_url>")
        print("\nTo get a Discord webhook URL:")
        print("1. Go to your Discord server settings")
        print("2. Navigate to Integrations → Webhooks") 
        print("3. Click 'New Webhook'")
        print("4. Copy the webhook URL")
        sys.exit(1)
    
    webhook_url = sys.argv[1]
    
    if not (webhook_url.startswith("https://discord.com/api/webhooks/") or webhook_url.startswith("https://discordapp.com/api/webhooks/")):
        print("❌ Invalid Discord webhook URL format.")
        print("Expected format: https://discord.com/api/webhooks/... or https://discordapp.com/api/webhooks/...")
        sys.exit(1)
    
    test_discord_notification(webhook_url)
