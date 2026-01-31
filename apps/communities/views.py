from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.db.models import Count
from django.shortcuts import redirect
from .models import Community


class CommunityListView(LoginRequiredMixin, ListView):
    model = Community
    template_name = "communities/community_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Community.objects.filter(visibility=Community.Visibility.PUBLIC)
            .annotate(members_count=Count("members", distinct=True))
            .select_related("owner")
        )
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs.order_by("-members_count", "name", "id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        ctx["sidebar_top"] = list(self.get_queryset()[:20])
        ctx["sidebar_mine"] = list(self.request.user.communities.all().order_by("name")[:20])
        return ctx


class CommunityDetailView(LoginRequiredMixin, DetailView):
    model = Community
    template_name = "communities/community_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Community.objects.select_related("owner")
            .annotate(members_count=Count("members", distinct=True))
            .prefetch_related("members")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["sidebar_top"] = list(
            Community.objects.filter(visibility=Community.Visibility.PUBLIC)
            .annotate(members_count=Count("members", distinct=True))
            .order_by("-members_count", "name", "id")[:20]
        )
        ctx["sidebar_mine"] = list(self.request.user.communities.all().order_by("name")[:20])
        ctx["is_member"] = self.object.members.filter(id=self.request.user.id).exists()
        return ctx


class CommunityJoinToggleView(LoginRequiredMixin, View):
    def post(self, request, slug: str):
        community = (
            Community.objects.filter(slug=slug, visibility=Community.Visibility.PUBLIC)
            .prefetch_related("members")
            .first()
        )
        if not community:
            return redirect("communities:community_list")

        if community.members.filter(id=request.user.id).exists():
            community.members.remove(request.user)
        else:
            community.members.add(request.user)

        return redirect("communities:community_detail", slug=slug)








