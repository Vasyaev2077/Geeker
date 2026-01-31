from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from django.http import Http404, JsonResponse
from django.views.generic import DetailView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views import View

from .models import (
    UserProfile,
    ProfilePost,
    ProfilePostComment,
    ProfilePostMedia,
    ProfilePostVote,
)
from .forms import UserProfileForm, ProfilePostForm


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = "profiles/profile_detail.html"

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"display_name": self.request.user.username},
        )
        return profile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        posts_qs = (
            ProfilePost.objects.filter(author=self.request.user, is_deleted=False)
            .annotate(vote_score=Coalesce(Sum("votes__value"), 0))
            .annotate(
                comments_count=Count("comments", filter=Q(comments__is_deleted=False), distinct=True)
            )
            .prefetch_related("media_items")
            .prefetch_related(
                Prefetch(
                    "votes",
                    queryset=ProfilePostVote.objects.filter(user=self.request.user),
                    to_attr="current_user_votes",
                )
            )
            # Ensure newest posts are always above older ones (stable ordering).
            .order_by("-is_pinned", "-created_at", "-id")
        )
        paginator = Paginator(posts_qs, 10)
        page_number = self.request.GET.get("page") or 1
        page_obj = paginator.get_page(page_number)
        ctx["page_obj"] = page_obj
        ctx["is_paginated"] = page_obj.has_other_pages()
        ctx["posts"] = page_obj.object_list
        ctx["post_form"] = ProfilePostForm()
        return ctx


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = "profiles/profile_form.html"
    success_url = reverse_lazy("profiles:detail")

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"display_name": self.request.user.username},
        )
        return profile


class ProfileSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "profiles/settings.html"


class ProfilePostCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = ProfilePostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            images = request.FILES.getlist("media")[:8]
            for idx, img in enumerate(images):
                ProfilePostMedia.objects.create(post=post, file=img, position=idx)
        return redirect("profiles:detail")


class ProfilePostUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        post = ProfilePost.objects.filter(pk=pk, author=request.user, is_deleted=False).first()
        if not post:
            raise Http404
        form = ProfilePostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            # Handle deleting existing images (from modal UI)
            raw_deleted = (request.POST.get("deleted_media_ids") or "").strip()
            if raw_deleted:
                ids = []
                for part in raw_deleted.split(","):
                    part = part.strip()
                    if part.isdigit():
                        ids.append(int(part))
                if ids:
                    ProfilePostMedia.objects.filter(post=post, id__in=ids).delete()

            # Re-pack positions after deletions
            remaining_media = list(post.media_items.all().order_by("position", "created_at"))
            for idx, m in enumerate(remaining_media):
                if m.position != idx:
                    m.position = idx
                    m.save(update_fields=["position"])

            # Add new images on edit (up to 8 total)
            existing = len(remaining_media)
            remaining_slots = max(0, 8 - existing)
            if remaining_slots:
                new_images = request.FILES.getlist("media")[:remaining_slots]
                for i, img in enumerate(new_images):
                    ProfilePostMedia.objects.create(post=post, file=img, position=existing + i)
        return redirect("profiles:detail")


class ProfilePostTogglePinView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        post = ProfilePost.objects.filter(pk=pk, author=request.user, is_deleted=False).first()
        if not post:
            raise Http404
        new_value = not post.is_pinned
        if new_value:
            ProfilePost.objects.filter(author=request.user, is_deleted=False, is_pinned=True).update(
                is_pinned=False
            )
        post.is_pinned = new_value
        post.save(update_fields=["is_pinned"])
        return redirect("profiles:detail")


class ProfilePostToggleCommentsView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        post = ProfilePost.objects.filter(pk=pk, author=request.user, is_deleted=False).first()
        if not post:
            raise Http404
        post.comments_enabled = not post.comments_enabled
        post.save(update_fields=["comments_enabled"])
        return redirect("profiles:detail")


class ProfilePostDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        post = ProfilePost.objects.filter(pk=pk, author=request.user, is_deleted=False).first()
        if not post:
            raise Http404
        post.is_deleted = True
        post.save(update_fields=["is_deleted"])
        return redirect("profiles:detail")


class ProfilePostVoteView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        post = ProfilePost.objects.filter(pk=pk, author=request.user, is_deleted=False).first()
        if not post:
            raise Http404
        try:
            value = int(request.POST.get("value"))
        except (TypeError, ValueError):
            return redirect("profiles:detail")
        if value not in (-1, 1):
            return redirect("profiles:detail")

        vote = ProfilePostVote.objects.filter(post=post, user=request.user).first()
        if vote and vote.value == value:
            vote.delete()
        elif vote:
            vote.value = value
            vote.save(update_fields=["value"])
        else:
            ProfilePostVote.objects.create(post=post, user=request.user, value=value)

        wants_json = (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or "application/json" in (request.headers.get("accept") or "")
        )
        if wants_json:
            score = (
                ProfilePostVote.objects.filter(post=post).aggregate(s=Coalesce(Sum("value"), 0)).get("s")
                or 0
            )
            current = ProfilePostVote.objects.filter(post=post, user=request.user).values_list("value", flat=True).first()
            return JsonResponse({"ok": True, "score": int(score), "user_vote": current or 0})

        return redirect("profiles:detail")


class ProfilePostCommentCreateView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        post = ProfilePost.objects.filter(pk=pk, author=request.user, is_deleted=False).first()
        if not post:
            raise Http404
        if not post.comments_enabled:
            return redirect("profiles:detail")
        text = (request.POST.get("text") or "").strip()
        if text:
            ProfilePostComment.objects.create(post=post, author=request.user, text=text[:2000])
        return redirect("profiles:detail")






