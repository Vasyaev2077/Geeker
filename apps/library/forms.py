from django import forms

from .models import Section, Collection, Item


class SectionForm(forms.ModelForm):
    name = forms.CharField(label="Название раздела", required=True)

    class Meta:
        model = Section
        fields = ["name", "description", "cover"]
        labels = {
            "name": "Название",
            "description": "Описание (что это за раздел)",
            "cover": "Обложка",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "maxlength": "50"}),
            # Use plain FileInput so Django doesn't render "currently/clear" block
            "cover": forms.FileInput(),
        }


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
        fields = ["title", "description", "sections", "tags"]
        labels = {
            "title": "Название предмета",
            "description": "Описание",
            "sections": "Разделы",
            "tags": "Теги",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "sections": forms.SelectMultiple(attrs={"size": 1}),
        }


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["collection", "title", "description", "sections", "tags", "metadata"]
        labels = {
            "collection": "Коллекция",
            "title": "Название",
            "description": "Описание",
            "sections": "Разделы",
            "tags": "Теги",
            "metadata": "",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "sections": forms.SelectMultiple(attrs={"size": 1}),
            "metadata": forms.HiddenInput(attrs={"data-metadata-json": "1"}),
        }