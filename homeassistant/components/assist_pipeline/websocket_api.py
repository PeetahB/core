"""Assist pipeline Websocket API."""

import asyncio

# Suppressing disable=deprecated-module is needed for Python 3.11
import audioop  # pylint: disable=deprecated-module
import base64
from collections.abc import AsyncGenerator, Callable
import contextlib
import logging
import math
from typing import Any, Final,Optional,Tuple

import voluptuous as vol

from homeassistant.components import conversation, stt, tts, websocket_api
from homeassistant.const import ATTR_DEVICE_ID, ATTR_SECONDS, MATCH_ALL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.util import language as language_util

from .const import (
    DEFAULT_PIPELINE_TIMEOUT,
    DEFAULT_WAKE_WORD_TIMEOUT,
    DOMAIN,
    EVENT_RECORDING,
    SAMPLE_CHANNELS,
    SAMPLE_RATE,
    SAMPLE_WIDTH,
)
from .error import PipelineNotFound
from .pipeline import (
    AudioSettings,
    DeviceAudioQueue,
    Pipeline,
    PipelineData,
    PipelineError,
    PipelineEvent,
    PipelineEventType,
    PipelineInput,
    PipelineRun,
    PipelineStage,
    WakeWordSettings,
    async_get_pipeline,
)

_LOGGER = logging.getLogger(__name__)

CAPTURE_RATE: Final = 16000
CAPTURE_WIDTH: Final = 2
CAPTURE_CHANNELS: Final = 1
MAX_CAPTURE_TIMEOUT: Final = 60.0


@callback
def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register the websocket API."""
    websocket_api.async_register_command(hass, websocket_run)
    websocket_api.async_register_command(hass, websocket_list_languages)
    websocket_api.async_register_command(hass, websocket_list_runs)
    websocket_api.async_register_command(hass, websocket_list_devices)
    websocket_api.async_register_command(hass, websocket_get_run)
    websocket_api.async_register_command(hass, websocket_device_capture)


@websocket_api.websocket_command(
    vol.All(
        websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
            {
                vol.Required("type"): "assist_pipeline/run",
                # pylint: disable-next=unnecessary-lambda
                vol.Required("start_stage"): lambda val: PipelineStage(val),
                # pylint: disable-next=unnecessary-lambda
                vol.Required("end_stage"): lambda val: PipelineStage(val),
                vol.Optional("input"): dict,
                vol.Optional("pipeline"): str,
                vol.Optional("conversation_id"): vol.Any(str, None),
                vol.Optional("device_id"): vol.Any(str, None),
                vol.Optional("timeout"): vol.Any(float, int),
            },
        ),
        cv.key_value_schemas(
            "start_stage",
            {
                PipelineStage.WAKE_WORD: vol.Schema(
                    {
                        vol.Required("input"): {
                            vol.Required("sample_rate"): int,
                            vol.Optional("timeout"): vol.Any(float, int),
                            vol.Optional("audio_seconds_to_buffer"): vol.Any(
                                float, int
                            ),
                            # Audio enhancement
                            vol.Optional("noise_suppression_level"): int,
                            vol.Optional("auto_gain_dbfs"): int,
                            vol.Optional("volume_multiplier"): float,
                            # Advanced use cases/testing
                            vol.Optional("no_vad"): bool,
                        }
                    },
                    extra=vol.ALLOW_EXTRA,
                ),
                PipelineStage.STT: vol.Schema(
                    {
                        vol.Required("input"): {
                            vol.Required("sample_rate"): int,
                            vol.Optional("wake_word_phrase"): str,
                        }
                    },
                    extra=vol.ALLOW_EXTRA,
                ),
                PipelineStage.INTENT: vol.Schema(
                    {vol.Required("input"): {"text": str}},
                    extra=vol.ALLOW_EXTRA,
                ),
                PipelineStage.TTS: vol.Schema(
                    {vol.Required("input"): {"text": str}},
                    extra=vol.ALLOW_EXTRA,
                ),
            },
        ),
    ),
)
@websocket_api.async_response
async def websocket_run(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Run a pipeline."""
    pipeline_id = msg.get("pipeline")
    pipeline = get_pipeline(hass, connection, msg, pipeline_id)
    if pipeline is None:  # Error already sent in get_pipeline
        return

    timeout = msg.get("timeout", DEFAULT_PIPELINE_TIMEOUT)
    start_stage = PipelineStage(msg["start_stage"])
    end_stage = PipelineStage(msg["end_stage"])

    input_args, handler_id, unregister_handler, wake_word_settings, audio_settings = await prepare_input_args(
        msg, start_stage, pipeline, connection
    )

    input_args["run"] = create_pipeline_run(
        hass, connection, pipeline, start_stage, end_stage, handler_id, timeout, wake_word_settings, audio_settings, msg
    )

    pipeline_input = PipelineInput(**input_args)

    if await validate_pipeline_input(pipeline_input, connection, msg):
        return  # Error already sent in validate_pipeline_input

    # Confirm subscription
    connection.send_result(msg["id"])
    run_task = hass.async_create_task(pipeline_input.execute())

    # Cancel pipeline if user unsubscribes
    connection.subscriptions[msg["id"]] = run_task.cancel

    await run_pipeline_with_timeout(run_task, pipeline_input, timeout)


