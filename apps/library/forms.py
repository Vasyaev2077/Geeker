from django import forms

from .models import Section, Collection, Item


class SectionForm(forms.ModelForm):
    name = forms.CharField(label="Название раздела", required=False)

    class Meta:
        model = Section
        fields = ["name"]


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["title", "description", "visibility", "tags"]
        labels = {
            "title": "Название коллекции",
            "description": "Описание",
            "visibility": "Видимость",
            "tags": "",
        }


class ItemInlineForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["title", "description", "sections"]
        labels = {
            "title": "Название предмета",
            "description": "Описание",
            "sections": "Разделы",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "sections": forms.SelectMultiple(attrs={"size": 1}),
        }