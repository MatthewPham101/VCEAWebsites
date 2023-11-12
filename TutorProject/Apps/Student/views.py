from django.shortcuts import render
from Apps.TutorApp.models import Tutor, Major, CustomUser
from django.db.models import Q
from .forms import TutorRatingForm
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from Apps.TutorApp.models import TutoringSession
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.core.signing import TimestampSigner, BadSignature
from django.http import HttpResponse
from Apps.TutorApp.forms import FeedbackForm
from Apps.TutorApp.models import Feedback

def student_view(request):
    # Get all majors for the filter dropdown
    majors = Major.objects.all()

    # Get query parameters for major and search
    major_name = request.GET.get('major')
    search_query = request.GET.get('search')

    # Start with all tutors
    tutors = Tutor.objects.all()

    # Filter by major if major name is selected
    # Note: This assumes your Major model has a 'name' field that stores the name of the major
    if major_name:
        tutors = tutors.filter(major__name=major_name)  # Filter by the name field of the Major model

    # Search by tutor's name or other fields if search query is provided
    if search_query:
        tutors = tutors.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )

    context = {
        'tutors': tutors,
        'majors': majors,
        # No need to convert to int, since we are now using the major name
        'selected_major': major_name,
        'search_query': search_query,
    }
    return render(request, 'studentPage.html', context)



def rate_tutor(request, tutor_id):
    tutor = get_object_or_404(Tutor, id=tutor_id)
    if request.method == 'POST':
        form = TutorRatingForm(request.POST, instance=tutor)  # Pass the tutor instance to the form
        if form.is_valid():
            form.save()
            return redirect('Student:student_view')  # Redirect to a success page or the tutor list
    else:
        form = TutorRatingForm(instance=tutor)  # Initialize the form with the tutor instance
    return render(request, 'rateTutor.html', {'form': form, 'tutor': tutor})


def student_view_tutors(request, tutor_id):
    tutor = get_object_or_404(Tutor, id=tutor_id)
    available_appointments = TutoringSession.objects.filter(tutor=tutor, student = None)
    return render(request, 'tutor_available_appointments.html', {'tutor': tutor, 'available_appointments': available_appointments})

from Apps.TutorApp.forms import AppointmentForm

def book_appointment(request, appointment_id):
    appointment = get_object_or_404(TutoringSession, id=appointment_id)

    if request.method == 'POST':
        form = AppointmentForm(appointment.tutor, request.POST, instance=appointment)
        if form.is_valid():
            theclass = form.cleaned_data['tutored_class']
            appointment.tutored_class = theclass
            appointment.student = request.user.student
            appointment.save()
            send_email(appointment)
            return redirect('Student:student_view_appointments', appointment.student.id)
    else:
        form = AppointmentForm(appointment.tutor, instance=appointment)

    return render(request, 'book_appointment.html', {'form': form, 'tutor': appointment.tutor})


    
def student_view_appointments(request, student_id):
    student = CustomUser.objects.get(pk=request.user.pk).student
    appointments = TutoringSession.objects.filter(student=student)
    return render(request, 'student_appointments.html', {'appointments': appointments, 'student': student})


def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(TutoringSession, id=appointment_id)
    student = appointment.student
    appointment.student = None
    appointment.save()
    return redirect('Student:student_view_appointments', student.id)

def send_email(appointment):
    subject = 'Your Appointment'
    message = render_to_string('appointment_email_template.txt', {'appointment': appointment})
    from_email = 'trentondb0303@gmail.com'
    recipient_list = [appointment.student.user.email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


def rate_tutor(request, signed_token):
    try:
        signer = TimestampSigner()
        data = signer.unsign(signed_token, max_age=60*60*24)
        tutor_id = int(data.split("_")[-1])

        tutor = get_object_or_404(Tutor, id=tutor_id)

        if request.method == 'POST':
            form = FeedbackForm(request.POST)
            if form.is_valid():
                feedback = Feedback(tutor=tutor, rating=form.cleaned_data['rating'], feedback=form.cleaned_data['feedback'])
                feedback.save()
                tutor.compute_rating()
                return HttpResponse("Thanks For Your Feedback!")
        else:
            form = FeedbackForm()

        return render(request, 'feedback_form.html', {'form': form, 'tutor': tutor})

    except BadSignature:
        return HttpResponse("Link Has Expired.")