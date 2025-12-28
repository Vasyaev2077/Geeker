from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from .models import Community


class CommunityListView(LoginRequiredMixin, ListView):
    model = Community
    template_name = "communities/community_list.html"
    paginate_by = 20

    def get_queryset(self):
        return Community.objects.filter(visibility=Community.Visibility.PUBLIC)


class CommunityDetailView(LoginRequiredMixin, DetailView):
    model = Community
    template_name = "communities/community_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"








