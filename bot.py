#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Gemini Live + WhatsApp Example.

A Pipecat bot that uses Google Gemini Live and WhatsApp.
You can connect to this bot using either SmallWebRTC or WhatsApp.

Required AI services:
- Google Gemini Live (LLM)

Run the bot locally using:

    uv run bot.py
"""

import os
import sys

# Windows UTF-8 console fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from bot_prompt import PipecatPrompt
from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import TranscriptionMessage, LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.processors.transcript_processor import TranscriptProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecatcloud import PipecatSessionArguments, SmallWebRTCSessionManager
from pipecatcloud.agent import SmallWebRTCSessionArguments

load_dotenv(override=True)

# Create a global session manager instance
session_manager = SmallWebRTCSessionManager(timeout_seconds=120)

async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    """Run your bot with the provided transport.

    Args:
        transport (BaseTransport): The transport to use for communication.
        runner_args: runner session arguments
    """
    llm = GeminiMultimodalLiveLLMService(
        model="models/gemini-2.5-flash-native-audio-latest",
        api_key=os.getenv("GOOGLE_API_KEY"),
        voice_id="Kore",  # Female: Kore, Aoede, Leda. Male: Puck, Charon, Fenrir, Orus
        system_instruction=PipecatPrompt.get_prompt()
    )

    messages = [
        {
            "role": "user",
            "content": "Introduce yourself in one sentence and ask how you can help.",
        },
    ]

    # This sets up the LLM context by providing messages and tools
    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    # Emit `on_transcript_update` events for the user and assistant spoken responses
    transcript = TranscriptProcessor()

    # Add RTVI to the pipeline to receive events for the SmallWebRTC Prebuilt UI
    # Only needed for client/server messaging and events
    # You can remove RTVI processors and observers for Twilio/phone use cases
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    pipeline = Pipeline(
        [
            transport.input(),  # Transport user input
            rtvi,
            context_aggregator.user(),  # User respones
            transcript.user(),  # User transcript
            llm,  # LLM
            transport.output(),  # Transport bot output
            transcript.assistant(),  # Assistant transcript
            context_aggregator.assistant(),  # Assistant spoken responses
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        logger.debug("Client ready event received")
        await rtvi.set_bot_ready()

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected.")
        # Kick off the conversation
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, participant):
        logger.info("Client disconnected: {}", participant)
        await task.cancel()

    # Register event handler for transcript updates
    @transcript.event_handler("on_transcript_update")
    async def on_transcript_update(processor, frame):
        for msg in frame.messages:
            if isinstance(msg, TranscriptionMessage):
                timestamp = f"[{msg.timestamp}] " if msg.timestamp else ""
                line = f"{timestamp}{msg.role}: {msg.content}"
                logger.info(f"Transcript: {line}")

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""

    if isinstance(runner_args, PipecatSessionArguments):
        logger.info("Starting the bot, but still waiting for the webrtc_connection to be set")
        try:
            await session_manager.wait_for_webrtc()
        except TimeoutError as e:
            logger.error(f"Timeout waiting for WebRTC connection: {e}")
            raise
        return

    elif isinstance(runner_args, SmallWebRTCSessionArguments):
        logger.info("Received the webrtc_connection from Pipecat Cloud, will start the pipeline")
        session_manager.cancel_timeout()

    webrtc_connection: SmallWebRTCConnection = runner_args.webrtc_connection
    try:
        if os.environ.get("ENV") != "local":
            from pipecat.audio.filters.krisp_filter import KrispFilter

            krisp_filter = KrispFilter()
        else:
            krisp_filter = None

        transport = SmallWebRTCTransport(
            webrtc_connection=webrtc_connection,
            params=TransportParams(
                audio_in_enabled=True,
                audio_in_filter=krisp_filter,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
            ),
        )

        if transport is None:
            logger.error("Failed to create transport")
            return

        await run_bot(transport, runner_args)
        logger.info("Bot process completed")
    except Exception as e:
        logger.exception(f"Error in bot process: {str(e)}")
        raise
    finally:
        logger.info("Cleaning up SmallWebRTC resources")
        session_manager.complete_session()


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
