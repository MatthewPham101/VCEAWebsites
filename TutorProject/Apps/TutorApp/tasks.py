from background_task import background
from datetime import time
from Apps.TutorApp.models import Tutor

@background(schedule=20)  # Schedule the task to run every 60 seconds
def my_scheduled_task():
    for tutor in Tutor.objects.all():
        tutor.create_appointments()
    print("Created Appointments")