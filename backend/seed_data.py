import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.candidates.models import Candidate
from apps.messages_comm.models import Message, MessageRecipient

IST = ZoneInfo("Asia/Kolkata")


def run_seed():
    print("Clearing existing candidate and message records for fresh seed...")
    Candidate.objects.all().delete()
    Message.objects.all().delete()
    MessageRecipient.objects.all().delete()

    figma_candidates = [
        {
            "candidate_id": "A1B2C3",
            "name": "Krishna Khandelwal",
            "phone": "+919876543210",
            "email": "krishna.khandelwal@gmail.com",
            "status": "read",
            "date_str": "12-10-2026 10:30",
            "text": "Great ideas often begin with simple observations. Creativity grows when we explore new perspectives and challenge familiar ways of thinking.",
        },
        {
            "candidate_id": "D4E5F6",
            "name": "Urvashi Soni",
            "phone": "+919123456789",
            "email": "urvashi.soni@gmail.com",
            "status": "failed",
            "date_str": "15-10-2026 14:15",
            "text": "Your interview has been scheduled for tomorrow at 2:00 PM.",
            "error_code": "delivery_failed",
            "friendly_message": "The message couldn't be delivered to the recipient.",
            "retryable": False,
        },
        {
            "candidate_id": "G7H8I9",
            "name": "Aditya Kumar",
            "phone": "+919988766554",
            "email": "aditya.kumar@gmail.com",
            "status": "read",
            "date_str": "18-10-2026 11:00",
            "text": "Hello Aditya, welcome to the recruitment process at Hunar.ai.",
        },
        {
            "candidate_id": "J1K2L3",
            "name": "Ajit Srivastava",
            "phone": "+919234567890",
            "email": "ajit.srivastava@gmail.com",
            "status": "read",
            "date_str": "21-10-2026 16:45",
            "text": "Please confirm your availability for the technical round.",
        },
        {
            "candidate_id": "M4N5O6",
            "name": "Aniket Sawant",
            "phone": "+919876512345",
            "email": "aniket.sawant@gmail.com",
            "status": "sent",
            "date_str": "24-10-2026 09:15",
            "text": "We have received your application and will review it shortly.",
        },
        {
            "candidate_id": "P7Q8R9",
            "name": "Ira Akbar",
            "phone": "+919456789012",
            "email": "ira.akbar@gmail.com",
            "status": None,
        },
        {
            "candidate_id": "S1T2U3",
            "name": "Amarjeet Kumar",
            "phone": "+919012345678",
            "email": "amarjeet.kumar@gmail.com",
            "status": None,
        },
    ]

    deterministic_test_candidates = [
        {
            "candidate_id": "T0E000",
            "name": "Vikram Test-Invalid",
            "phone": "+919876500000",
            "email": "vikram.0000@test.com",
            "status": None,
        },
        {
            "candidate_id": "T0E429",
            "name": "Priya Test-RateLimit",
            "phone": "+919876500429",
            "email": "priya.0429@test.com",
            "status": None,
        },
        {
            "candidate_id": "T0E503",
            "name": "Rohan Test-TempFail",
            "phone": "+919876500503",
            "email": "rohan.0503@test.com",
            "status": None,
        },
        {
            "candidate_id": "T0E500",
            "name": "Neha Test-DeliveryFail",
            "phone": "+919876500500",
            "email": "neha.0500@test.com",
            "status": None,
        },
    ]

    overflow_names = [
        "Aarav Patel", "Diya Sharma", "Kabir Mehta", "Ananya Verma",
        "Ishaan Gupta", "Meera Joshi", "Vihaan Singh", "Tanvi Rao",
        "Reyansh Nair", "Kavya Deshmukh", "Shaurya Kapoor", "Avani Bhat",
        "Dhruv Malhotra", "Myra Kulkarni", "Advait Choudhury", "Saanvi Reddy",
        "Atharv Pillai", "Zoya Khan", "Devansh Sen", "Kiara Saxena",
        "Samarth Bose", "Riya Das"
    ]

    overflow_candidates = []
    for i, name in enumerate(overflow_names, start=1):
        clean_name_parts = name.lower().split()
        cand_id = f"OV{i:02d}X9"
        overflow_candidates.append({
            "candidate_id": cand_id,
            "name": name,
            "phone": f"+9198761{i:05d}",
            "email": f"{clean_name_parts[0]}.{clean_name_parts[1]}@test.com",
            "status": None,
        })

    all_to_seed = figma_candidates + deterministic_test_candidates + overflow_candidates

    created_count = 0
    for data in all_to_seed:
        cand = Candidate.objects.create(
            candidate_id=data["candidate_id"],
            name=data["name"],
            phone=data["phone"],
            email=data["email"],
            is_deleted=False
        )
        created_count += 1

        # Seed initial message if specified
        if data.get("status"):
            dt = datetime.strptime(data["date_str"], "%d-%m-%Y %H:%M").replace(tzinfo=IST)
            msg = Message.objects.create(
                body=data["text"],
                created_at=dt
            )
            MessageRecipient.objects.create(
                message=msg,
                candidate=cand,
                status=data["status"],
                error_code=data.get("error_code"),
                friendly_message=data.get("friendly_message"),
                retryable=data.get("retryable", False),
                created_at=dt,
                read_at=dt if data["status"] == "read" else None,
                failed_at=dt if data["status"] == "failed" else None,
                sent_at=dt if data["status"] in ["sent", "read", "failed"] else None,
            )

    print(f"SUCCESS: Seeded {created_count} candidates into MongoDB Atlas.")


if __name__ == "__main__":
    run_seed()
