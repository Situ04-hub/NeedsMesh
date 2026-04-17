from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile, CommunityProblem, Locality, Organisation, CATEGORY_CHOICES, URGENCY_CHOICES, ROLE_CHOICES


# ---------------------------------------------------------------------------
# Registration Form
# ---------------------------------------------------------------------------
class RegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unique Username (for login)'})
    )
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'role-select'})
    )
    # Dynamic fields (initially optional)
    ngo_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NGO Name'})
    )
    locality = forms.ModelChoiceField(
        queryset=Locality.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ChoiceField(
        choices=[('', 'Select Category')] + CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # Organization Logic
    organisation_name = forms.CharField(
        max_length=200,
        required=False,
        label="New Organisation Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Hope Foundation'})
    )
    organisation_choice = forms.ModelChoiceField(
        queryset=Organisation.objects.all(),
        required=False,
        label="Select Existing Organisation",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Whisper of this username already exists in our network. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_organisation_name(self):
        role = self.cleaned_data.get('role')
        name = self.cleaned_data.get('organisation_name')
        if role == 'admin' and name:
            if Organisation.objects.filter(name=name).exists():
                raise forms.ValidationError("This Organisation already exists. Please choose a unique name or join an existing one.")
        return name

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        role = cleaned.get('role')

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")

        # Role-specific requirements
        if role == 'admin':
            if not cleaned.get('organisation_name'):
                self.add_error('organisation_name', "Please provide a name for your NGO/Organisation.")

        elif role == 'field_worker':
            if not cleaned.get('organisation_choice'):
                self.add_error('organisation_choice', "Please select an NGO to join.")
            if not cleaned.get('locality'):
                self.add_error('locality', "Please select your primary mission locality.")

        elif role == 'volunteer':
            if not cleaned.get('category'):
                self.add_error('category', "Please select your expertise area.")
            if not cleaned.get('locality'):
                self.add_error('locality', "Please select your preferred locality.")

        return cleaned


# ---------------------------------------------------------------------------
# Login Form
# ---------------------------------------------------------------------------
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


# ---------------------------------------------------------------------------
# Profile Edit Form
# ---------------------------------------------------------------------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'locality', 'resume']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'locality': forms.Select(attrs={'class': 'form-select'}),
            'resume': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


# ---------------------------------------------------------------------------
# Survey / CommunityProblem Submission Form (for Field Workers)
# ---------------------------------------------------------------------------
class SurveyForm(forms.ModelForm):
    # Multi-select category
    categories = forms.MultipleChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'category-checkbox'}),
        label='Categories'
    )

    class Meta:
        model = CommunityProblem
        fields = ['locality', 'problem_statement', 'urgency', 'detected_date']
        widgets = {
            'locality': forms.Select(attrs={'class': 'form-select'}),
            'problem_statement': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Describe the community problem in detail...'
            }),
            'urgency': forms.Select(attrs={'class': 'form-select'}),
            'detected_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill categories from saved comma-sep string
        if self.instance.pk and self.instance.category:
            self.fields['categories'].initial = self.instance.get_category_list()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.category = ','.join(self.cleaned_data['categories'])
        if commit:
            instance.save()
        return instance


# ---------------------------------------------------------------------------
# Proof Image Upload Form (handled separately — multiple files)
# ---------------------------------------------------------------------------
class ProofImageForm(forms.Form):
    images = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        required=False,
        label='Proof Images (multiple allowed)'
    )


# ---------------------------------------------------------------------------
# Finalise Event Form (admin selects volunteers + event date)
# ---------------------------------------------------------------------------
class FinaliseEventForm(forms.ModelForm):
    class Meta:
        model = CommunityProblem
        fields = ['selected_volunteers', 'final_event_date']
        widgets = {
            'selected_volunteers': forms.CheckboxSelectMultiple(),
            'final_event_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show volunteers who expressed interest
        if self.instance.pk:
            self.fields['selected_volunteers'].queryset = self.instance.interested_volunteers.all()


# ---------------------------------------------------------------------------
# Resolve / Kill Form
# ---------------------------------------------------------------------------
class SetVolunteersRequiredForm(forms.ModelForm):
    class Meta:
        model = CommunityProblem
        fields = ['volunteers_required']
        widgets = {
            'volunteers_required': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class ResolveProblemForm(forms.ModelForm):
    class Meta:
        model = CommunityProblem
        fields = ['before_after', 'total_need', 'community_reaction', 'status']
        widgets = {
            'before_after': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'total_need': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'community_reaction': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                        'placeholder': 'Reactions, emojis, feedback...'}),
            'status': forms.Select(
                choices=[('resolved', 'Resolved'), ('killed', 'Killed')],
                attrs={'class': 'form-select'}
            ),
        }


class KillProblemForm(forms.ModelForm):
    class Meta:
        model = CommunityProblem
        fields = ['killed_reason']
        widgets = {
            'killed_reason': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Reason for killing this task...'
            }),
        }


# ---------------------------------------------------------------------------
# Locality Add Form
# ---------------------------------------------------------------------------
class LocalityForm(forms.ModelForm):
    class Meta:
        model = Locality
        fields = ['name', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
        }


# ---------------------------------------------------------------------------
# CSV Import Form (for localities/categories)
# ---------------------------------------------------------------------------
class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'}),
        label='Upload CSV file'
    )