def get_pipeline(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any], pipeline_id: str
) -> Pipeline | None:
    """Get the pipeline and handle errors."""
    try:
        return async_get_pipeline(hass, pipeline_id=pipeline_id)  # Not awaited
    except PipelineNotFound:
        connection.send_error(
            msg["id"],
            "pipeline-not-found",
            f"Pipeline not found: id={pipeline_id}",
        )
        return None


async def prepare_input_args(
    msg: dict[str, Any],
    start_stage: PipelineStage,
    pipeline: Pipeline,
    connection: websocket_api.ActiveConnection,  # Added connection here
) -> Tuple[dict[str, Any], Optional[int], Optional[Callable[[], None]], Optional[WakeWordSettings], Optional[AudioSettings]]:
    """Prepare input arguments for the pipeline."""
    input_args = {
        "conversation_id": msg.get("conversation_id"),
        "device_id": msg.get("device_id"),
    }
    handler_id, unregister_handler = None, None
    wake_word_settings, audio_settings = None, None
    wake_word_phrase: str | None = None

    if start_stage in (PipelineStage.WAKE_WORD, PipelineStage.STT):
        msg_input = msg["input"]
        audio_queue = asyncio.Queue()
        incoming_sample_rate = msg_input["sample_rate"]

        if start_stage == PipelineStage.WAKE_WORD:
            wake_word_settings = WakeWordSettings(
                timeout=msg_input.get("timeout", DEFAULT_WAKE_WORD_TIMEOUT),
                audio_seconds_to_buffer=msg_input.get("audio_seconds_to_buffer", 0),
            )
        else:  # start_stage == PipelineStage.STT
            wake_word_phrase = msg_input.get("wake_word_phrase")

        handler_id, unregister_handler = connection.async_register_binary_handler(
            lambda _hass, _connection, data: audio_queue.put_nowait(data)
        )

        input_args["stt_metadata"] = stt.SpeechMetadata(
            language=pipeline.stt_language or pipeline.language,
            format=stt.AudioFormats.WAV,
            codec=stt.AudioCodecs.PCM,
            bit_rate=stt.AudioBitRates.BITRATE_16,
            sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
            channel=stt.AudioChannels.CHANNEL_MONO,
        )
        input_args["stt_stream"] = create_stt_stream(audio_queue, incoming_sample_rate)
        input_args["wake_word_phrase"] = wake_word_phrase

        audio_settings = AudioSettings(
            noise_suppression_level=msg_input.get("noise_suppression_level", 0),
            auto_gain_dbfs=msg_input.get("auto_gain_dbfs", 0),
            volume_multiplier=msg_input.get("volume_multiplier", 1.0),
            is_vad_enabled=not msg_input.get("no_vad", False),
        )
    elif start_stage == PipelineStage.INTENT:
        input_args["intent_input"] = msg["input"]["text"]
    elif start_stage == PipelineStage.TTS:
        input_args["tts_input"] = msg["input"]["text"]

    return input_args, handler_id, unregister_handler, wake_word_settings, audio_settings


