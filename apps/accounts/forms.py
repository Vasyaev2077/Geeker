from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q

User = get_user_model()


class LocalUserCreationForm(UserCreationForm):
    """
    Local-friendly registration form that collects email so password reset works.
    """

    email = forms.EmailField(required=True, label="Email")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LocalPasswordResetForm(PasswordResetForm):
    """
    Allow resetting password locally by entering either email OR username.

    Also supports users with empty email by sending the reset message to a
    dummy local recipient so the console email backend still prints the link.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Reuse the built-in "email" field name so PasswordResetView works,
        # but accept username too.
        self.fields["email"] = forms.CharField(
            label="Email или имя пользователя",
            widget=forms.TextInput(attrs={"autocomplete": "username email"}),
        )

    def get_users(self, email: str):
        identifier = (email or "").strip()
        if not identifier:
            return []
        # Keep behavior similar to Django: only active users.
        qs = User._default_manager.filter(is_active=True).filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier)
        )
        return qs.iterator()

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        # If user has no email, still print link to console/backend by using a dummy local recipient.
        if not to_email:
            to_email = "local@localhost"

        subject = self.render_mail_subject(subject_template_name, context)
        body = self.render_mail_body(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_body = self.render_mail_body(html_email_template_name, context)
            email_message.attach_alternative(html_body, "text/html")
        email_message.send()

    @staticmethod
    def render_mail_subject(subject_template_name, context) -> str:
        from django.template.loader import render_to_string

        return render_to_string(subject_template_name, context).strip().replace("\n", "")

    @staticmethod
    def render_mail_body(email_template_name, context) -> str:
        from django.template.loader import render_to_string

        return render_to_string(email_template_name, context)

