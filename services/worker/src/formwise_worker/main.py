import argparse
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import cycle, islice

import structlog

from formwise_worker.config import get_worker_settings
from formwise_worker.firebase import get_firestore_client
from formwise_worker.logging import configure_logging
from formwise_worker.ocr.worker import FirestoreOcrWorker
from formwise_worker.operations import FirestoreOperationalReporter
from formwise_worker.rendering.composition import build_render_worker
from formwise_worker.retention.composition import build_retention_worker


def main() -> None:
    parser = argparse.ArgumentParser(description="FormWise OCR worker")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process at most one durable OCR job.",
    )
    arguments = parser.parse_args()

    settings = get_worker_settings()

    configure_logging(settings.log_level)
    logger = structlog.get_logger()

    client = get_firestore_client()

    reporter = FirestoreOperationalReporter(
        client,
        settings.worker_instance_id,
    )

    ocr_worker = FirestoreOcrWorker(
        client,
        settings,
        reporter=reporter,
    )

    render_worker = build_render_worker(client, settings)
    retention_worker = build_retention_worker(client, settings)

    processors = [
        ocr_worker.process_once,
        render_worker.process_once,
        retention_worker.process_once,
    ]

    if arguments.once:
        if not ocr_worker.process_once() and not render_worker.process_once():
            retention_worker.process_once()

        try:
            reporter.heartbeat(active_jobs=0)
        except Exception as error:
            logger.warning(
                "worker_heartbeat_unavailable",
                error_type=type(error).__name__,
            )
        return

    last_heartbeat = 0.0
    processor_cycle = cycle(processors)

    with ThreadPoolExecutor(
        max_workers=settings.worker_max_concurrency
    ) as executor:
        while True:
            selected = list(
                islice(
                    processor_cycle,
                    settings.worker_max_concurrency,
                )
            )

            futures = [executor.submit(processor) for processor in selected]

            processed = 0

            for future in futures:
                try:
                    processed += int(future.result())
                except Exception as error:
                    logger.error(
                        "worker_loop_failure",
                        error_type=type(error).__name__,
                    )

            now = time.monotonic()

            if now - last_heartbeat >= settings.worker_heartbeat_seconds:
                try:
                    reporter.heartbeat(active_jobs=processed)
                except Exception as error:
                    logger.warning(
                        "worker_heartbeat_unavailable",
                        error_type=type(error).__name__,
                    )

                last_heartbeat = now

            if not processed:
                time.sleep(settings.ocr_worker_poll_seconds)


if __name__ == "__main__":
    main()