def create_stt_stream(audio_queue: asyncio.Queue[bytes], incoming_sample_rate: int) -> AsyncGenerator[bytes]:
    """Create the STT stream."""
    async def stt_stream() -> AsyncGenerator[bytes]:
        state = None
        while chunk := await audio_queue.get():
            if incoming_sample_rate != SAMPLE_RATE:
                chunk, state = audioop.ratecv(
                    chunk,
                    SAMPLE_WIDTH,
                    SAMPLE_CHANNELS,
                    incoming_sample_rate,
                    SAMPLE_RATE,
                    state,
                )
            yield chunk

    return stt_stream()


def create_pipeline_run(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    pipeline: Pipeline,
    start_stage: PipelineStage,
    end_stage: PipelineStage,
    handler_id: Optional[int],
    timeout: int,
    wake_word_settings: Optional[WakeWordSettings],
    audio_settings: Optional[AudioSettings],
    msg: dict[str, Any]  # Pass msg to this function
) -> PipelineRun:
    """Create a PipelineRun instance."""
    return PipelineRun(
        hass,
        context=connection.context(msg),
        pipeline=pipeline,
        start_stage=start_stage,
        end_stage=end_stage,
        event_callback=lambda event: connection.send_event(msg["id"], event),
        runner_data={
            "stt_binary_handler_id": handler_id,
            "timeout": timeout,
        },
        wake_word_settings=wake_word_settings,
        audio_settings=audio_settings or AudioSettings(),
    )


