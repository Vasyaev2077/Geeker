from django import forms

from .models import UserProfile, ProfilePost


class UserProfileForm(forms.ModelForm):
    bio = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": 200}),
    )

    class Meta:
        model = UserProfile
        fields = ["display_name", "avatar", "bio", "language", "timezone"]
        labels = {
            "display_name": "Имя",
            "avatar": "Аватар",
            "bio": "Bio",
            "language": "Язык интерфейса",
            "timezone": "Часовой пояс",
        }
        widgets = {
            # Use plain FileInput to avoid "current file / clear / change" block in UI.
            "avatar": forms.FileInput(attrs={"accept": "image/*"}),
        }


class ProfilePostForm(forms.ModelForm):
    class Meta:
        model = ProfilePost
        # Media is handled separately as multiple images (up to 8) via ProfilePostMedia.
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Напишите что-нибудь...",
                }
            ),
        }



