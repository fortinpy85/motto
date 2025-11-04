import os
import uuid
from datetime import datetime

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from structlog import get_logger
from structlog.contextvars import bind_contextvars, get_contextvars

from chat.llm import OttoLLM
from chat.utils import swap_glossary_columns
from otto.models import Cost

logger = get_logger(__name__)
ten_minutes = 600


@shared_task(soft_time_limit=ten_minutes)
def extract_text_task(file_id, pdf_method="default", context_vars=None):
    """
    Celery task to extract text from a ChatFile.
    Returns the file_id when complete, or raises an exception on error.
    """
    try:
        from chat.models import ChatFile
        from librarian.utils.process_engine import (
            extract_markdown,
            get_process_engine_from_type,
            guess_content_type,
        )

        # Bind context variables for cost tracking
        if context_vars:
            bind_contextvars(**context_vars)

        file = ChatFile.objects.get(id=file_id)

        if not file.saved_file:
            raise Exception("No saved file found")

        with file.saved_file.file.open("rb") as file_handle:
            content = file_handle.read()
            content_type = guess_content_type(
                content, file.saved_file.content_type, file.filename
            )
            process_engine = get_process_engine_from_type(content_type)
            extraction_result = extract_markdown(
                content, process_engine, pdf_method=pdf_method
            )
            file.text = extraction_result.markdown
            file.save()

        return file_id

    except Exception as e:
        logger.exception(f"Error in extract_text_task for file {file_id}: {e}")
        raise


@shared_task(soft_time_limit=ten_minutes)
def translate_file(
    file_path, target_language, custom_translator_id=None, glossary_path=None
):
    if target_language == "fr":
        target_language = "fr-ca"
    try:
        from chat.models import ChatFile, Message
        from django.core.files.base import ContentFile

        with open(file_path, "rb") as f:
            file_content = f.read()

        llm = OttoLLM(deployment="gemini-1.5-flash")
        prompt = f"Translate the following document to {target_language}:\n\n{file_content.decode('utf-8')}"
        translated_text = llm.complete(prompt)
        llm.create_costs()

        file_name = file_path.split("/")[-1]
        file_extension = os.path.splitext(file_name)[1]
        file_name_without_extension = os.path.splitext(file_name)[0]
        output_file_name = (
            f"{file_name_without_extension}_{target_language.upper()}{file_extension}"
        )

        request_context = get_contextvars()
        out_message = Message.objects.get(id=request_context.get("message_id"))

        new_file = ChatFile.objects.create(
            message=out_message,
            filename=output_file_name,
            content_type="text/plain",
        )
        new_file.saved_file.file.save(
            output_file_name, ContentFile(translated_text.encode("utf-8"))
        )

    except SoftTimeLimitExceeded:
        logger.error(f"Translation task timed out for {file_path}")
        raise Exception(f"Translation task timed out for {file_path}")
    except Exception as e:
        logger.exception(f"Error translating {file_path}: {e}")
        raise Exception(f"Error translating {file_path}")