async def validate_pipeline_input(pipeline_input: PipelineInput, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> bool:
    """Validate the pipeline input and handle errors."""
    try:
        await pipeline_input.validate()
    except PipelineError as error:
        connection.send_error(msg["id"], error.code, error.message)
        return True  # Error occurred
    return False  # No error


async def run_pipeline_with_timeout(run_task: asyncio.Task, pipeline_input: PipelineInput, timeout: int) -> None:
    """Run the pipeline and handle timeout."""
    try:
        async with asyncio.timeout(timeout):
            await run_task
    except TimeoutError:
        pipeline_input.run.process_event(
            PipelineEvent(
                PipelineEventType.ERROR,
                {"code": "timeout", "message": "Timeout running pipeline"},
            )
        )

@callback
@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "assist_pipeline/pipeline_debug/list",
        vol.Required("pipeline_id"): str,
    }
)
def websocket_list_runs(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """List pipeline runs for which debug data is available."""
    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_id = msg["pipeline_id"]

    if pipeline_id not in pipeline_data.pipeline_debug:
        connection.send_result(msg["id"], {"pipeline_runs": []})
        return

    pipeline_debug = pipeline_data.pipeline_debug[pipeline_id]

    connection.send_result(
        msg["id"],
        {
            "pipeline_runs": [
                {
                    "pipeline_run_id": pipeline_run_id,
                    "timestamp": pipeline_run.timestamp,
                }
                for pipeline_run_id, pipeline_run in pipeline_debug.items()
            ]
        },
    )


@callback
@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "assist_pipeline/device/list",
    }
)
def websocket_list_devices(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """List assist devices."""
    pipeline_data: PipelineData = hass.data[DOMAIN]
    ent_reg = er.async_get(hass)
    connection.send_result(
        msg["id"],
        [
            {
                "device_id": device_id,
                "pipeline_entity": ent_reg.async_get_entity_id(
                    "select", info.domain, f"{info.unique_id_prefix}-pipeline"
                ),
            }
            for device_id, info in pipeline_data.pipeline_devices.items()
        ],
    )


@callback
@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "assist_pipeline/pipeline_debug/get",
        vol.Required("pipeline_id"): str,
        vol.Required("pipeline_run_id"): str,
    }
)
def websocket_get_run(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get debug data for a pipeline run."""
    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_id = msg["pipeline_id"]
    pipeline_run_id = msg["pipeline_run_id"]

    if pipeline_id not in pipeline_data.pipeline_debug:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            f"pipeline_id {pipeline_id} not found",
        )
        return

    pipeline_debug = pipeline_data.pipeline_debug[pipeline_id]

    if pipeline_run_id not in pipeline_debug:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            f"pipeline_run_id {pipeline_run_id} not found",
        )
        return

    connection.send_result(
        msg["id"],
        {"events": pipeline_debug[pipeline_run_id].events},
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "assist_pipeline/language/list",
    }
)
@callback
def websocket_list_languages(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """List languages supported by a complete pipeline."""
    # Get languages from conversation, STT, and TTS
    conv_language_tags = conversation.async_get_conversation_languages(hass)
    stt_language_tags = stt.async_get_speech_to_text_languages(hass)
    tts_language_tags = tts.async_get_text_to_speech_languages(hass)

    # Process the pipeline languages
    pipeline_languages = _process_language_tags(conv_language_tags)
    pipeline_languages = _intersect_languages(pipeline_languages, stt_language_tags)
    pipeline_languages = _intersect_languages(pipeline_languages, tts_language_tags)

    # Send the result
    connection.send_result(
        msg["id"],
        {"languages": sorted(pipeline_languages) if pipeline_languages else None}
    )


def _process_language_tags(language_tags: set[str] | None) -> set[str] | None:
    """Convert language tags to a set of language codes, return None if tags are empty."""
    if not language_tags or language_tags == MATCH_ALL:
        return None
    return {language_util.Dialect.parse(tag).language for tag in language_tags}


def _intersect_languages(pipeline_languages: set[str] | None, new_language_tags: set[str] | None) -> set[str] | None:
    """Intersect the pipeline languages with new tags, or initialize if pipeline is None."""
    if not new_language_tags:
        return pipeline_languages
    new_languages = _process_language_tags(new_language_tags)
    return language_util.intersect(pipeline_languages, new_languages) if pipeline_languages else new_languages



@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "assist_pipeline/device/capture",
        vol.Required("device_id"): str,
        vol.Required("timeout"): vol.All(
            # 0 < timeout <= MAX_CAPTURE_TIMEOUT
            vol.Coerce(float),
            vol.Range(min=0, min_included=False, max=MAX_CAPTURE_TIMEOUT),
        ),
    }
)
@websocket_api.async_response
async def websocket_device_capture(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Capture raw audio from a satellite device and forward to client."""
    pipeline_data: PipelineData = hass.data[DOMAIN]
    device_id = msg["device_id"]

    # Number of seconds to record audio in wall clock time
    timeout_seconds = msg["timeout"]

    # We don't know the chunk size, so the upper bound is calculated assuming a
    # single sample (16 bits) per queue item.
    max_queue_items = (
        # +1 for None to signal end
        int(math.ceil(timeout_seconds * CAPTURE_RATE)) + 1
    )

    audio_queue = DeviceAudioQueue(queue=asyncio.Queue(maxsize=max_queue_items))

    # Running simultaneous captures for a single device will not work by design.
    # The new capture will cause the old capture to stop.
    if (
        old_audio_queue := pipeline_data.device_audio_queues.pop(device_id, None)
    ) is not None:
        with contextlib.suppress(asyncio.QueueFull):
            # Signal other websocket command that we're taking over
            old_audio_queue.queue.put_nowait(None)

    # Only one client can be capturing audio at a time
    pipeline_data.device_audio_queues[device_id] = audio_queue

    def clean_up_queue() -> None:
        # Clean up our audio queue
        maybe_audio_queue = pipeline_data.device_audio_queues.get(device_id)
        if (maybe_audio_queue is not None) and (maybe_audio_queue.id == audio_queue.id):
            # Only pop if this is our queue
            pipeline_data.device_audio_queues.pop(device_id)

    # Unsubscribe cleans up queue
    connection.subscriptions[msg["id"]] = clean_up_queue

    # Audio will follow as events
    connection.send_result(msg["id"])

    # Record to logbook
    hass.bus.async_fire(
        EVENT_RECORDING,
        {
            ATTR_DEVICE_ID: device_id,
            ATTR_SECONDS: timeout_seconds,
        },
    )

    try:
        with contextlib.suppress(TimeoutError):
            async with asyncio.timeout(timeout_seconds):
                while True:
                    # Send audio chunks encoded as base64
                    audio_bytes = await audio_queue.queue.get()
                    if audio_bytes is None:
                        # Signal to stop
                        break

                    connection.send_event(
                        msg["id"],
                        {
                            "type": "audio",
                            "rate": CAPTURE_RATE,  # hertz
                            "width": CAPTURE_WIDTH,  # bytes
                            "channels": CAPTURE_CHANNELS,
                            "audio": base64.b64encode(audio_bytes).decode("ascii"),
                        },
                    )

        # Capture has ended
        connection.send_event(
            msg["id"], {"type": "end", "overflow": audio_queue.overflow}
        )
    finally:
        clean_up_queue()
