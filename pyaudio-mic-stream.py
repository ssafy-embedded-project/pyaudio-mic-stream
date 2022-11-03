# pyaudio-mic-stream.py

import pyaudio
import queue
import time

# 디지털 사운드 인코딩 특성
RATE = 16000 # Hz
CHUNK = int(RATE/10) # 연속되는 음성 데이터를 끊어 처리하기 위한 버퍼크기. 100ms

# 음성데이터 스트림
class MicrophoneStream:
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()  # 마이크로 입력받은 오디오 데이터를 chunk 단위로 queue에 저장한다.
        self.closed = True  # audio스트림 열려있는지 닫혀있는지

    # 클래스 생성 (스트림 시작)될 때
    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(    # pyaudio.open()은 pyaudio.Stream object를 리턴.
            format = pyaudio.paInt16,  #16bit 다이나믹 레인지
            channels = 1,   # mono
            rate = self._rate,  # sampling rate
            input = True,   # 마이크로부터 입력되는 스트림임 명시
            frames_per_buffer = self._chunk,
            stream_callback = self._fill_buffer,    # 버퍼가 chunk만큼 꽉 찼을 때 실행할 콜백함수 등록 (non-blocking)
        )
        self.closed = False
        return self

    # 스트림 끝날 때
    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    # 버퍼 찼을 때 콜백함수. pyaudio.Stream에서 호출되는 콜백은 4개 매개변수 갖고, 2개값 리턴한다. pyaudio문서 참고.
    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data) # data를 queue에 넣기
        return None, pyaudio.paContinue

    # python generator, 한 라운드의 루프마다 현재 버퍼의 내용을 모아서  byte-stream을 생산함.
    def generator(self):
        while not self.closed:
            chunk = self._buff.get() # 큐에서 데이터 가져오기
            if chunk is None:
                return

            # 큐에 더이상 데이터가 없을 때 까지 data에 이어붙임
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            
            yield b''.join(data)    # byte-stream

def main():
    # mic로부터 오디오스트림 생성      
    MicStream = MicrophoneStream(RATE, CHUNK)
    with MicStream as stream:   
        audio_generator = stream.generator()

        for val in audio_generator:
            print(val)  # raw data 출력

if __name__ == '__main__':
    main()
