import os
import soco
import RPi.GPIO as GPIO
from time import sleep
from soco.snapshot import Snapshot
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
from decouple import config

def send_slack_msg():
    # Send slack msg
    slack_client = WebClient(token=config('SLACK_TOKEN'))
    try:
        response = slack_client.chat_postMessage(channel='#doorbell', text="@all Ring ring!")
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")

def find_speaker(name, iface):
    devices = soco.discover(interface_addr=iface)
    if devices is None:
        return None

    for device in devices:
        if device.player_name == name:
            return device
    return None

def ring(speaker):
    # Take snapshot
    snap = Snapshot(speaker)
    snap.snapshot()

    # Play ring sound
    state = speaker.get_current_transport_info()
    if state['current_transport_state'] == 'PLAYING':
        speaker.pause()

    speaker.volume = config('SPEAKER_VOLUME')
    speaker.play_uri(config('SOUND_URI'))

    send_slack_msg()

    sleep(5)
    speaker.pause()


    # Resume from snapshot
    snap.restore()

def main():
    print('Connecting to speaker...')
    # Discove speaker
    speaker = find_speaker(config('SPEAKER_NAME'), config('SPEAKER_IFACE'))

    # Define GPIO -pins as standard
    GPIO.setmode(GPIO.BCM)

    # Define pin 18 as input and enable internal resistors
    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print('Testing speaker...')
    ring(speaker)

    # function for button press
    print('Doorbell ready')
    while True:
        input_state = GPIO.input(18)
        if input_state == False:
            print ("The button works!")
            ring(speaker)

        # Sleep.
        sleep(0.3)

if __name__ == "__main__":
    main()
