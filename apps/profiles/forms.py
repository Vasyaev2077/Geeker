from django import forms

from .models import UserProfile


class UserProfileForm(forms.ModelForm):
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
            "bio": forms.Textarea(attrs={"rows": 3}),
        }



