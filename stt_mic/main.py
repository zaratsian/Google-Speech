import re
import sys
import os
import datetime

from google.cloud import speech, storage

import pyaudio
from six.moves import queue
from models import sentiment, redact

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'stealth-air-23412-f7423ca617a5.json'

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)

class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


def listen_print_loop(responses):

    try:
        channel_convo_list = []
        num_chars_printed = 0
        for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            # Display the transcription of the top alternative.
            transcript = result.alternatives[0].transcript

            overwrite_chars = " " * (num_chars_printed - len(transcript))

            if not result.is_final:
                sys.stdout.write(transcript + overwrite_chars + "\r")
                sys.stdout.flush()

                num_chars_printed = len(transcript)

            else:

                datetimestr = f'{datetime.datetime.now()}'
                translationLog = f'{datetimestr}: {(transcript + overwrite_chars).strip()}'
                print(translationLog)
                print(f'Sentiment: {sentiment(transcript + overwrite_chars)}')
                print(f'Redacted:  {redact(transcript + overwrite_chars)}')
                print('\n')

                channel_convo_list.append(translationLog)

                # Exit recognition
                if re.search(r"\b(exit|quit|end session)\b", transcript, re.I):
                    blob_name = f"stt_{datetimestr}"
                    gcsUpload(bucket_name='steath-air-stt-dropzone', contents='\n'.join(channel_convo_list), destination_blob_name=blob_name)
                    print("Exiting..")
                    break

                num_chars_printed = 0
    except KeyboardInterrupt:
        blob_name = f"stt_{datetimestr}"


def gcsUpload(bucket_name, contents, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(contents)

    print(f"{destination_blob_name} uploaded to {bucket_name}.")


def main():

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
        profanity_filter=True,
        model="default"
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses)


if __name__ == "__main__":
    main()