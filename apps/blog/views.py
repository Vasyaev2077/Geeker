from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import BlogPost


class BlogListView(LoginRequiredMixin, ListView):
    model = BlogPost
    template_name = "blog/post_list.html"
    paginate_by = 10

    def get_queryset(self):
        return (
            BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)
            .select_related("author")
            .prefetch_related("tags")
        )


class BlogDetailView(LoginRequiredMixin, DetailView):
    model = BlogPost
    template_name = "blog/post_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).select_related(
            "author"
        )








