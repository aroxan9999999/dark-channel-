from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponseForbidden
from .forms import UserProfileForm, CertificationForm, LanguageForm
from Services.models import Overview, Category
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from .models import UserProfile, Certification, Language, RatingSeller
from django.forms import inlineformset_factory

def IntroHome(request):
    if request.user.is_authenticated:
        username = request.user.username
        return redirect('home', username)
    else:
        return render(request, 'index.html')


@login_required()  # Requiring login for access
def home(request, identifier):
    user = get_object_or_404(User, username=identifier)  # Getting the user object
    users = User.objects.all()
    usernames = [user.username for user in users]
    user_id = [user.id for user in users]
    user_profile = UserProfile.objects.all()
    user_service_profiles = Overview.objects.all()
    user_profile_change, created = UserProfile.objects.get_or_create(user=user)

    category = Category.objects.all()
    current_user = request.user
    if identifier == current_user.username:
        pass
    else:
        return HttpResponseForbidden("Access Denied")

    context = {
        'user': user,
        'user_id': user_id,
        'usernames': usernames,
        'user_profile': user_profile,
        'user_service_profiles': user_service_profiles,
        'category': category,
    }
    return render(request, 'home.html', context)



@login_required()  # Requiring login for access
def edit_profile(request, identifier):
    user = get_object_or_404(User, username=identifier)  # Getting the user object
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    # Initialize context with common values
    current_user = request.user
    if identifier == current_user.username:
        pass
    else:
        return HttpResponseForbidden("Access Denied")

    context = {
        'user': user,
        'user_profile': user_profile,
    }

    if request.user != user:
        raise PermissionDenied("You are not authorized to edit this profile.")



    user_form = UserProfileForm(request.POST or None, request.FILES or None, instance=user_profile)
    CertificationFormSet = inlineformset_factory(UserProfile, Certification, form=CertificationForm, extra=1)
    certification_queryset = Certification.objects.filter(user_profile=user_profile)
    certification_formset = CertificationFormSet(request.POST or None, instance=user_profile, prefix='certifications', queryset=certification_queryset)
    LanguageFormSet = inlineformset_factory(UserProfile, Language, form=LanguageForm, extra=1)
    language_queryset = Language.objects.filter(user_profile=user_profile)
    language_formset = LanguageFormSet(request.POST or None, instance=user_profile, prefix='languages', queryset=language_queryset)

    username_taken = False
    email_taken = False
    if request.method == 'POST':
        new_username = request.POST['username']
        new_email = request.POST['email']

        username_taken = User.objects.filter(username=new_username).exclude(pk=user.pk).exists()
        email_taken = User.objects.filter(email=new_email).exclude(pk=user.pk).exists()

        if username_taken or email_taken:
            if username_taken:
                context['username_message'] = "Username is already taken. Please choose another."
            if email_taken:
                context['email_message'] = "Email is already taken. Please choose another."
        else:
            user.username = new_username
            user.email = new_email
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.save()

            if user_form.is_valid() and certification_formset.is_valid() and language_formset.is_valid():
                user_form.save()

                for form in certification_formset.deleted_forms:
                    if form.cleaned_data.get('id'):
                        form.instance.delete()

                for form in language_formset.deleted_forms:
                    if form.cleaned_data.get('id'):
                        form.instance.delete()

                for form in certification_formset:
                    if form.is_valid() and not form.cleaned_data.get('id'):
                        certification = form.save(commit=False)
                        if certification.title and certification.issuing_organization:
                            certification.user_profile = user_profile
                            certification.save()

                for form in language_formset:
                    if form.is_valid() and not form.cleaned_data.get('id'):
                        language = form.save(commit=False)
                        if language.language and language.proficiency:
                            language.user_profile = user_profile
                            language.save()

                return redirect('IntroHome')

    context.update({
        'user_form': user_form,
        'certification_formset': certification_formset,
        'language_formset': language_formset,
        'username_taken': username_taken,
        'email_taken': email_taken,
    })
    return render(request, 'edit_profile.html', context)


@login_required()  # Requiring login for access
def view_profile_public(request, username):
    user = get_object_or_404(User, username=username)  # Getting the user object
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    user_service_profiles = Overview.objects.filter(user=user)
    seller_profile, created = UserProfile.objects.get_or_create(user=user_profile.user)
    u, created = UserProfile.objects.get_or_create(user=request.user)
    re_profile = UserProfile.objects.get(user=request.user)


    profile_reviews = RatingSeller.objects.filter(seller=seller_profile)
    total_review_sum = sum(review.review_rating for review in profile_reviews)
    reviewer_profile_usr = [review.reviewer.user for review in profile_reviews]
    user_profile.overall_rating = round(total_review_sum / profile_reviews.count()) if profile_reviews.count() > 0 else 0
    user_profile.save()


    if request.method == 'POST':
        rating_value = request.POST.get('rg1')
        title = request.POST.get('review_title')
        review_text = request.POST.get('review_message')
        existing_review = RatingSeller.objects.filter(seller=seller_profile, reviewer=re_profile).first()

        if existing_review:
            existing_review.review_rating = rating_value
            existing_review.title = title
            existing_review.review = review_text
            existing_review.save()
        else:
            RatingSeller.objects.create(
                seller=seller_profile,
                reviewer=re_profile,
                review_rating=rating_value,
                title=title,
                review=review_text
            )

    context = {
        'user_profile': user_profile,
        'user_service_profiles': user_service_profiles,
        'profile_reviews': profile_reviews,
        'count_review': profile_reviews.count(),
        'reviewer_profile_usr': reviewer_profile_usr,
    }

    return render(request, 'view_profile_public.html', context)
