from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from transformers import pipeline

router = APIRouter()

# Load the DeepSeek LLM for text generation
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
    device=0  # Use GPU
)

CANDIDATE_LABELS = [
    "Job Rejection",
    "Job Offer",
    "Job Online Assessment",
    "Recruiter Call",
    "Non Job Related",
]

FEW_SHOT_PROMPT = '''You are an email classifier. Classify each email as one of: Job Application, Job Rejection, Job Offer, Job Online Assessment, Recruiter Call, Non Job Related.
Here are some examples:

Email:
From: Sarah Lee <sarah.lee@gmail.com>
Subject: Application for Data Scientist
Body: I am excited to submit my application for the Data Scientist position at Acme Corp. Please find my resume attached.
Label: Job Application

Email:
From: Michael Brown <michael.brown@yahoo.com>
Subject: Resume Submission
Body: Attached is my resume for the Software Developer opening. Looking forward to hearing from you.
Label: Job Application

Email:
From: HR Team <hr@bigcompany.com>
Subject: Application Status Update
Body: Thank you for your interest in the Marketing Analyst role. Unfortunately, we have decided not to move forward with your application.
Label: Job Rejection

Email:
From: Talent Acquisition <talent@startup.com>
Subject: Your Application with Us
Body: We appreciate your application, but we will not be proceeding with your candidacy at this time.
Label: Job Rejection

Email:
From: HR <hr@fintech.com>
Subject: Offer Letter for Product Manager
Body: Congratulations! We are pleased to offer you the position of Product Manager at FinTech Solutions.
Label: Job Offer

Email:
From: People Operations <people@edutech.com>
Subject: Job Offer
Body: We are excited to extend you a job offer for the UX Designer role. Please see the attached offer letter.
Label: Job Offer

Email:
From: Assessments <assess@company.com>
Subject: Online Assessment Invitation
Body: As part of your application, please complete the online assessment using the link below.
Label: Job Online Assessment

Email:
From: HR <hr@consulting.com>
Subject: Assessment Test Required
Body: Please take the online test to continue your application process for the Consultant position.
Label: Job Online Assessment

Email:
From: Recruiter <recruiter@agency.com>
Subject: Schedule a Call
Body: I would like to schedule a call to discuss your background and the open position.
Label: Recruiter Call

Email:
From: Talent Scout <scout@company.com>
Subject: Phone Interview Request
Body: Can we arrange a phone interview to talk about your experience and the role?
Label: Recruiter Call

Email:
From: Amazon <no-reply@amazon.com>
Subject: Your Order Has Shipped
Body: Your order #12345 has shipped and is on its way to you.
Label: Non Job Related

Email:
From: Netflix <info@netflix.com>
Subject: New Arrivals This Month
Body: Check out the latest movies and shows added to our platform.
Label: Non Job Related

'''

class EmailInput(BaseModel):
    subject: str
    snippet: str
    sender: str

class ClassifyRequest(BaseModel):
    emails: List[EmailInput]

@router.post("/classify")
def classify_emails(request: ClassifyRequest):
    results = []
    for email in request.emails:
        text = f"From: {email.sender}\nSubject: {email.subject}\nBody: {email.snippet}"
        result = classifier(text, CANDIDATE_LABELS)
        label = result['labels'][0]  # Top predicted label
        results.append({
            "subject": email.subject,
            "snippet": email.snippet,
            "sender": email.sender,
            "predicted_label": label,
            "scores": dict(zip(result['labels'], result['scores'])),
        })
    return {"results": results} 