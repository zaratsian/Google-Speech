import argparse
import asyncio
import websockets
from google.cloud import speech
import time
import io
from pydub import AudioSegment

FRAMERATE = 16000

client = speech.SpeechClient()

def wrap_opus_packet_in_ogg(raw_packet, framerate):
    audio_segment = AudioSegment(raw_packet, frame_rate=framerate, sample_width=2, channels=1)
    in_memory_obj = io.BytesIO()
    audio_segment.export(in_memory_obj, format="ogg")
    in_memory_obj.seek(0)
    return in_memory_obj


async def process_audio(websocket, path):
    
    try:
        async def stream_generator(websocket):
            window_length = 200
            window = []
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    #message = await websocket.recv()
                    window.append(message)
                    #print(len(window))
                    if len(window) >= window_length:
                        result = b''.join(window[:window_length])
                        ogg = wrap_opus_packet_in_ogg(result, framerate=FRAMERATE)
                        yield ogg
                        window = window[window_length:]
                except asyncio.TimeoutError:
                    if len(window) >= 0:
                        result = b''.join(window[:window_length])
                        ogg = wrap_opus_packet_in_ogg(result, framerate=FRAMERATE)
                        yield ogg
                        window = window[window_length:]
                    print('[ INFO ] Sending close signal to websocket client')
                    print('[ INFO ] Waiting for new audio stream...')
                    await websocket.send('close ws')
                    time.sleep(1)

        async def recognize_speech(stream):
            requests = (
                speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in stream
            )

            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=FRAMERATE,
                language_code="en-US",
            )

            streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=False)

            responses = client.streaming_recognize(
                config=streaming_config,
                requests=requests,
            )

            for response in responses:
                print('[ INFO ] Processing streaming responses...')
                for result in response.results:
                    print(f'result: {result}')
                    if result.is_final:
                        print(f'Final transcription: {result.alternatives[0].transcript}')
                        return result.alternatives[0].transcript

        async for chunk in stream_generator(websocket):
            #print('new chunk')
            final_transcript = await recognize_speech(chunk)
            if final_transcript:
                await websocket.send(final_transcript)
    except Exception as e:
        # Handle the connection closed error
        print(f'[ WARNING ] Client connection has been closed. {e}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--port', type=int, default=7777, help='Websocket server port number')
    args = parser.parse_args()

    async def websocket_server():
        async with websockets.serve(process_audio, "0.0.0.0", args.port):
            print(f'[ INFO ] Server running on port {args.port}\n')
            await asyncio.Future()  # keep server running

    print(f'\n[ INFO ] Starting websocket server...')
    asyncio.run(websocket_server())
