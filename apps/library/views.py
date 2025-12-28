from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Collection, Item, Section
from .forms import SectionForm, CollectionForm, ItemInlineForm


class HomeView(LoginRequiredMixin, ListView):
    """
    Главная вкладка библиотеки: карточки предметов с фильтрами по разделам
    и поиском.
    """

    model = Item
    template_name = "library/home.html"
    context_object_name = "items"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        qs = (
            Item.objects.filter(collection__owner=user, collection__is_archived=False)
            .select_related("collection")
            .prefetch_related("media", "sections")
        )

        # Простой/расширенный поиск
        query = self.request.GET.get("q")
        if query:
            if self.request.GET.get("search_in_description") == "on":
                qs = qs.filter(description__icontains=query)
            else:
                qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

        # Фильтр по разделам (можно выбрать несколько)
        section_ids = self.request.GET.getlist("sections")
        if section_ids:
            qs = qs.filter(sections__id__in=section_ids).distinct()

        # Сортировка
        order = self.request.GET.get("order")
        if order == "recent":
            qs = qs.order_by("-created_at")
        elif order == "oldest":
            qs = qs.order_by("created_at")
        elif order == "az":
            qs = qs.order_by("title")
        elif order == "za":
            qs = qs.order_by("-title")

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["sections"] = Section.objects.filter(owner=user)
        ctx["selected_sections"] = [int(s) for s in self.request.GET.getlist("sections") if s.isdigit()]
        ctx["current_order"] = self.request.GET.get("order", "recent")
        ctx["query"] = self.request.GET.get("q", "")
        ctx["advanced"] = self.request.GET.get("advanced") == "on"
        return ctx


class CollectionListView(HomeView):
    template_name = "library/collection_list.html"


class CollectionDetailView(LoginRequiredMixin, DetailView):
    model = Collection
    template_name = "library/collection_detail.html"

    def get_queryset(self):
        return (
            Collection.objects.select_related("owner")
            .prefetch_related("items__media", "tags")
            .filter(owner=self.request.user)
        )


class CollectionCreateView(LoginRequiredMixin, CreateView):
    """
    Единая кнопка «Создать коллекцию»: создаёт (опционально) раздел,
    коллекцию и первый предмет с изображениями.
    """

    model = Collection
    form_class = CollectionForm
    template_name = "library/collection_form.html"
    success_url = reverse_lazy("library:home")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if "section_form" not in ctx:
            ctx["section_form"] = SectionForm(self.request.POST or None)
        if "item_form" not in ctx:
            ctx["item_form"] = ItemInlineForm(self.request.POST or None)
        ctx["has_sections"] = Section.objects.filter(owner=self.request.user).exists()
        ctx["sections"] = Section.objects.filter(owner=self.request.user)
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = None
        collection_form = self.get_form()
        section_form = SectionForm(request.POST)
        item_form = ItemInlineForm(request.POST)
        if collection_form.is_valid() and item_form.is_valid() and section_form.is_valid():
            return self.forms_valid(collection_form, section_form, item_form)
        return self.forms_invalid(collection_form, section_form, item_form)

    def forms_valid(self, collection_form, section_form, item_form):
        # Опционально создаём новый раздел
        new_section = None
        if section_form.cleaned_data.get("name"):
            new_section = section_form.save(commit=False)
            new_section.owner = self.request.user
            new_section.save()

        # Создаём коллекцию
        collection = collection_form.save(commit=False)
        collection.owner = self.request.user
        collection.save()
        collection_form.save_m2m()

        # Создаём первый предмет
        item = item_form.save(commit=False)
        item.collection = collection
        item.save()
        item_form.save_m2m()
        if new_section:
            item.sections.add(new_section)

        images = self.request.FILES.getlist("images")
        from .models import ItemMedia

        for idx, image in enumerate(images[:5]):
            ItemMedia.objects.create(
                item=item,
                file=image,
                type=ItemMedia.MediaType.IMAGE,
                is_primary=idx == 0,
                position=idx,
            )

        return super().form_valid(collection_form)

    def forms_invalid(self, collection_form, section_form, item_form):
        context = self.get_context_data(form=collection_form)
        context["section_form"] = section_form
        context["item_form"] = item_form
        return self.render_to_response(context)


class CollectionUpdateView(LoginRequiredMixin, UpdateView):
    model = Collection
    fields = ["title", "description", "visibility", "tags", "is_archived"]
    template_name = "library/collection_form.html"
    success_url = reverse_lazy("library:collection_list")

    def get_queryset(self):
        return Collection.objects.filter(owner=self.request.user)


class CollectionDeleteView(LoginRequiredMixin, DeleteView):
    model = Collection
    template_name = "library/collection_confirm_delete.html"
    success_url = reverse_lazy("library:collection_list")

    def get_queryset(self):
        return Collection.objects.filter(owner=self.request.user)


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = "library/item_detail.html"

    def get_queryset(self):
        return Item.objects.select_related("collection", "collection__owner").prefetch_related(
            "media", "tags"
        )


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    fields = ["collection", "title", "description", "sections"]
    template_name = "library/item_form.html"
    success_url = reverse_lazy("library:home")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["collection"].queryset = Collection.objects.filter(owner=self.request.user)
        form.fields["sections"].queryset = Section.objects.filter(owner=self.request.user)
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        images = self.request.FILES.getlist("images")
        for idx, image in enumerate(images[:5]):
            from .models import ItemMedia

            ItemMedia.objects.create(
                item=self.object,
                file=image,
                type=ItemMedia.MediaType.IMAGE,
                is_primary=idx == 0,
                position=idx,
            )
        return response


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = ItemInlineForm
    template_name = "library/item_form.html"
    success_url = reverse_lazy("library:home")

    def get_queryset(self):
        return Item.objects.filter(collection__owner=self.request.user)


class ItemDeleteView(LoginRequiredMixin, DeleteView):
    model = Item
    template_name = "library/item_confirm_delete.html"
    success_url = reverse_lazy("library:home")

    def get_queryset(self):
        return Item.objects.filter(collection__owner=self.request.user)


class SectionCreateView(LoginRequiredMixin, CreateView):
    model = Section
    form_class = SectionForm
    template_name = "library/section_form.html"
    success_url = reverse_lazy("library:home")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class SectionUpdateView(LoginRequiredMixin, UpdateView):
    model = Section
    form_class = SectionForm
    template_name = "library/section_form.html"
    success_url = reverse_lazy("library:home")

    def get_queryset(self):
        return Section.objects.filter(owner=self.request.user)


class SectionDeleteView(LoginRequiredMixin, DeleteView):
    model = Section
    template_name = "library/section_confirm_delete.html"
    success_url = reverse_lazy("library:home")

    def get_queryset(self):
        return Section.objects.filter(owner=self.request.user)







