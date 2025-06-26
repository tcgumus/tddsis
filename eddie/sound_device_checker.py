import sounddevice as sd
import numpy as np

def check_microphone():
    try:
        devices = sd.query_devices()
        input_devices = [device for device in devices if device['max_input_channels'] > 0]

        if not input_devices:
            print("No physical microphone detected.")
            return False
        else:
            print("Microphone detected:")
            for device in input_devices:
                print(f"- {device['name']} (ID: {device['index']})")

            mic_index = input_devices[0]['index']
            try:
                with sd.InputStream(device=mic_index):
                    print("Microphone is enabled and working.")
                    return True
            except Exception as e:
                print("Microphone detected but is disabled or not accessible:", e)
                return False

    except OSError as e:
        print(f"Error accessing audio devices. Microphone may be disabled or drivers missing: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def check_speaker():
    try:
        devices = sd.query_devices()
        output_devices = [device for device in devices if device['max_output_channels'] > 0]

        if not output_devices:
            print("No physical speaker detected.")
            return False
        else:
            print("Speaker detected:")
            for device in output_devices:
                print(f"- {device['name']} (ID: {device['index']})")

            speaker_index = output_devices[0]['index']
            try:
                sample_rate = 44100
                duration = 0.5
                silent_sound = np.zeros(int(sample_rate * duration))

                with sd.OutputStream(device=speaker_index, samplerate=sample_rate, channels=1):
                    sd.play(silent_sound, samplerate=sample_rate)
                    sd.wait()
                print("Speaker is enabled and working.")
                return True
            except Exception as e:
                print("Speaker detected but is disabled or not accessible:", e)
                return False

    except OSError as e:
        print(f"Error accessing audio devices. Speaker may be disabled or drivers missing: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


