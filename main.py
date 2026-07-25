import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, NoReturn

import sounddevice as sd
from dotenv import load_dotenv
from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(-1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class Config:
    def __init__(self) -> None:
        load_dotenv()
        self.mod_host: str = os.getenv("MOD_HOST", "127.0.0.1")
        try:
            self.mod_port: int = int(os.getenv("MOD_PORT", "25565"))
        except ValueError:
            self.mod_port = 25565
            logger.warning("Invalid MOD_PORT in .env, defaulting to 25565")
        self.model_path: str = "model"
        self.target_words: tuple[str, ...] = ("щит", "шит", "фит", "хит", "сид")
        self.sample_rate: int = 16000


class ModClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    async def send_command(self, command: str) -> None:
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
            writer.write(command.encode("utf-8"))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            logger.info("Command '%s' sent to Java mod", command)
        except ConnectionRefusedError:
            logger.error("Connection refused by Java mod. Is the server open?")
        except Exception as e:
            logger.error("Failed to send command: %s", e)


class VoiceRecognizer:
    def __init__(self, config: Config, mod_client: ModClient) -> None:
        self.config = config
        self.mod_client = mod_client
        self.loop = asyncio.get_running_loop()
        self.audio_queue: asyncio.Queue[bytes] = asyncio.Queue()

        try:
            self.model = Model(self.config.model_path)
        except Exception as e:
            logger.critical("Failed to load Vosk model: %s", e)
            sys.exit(1)

        self.recognizer = KaldiRecognizer(self.model, self.config.sample_rate)

    def audio_callback(self, indata: Any, frames: int, time_info: Any, status: Any) -> None:
        if status:
            logger.warning("Audio status: %s", status)
        self.loop.call_soon_threadsafe(self.audio_queue.put_nowait, bytes(indata))

    async def process_audio(self) -> NoReturn:
        logger.info("Starting audio processing loop...")
        while True:
            data: bytes = await self.audio_queue.get()
            self.recognizer.AcceptWaveform(data)

            result_str: str = self.recognizer.PartialResult()

            try:
                result_dict: Dict[str, Any] = json.loads(result_str)
                text: str = result_dict.get("partial", "").lower()

                if text:
                    if any(word in text for word in self.config.target_words):
                        logger.info("Target word detected instantly (Matched in: '%s')!", text)
                        await self.mod_client.send_command("EQUIP_SHIELD")
                        self.recognizer.Reset()
            except json.JSONDecodeError as e:
                logger.error("JSON parse error: %s", e)
            except Exception as e:
                logger.error("Error processing audio result: %s", e)

    async def start_listening(self) -> None:
        try:
            with sd.RawInputStream(
                    samplerate=self.config.sample_rate,
                    blocksize=800,
                    dtype="int16",
                    channels=1,
                    callback=self.audio_callback
            ):
                logger.info("Microphone initialized. Listening for %s...", self.config.target_words)
                await self.process_audio()
        except Exception as e:
            logger.critical("Microphone error: %s", e)


async def main() -> None:
    config = Config()
    mod_client = ModClient(config.mod_host, config.mod_port)
    recognizer = VoiceRecognizer(config, mod_client)
    await recognizer.start_listening()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")