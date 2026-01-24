from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from .models import Chat


class ChatListView(LoginRequiredMixin, ListView):
    model = Chat
    template_name = "chat/chat_list.html"

    def get_queryset(self):
        return Chat.objects.filter(participants=self.request.user)


class ChatDetailView(LoginRequiredMixin, DetailView):
    model = Chat
    template_name = "chat/chat_detail.html"

    def get_queryset(self):
        return Chat.objects.filter(participants=self.request.user)








