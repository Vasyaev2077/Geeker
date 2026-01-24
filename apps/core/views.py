from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class HomeMenuView(LoginRequiredMixin, TemplateView):
    """
    Домашняя страница с крупными кнопками разделов,
    как в макете из Figma.
    """

    template_name = "home/home.html"




