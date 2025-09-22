"""
SMS Celery Tasks

Celery tasks for asynchronous SMS sending using simple routing.
Routes SMS messages via SMS Router based on country codes - single attempt only.
"""

import logging
from celery import shared_task
from typing import List, Optional

from core.services.sms_router import sms_router

logger = logging.getLogger(__name__)


@shared_task
def send_sms_task(
    message: str, phone_numbers: List[str], otp_type: Optional[str] = None
):
    """
    Celery task for sending SMS messages using simple routing - no retries.

    Uses SMS Router to automatically route messages based on country codes:
    - Saudi Arabia (+966) → Neons SMS service
    - All other international numbers → Twilio SMS service

    Args:
        message: SMS message content
        phone_numbers: List of phone numbers to send to
        otp_type: Type of OTP (for logging purposes)

    Returns:
        dict: Result with success status and details
    """
    try:
        logger.info(
            f"SMS task started. Type: {otp_type}, Recipients: {len(phone_numbers)}"
        )

        router_status = sms_router.get_routing_status()
        available_services = [
            service
            for service, status in router_status["services"].items()
            if status.get("status") not in ["disabled", "unhealthy"]
        ]

        if not available_services:
            error_msg = "No SMS services are available. Please check SMS service configurations."
            logger.error(f"SMS task failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
            }

        results = []
        success_count = 0

        for phone_number in phone_numbers:
            if not phone_number:
                logger.warning("Skipping empty phone number")
                continue

            try:
                result = sms_router.send_sms(phone_number, message)

                result_dict = {
                    "phone_number": phone_number,
                    "success": result.success,
                    "error": result.error,
                    "service_used": result.service_used,
                    "message_id": result.message_id,
                }

                results.append(result_dict)

                if result.success:
                    success_count += 1
                    logger.info(
                        f"Successfully sent SMS to {phone_number} via {result.service_used}"
                    )
                else:
                    error_detail = result.error or "Unknown error"
                    logger.warning(
                        f"Failed to send SMS to {phone_number} via {result.service_used}: {error_detail}"
                    )

            except Exception as e:
                error_msg = f"Exception sending SMS to {phone_number}: {str(e)}"
                logger.error(error_msg)
                results.append(
                    {"phone_number": phone_number, "success": False, "error": error_msg}
                )

        total_numbers = len([num for num in phone_numbers if num])
        overall_success = success_count > 0

        if overall_success:
            logger.info(f"SMS task completed: {success_count}/{total_numbers} successful")
            return {
                "success": True,
                "results": results,
                "success_count": success_count,
                "total_count": total_numbers,
            }
        else:
            error_msg = f"All SMS sends failed ({total_numbers} numbers)"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "results": results,
                "success_count": success_count,
                "total_count": total_numbers,
            }

    except Exception as e:
        error_msg = f"Unexpected error in SMS task: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg,
        }


@shared_task
def send_bulk_sms_task(messages_data: List[dict]):
    """
    Celery task for sending bulk SMS messages.

    Args:
        messages_data: List of dicts with 'phone_number', 'message', and optional 'otp_type'

    Returns:
        dict: Bulk operation results
    """
    try:
        logger.info(f"Bulk SMS task started: {len(messages_data)} messages")

        results = []
        success_count = 0

        for msg_data in messages_data:
            phone_number = msg_data.get("phone_number")
            message = msg_data.get("message")
            otp_type = msg_data.get("otp_type", "bulk")

            if not phone_number or not message:
                logger.warning(f"Skipping invalid message data: {msg_data}")
                continue

            result = send_sms_task.apply_async(
                args=[message, [phone_number], otp_type], retry=False
            ).get()

            results.append(
                {"phone_number": phone_number, "otp_type": otp_type, "result": result}
            )

            if result.get("success"):
                success_count += 1

        logger.info(
            f"Bulk SMS task completed: {success_count}/{len(messages_data)} successful"
        )

        return {
            "success": success_count > 0,
            "results": results,
            "success_count": success_count,
            "total_count": len(messages_data),
        }

    except Exception as e:
        error_msg = f"Unexpected error in bulk SMS task: {str(e)}"
        logger.error(error_msg, exc_info=True)

        return {
            "success": False,
            "error": error_msg,
        }


@shared_task
def send_sms_task_legacy(message, phone_numbers):
    """
    Legacy Celery task for backward compatibility.
    Redirects to the new send_sms_task.
    """
    logger.warning(
        "Legacy send_sms_task_legacy called - redirecting to new send_sms_task"
    )
    return send_sms_task.delay(message, phone_numbers, "legacy").get()
