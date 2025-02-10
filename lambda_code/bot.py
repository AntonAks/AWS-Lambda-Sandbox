import requests


def send_telegram_message(bot_token: str, chat_id_list: list[str], message: str) -> None:
    """
    Send a message to a Telegram chat using a bot.

    :param bot_token: Your bot's token
    :param chat_id_list: The chat IDs of the recipients (comma separated)
    :param message: The message to send
    :return: True if the message was sent successfully, False otherwise
    """
    # Telegram API endpoint for sending messages
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Payload for the POST request
    try:
        # Send the POST request
        for char_id in chat_id_list:
            payload = {
                "chat_id": char_id,
                "text": message
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Check if the message was sent successfully
            if response.status_code == 200:
                print(f"Message sent successfully! CHAT ID: {char_id}")
            else:
                print(f"Failed to send message. Status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")
