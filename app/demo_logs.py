"""Synthetic incidents for demos and development. No real customer data."""

import random


DEMO_LOGS = [
    {"id": "webhook-failure", "label": "Carrier webhook failure", "raw_text": "2026-08-01T11:18:04Z WEBHOOK_FAILURE Shipment ORD-77341 departed the Delhi hub, but the carrier webhook returned HTTP 500. The retry queue exhausted after five attempts. Customer tracking still shows Processing."},
    {"id": "scan-timeout", "label": "Warehouse scan timeout", "raw_text": "2026-08-01 09:42:16 ERROR Package PKG-88291 is stuck at the Hyderabad sorting hub. Barcode scanner returned SCAN_TIMEOUT after three retries. The shipment status has not changed for 14 hours and no alert was raised."},
    {"id": "delivery-dispute", "label": "Delivery dispute", "raw_text": "Shipment TRK-10452 was marked delivered in Mumbai, but the customer reports it was not received. Recorded GPS coordinates differ from the delivery address by 2.3 km, and the proof-of-delivery image is missing."},
    {"id": "damaged-package", "label": "Damaged package", "raw_text": "Customer ticket: Package AWB-55109 arrived damaged in Pune. The outer box was wet and crushed. The shipment record contains no damage exception before dispatch."},
    {"id": "weather-delay", "label": "Weather delay and notification failure", "raw_text": "Package 99124 is delayed at the Bangalore hub during heavy rain. The route-planning service returned NO_ALTERNATE_ROUTE and the customer notification webhook returned HTTP 429."},
]


def get_demo_logs() -> list[dict[str, str]]:
    return DEMO_LOGS


def generate_demo_log() -> dict[str, str]:
    return random.choice(DEMO_LOGS)
