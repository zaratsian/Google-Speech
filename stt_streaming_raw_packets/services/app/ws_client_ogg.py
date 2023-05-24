import asyncio
import websockets
import time
import csv
import json
import base64
import opuslib
import sys
import io
from pydub import AudioSegment
import argparse

try:
    host = sys.argv[1]
except:
    host = '0.0.0.0'

try:
    record_number = int(sys.argv[2])
except:
    record_number = 0

def tsv_to_json(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        data = [dict(zip(header, row)) for row in reader]
    return data


def decode_base64_audio(base64_audio):
    audio_bytes = base64.b64decode(base64_audio)
    decoder = opuslib.Decoder(16000, 1)  # sample rate and channels
    decoded_audio = decoder.decode(audio_bytes, 360)  # framesize
    return decoded_audio


async def send_opus_packet():

    async with websockets.connect('ws://localhost:7777') as websocket:
        # Load Sample Audio files (base64 encoded raw opus packets)
        audio_records = tsv_to_json('GoogleSTT_for_PS-audio_sample-opus_raw-non_prod.tsv')
        audio_record_base64 = [json.loads(ar['Audio']) for ar in audio_records]

        # Decode base64 encoded raw opus packets
        decoded_audio_packets = []
        for duplicate in range(10):
            for base64_audio in audio_record_base64[record_number]:
                decoded_audio_packets.append(decode_base64_audio(base64_audio))

        start_time = time.time()

        # Send raw audio packets to websocket server
        print(f"\n[ INFO ] Sending record {record_number}. Expected Transcription: {[ar['Transcription'] for ar in audio_records][record_number]}")
        for packet in decoded_audio_packets:
            await websocket.send(packet)

        # Continue receiving responses until the connection is closed or timeout occurs
        # Receive websocket responses and then close the socket.
        while True:
            result = await websocket.recv()
            if result == "" or result == None or result=='close ws':
                break
            
            print(f'Transcription: {result}')
        
        print()
        await websocket.close()

        
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(send_opus_packet())
