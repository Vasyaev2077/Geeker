from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Collection, Item, Section
from .forms import SectionForm, CollectionForm, ItemInlineForm, ItemForm
from django.shortcuts import redirect
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

import json
import urllib.request
import urllib.parse
import urllib.error


class HomeView(LoginRequiredMixin, ListView):
    """
    Главная вкладка библиотеки: список разделов (пользователь создаёт вручную).
    Можно выбрать несколько разделов — они разворачиваются и показывают предметы.
    """

    model = Section
    template_name = "library/home.html"
    context_object_name = "sections"
    paginate_by = 60

    def get_queryset(self):
        user = self.request.user
        qs = Section.objects.filter(owner=user).select_related("collection")
        query = (self.request.GET.get("q") or "").strip()
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
        return qs.order_by("name", "id")

    def _items_for_section(self, section, query: str, order: str):
        qs = (
            Item.objects.filter(collection=section.collection, collection__owner=self.request.user)
            .select_related("collection")
            .prefetch_related("media", "sections")
        )
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
        if order == "oldest":
            qs = qs.order_by("created_at", "id")
        elif order == "az":
            qs = qs.order_by("title", "id")
        elif order == "za":
            qs = qs.order_by("-title", "id")
        else:
            qs = qs.order_by("-created_at", "-id")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        query = (self.request.GET.get("q") or "").strip()
        ctx["query"] = query
        ctx["advanced"] = self.request.GET.get("advanced") == "on"
        ctx["current_order"] = self.request.GET.get("order", "recent")
        ctx["selected_sections"] = [int(s) for s in self.request.GET.getlist("sections") if s.isdigit()]

        selected_ids = set(ctx["selected_sections"])
        expanded = []
        for s in ctx["sections"]:
            if s.id in selected_ids:
                expanded.append(
                    {
                        "section": s,
                        "items": self._items_for_section(s, query, ctx["current_order"])[:24],
                    }
                )
        ctx["expanded_sections"] = expanded
        return ctx


class CollectionListView(LoginRequiredMixin, ListView):
    model = Collection
    template_name = "library/collection_list.html"
    context_object_name = "collections"
    paginate_by = 20

    def get_queryset(self):
        qs = Collection.objects.filter(owner=self.request.user).prefetch_related("tags")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        archived = self.request.GET.get("archived")
        if archived != "on":
            qs = qs.filter(is_archived=False)
        return qs.order_by("-created_at", "-id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        ctx["show_archived"] = self.request.GET.get("archived") == "on"
        return ctx


class CollectionDetailView(LoginRequiredMixin, DetailView):
    model = Collection
    template_name = "library/collection_detail.html"

    def get_queryset(self):
        return (
            Collection.objects.select_related("owner")
            .prefetch_related("items__media", "tags")
            .filter(owner=self.request.user)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user_sections"] = Section.objects.filter(owner=self.request.user).select_related("collection").order_by("name", "id")
        return ctx


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
        primary_upload_idx = self.request.POST.get("primary_upload_idx") or ""
        try:
            primary_idx = int(primary_upload_idx)
        except Exception:
            primary_idx = 0

        for idx, image in enumerate(images[:10]):
            ItemMedia.objects.create(
                item=item,
                file=image,
                type=ItemMedia.MediaType.IMAGE,
                is_primary=idx == primary_idx,
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
        return (
            Item.objects.select_related("collection", "collection__owner")
            .prefetch_related("media", "tags", "sections")
            .filter(collection__owner=self.request.user)
        )


@method_decorator(csrf_protect, name="dispatch")
class ItemMoveToSectionView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        item = get_object_or_404(Item, pk=pk, collection__owner=request.user)
        section_id = (request.POST.get("section_id") or "").strip()
        section = get_object_or_404(Section.objects.select_related("collection"), pk=section_id, owner=request.user)

        # Move between sections means moving to the section's internal collection and updating the section link.
        item.collection = section.collection
        item.save(update_fields=["collection"])
        item.sections.set([section])

        next_url = (request.POST.get("next") or "").strip()
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)

        from django.urls import reverse

        return redirect(reverse("library:section_detail", args=[section.pk]))


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
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
        if images:
            from .models import ItemMedia
            primary_upload_idx = self.request.POST.get("primary_upload_idx") or ""
            try:
                primary_idx = int(primary_upload_idx)
            except Exception:
                primary_idx = 0

            for idx, image in enumerate(images[:10]):
                ItemMedia.objects.create(
                    item=self.object,
                    file=image,
                    type=ItemMedia.MediaType.IMAGE,
                    is_primary=idx == primary_idx,
                    position=idx,
                )
        return response


class SectionItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "library/item_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.section = Section.objects.filter(owner=request.user, pk=kwargs.get("pk")).select_related("collection").first()
        if not self.section:
            from django.http import Http404

            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # force collection to current section's internal collection
        form.fields["collection"].queryset = Collection.objects.filter(owner=self.request.user, pk=self.section.collection_id)
        form.fields["collection"].initial = self.section.collection_id
        form.fields["collection"].disabled = True
        form.fields["sections"].queryset = Section.objects.filter(owner=self.request.user)
        # preselect the current section
        try:
            form.fields["sections"].initial = [self.section.id]
        except Exception:
            pass
        return form

    def form_valid(self, form):
        # enforce mapping
        form.instance.collection = self.section.collection
        response = super().form_valid(form)
        # ensure the item belongs to the section
        self.object.sections.add(self.section)

        images = self.request.FILES.getlist("images")
        if images:
            from .models import ItemMedia
            primary_upload_idx = self.request.POST.get("primary_upload_idx") or ""
            try:
                primary_idx = int(primary_upload_idx)
            except Exception:
                primary_idx = 0

            for idx, image in enumerate(images[:10]):
                ItemMedia.objects.create(
                    item=self.object,
                    file=image,
                    type=ItemMedia.MediaType.IMAGE,
                    is_primary=idx == primary_idx,
                    position=idx,
                )
        return response

    def get_success_url(self):
        from django.urls import reverse

        return reverse("library:section_detail", args=[self.section.pk])


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "library/item_form.html"
    success_url = reverse_lazy("library:home")

    def get_queryset(self):
        return Item.objects.filter(collection__owner=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["collection"].queryset = Collection.objects.filter(owner=self.request.user)
        form.fields["sections"].queryset = Section.objects.filter(owner=self.request.user)
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["media_items"] = list(self.object.media.all().order_by("-is_primary", "position", "id"))
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)

        # Delete selected media
        delete_ids = self.request.POST.getlist("delete_media")
        if delete_ids:
            self.object.media.filter(id__in=delete_ids).delete()

        # Set primary media
        primary_id = self.request.POST.get("primary_media_id") or ""
        if primary_id.isdigit():
            self.object.media.update(is_primary=False)
            self.object.media.filter(id=int(primary_id)).update(is_primary=True)

        # Add new uploads (append to end)
        images = self.request.FILES.getlist("images")
        if images:
            from .models import ItemMedia
            from django.db.models import Max

            start = (self.object.media.aggregate(Max("position")).get("position__max") or 0) + 1
            created = []
            for idx, image in enumerate(images[:10]):
                created.append(
                    ItemMedia.objects.create(
                    item=self.object,
                    file=image,
                    type=ItemMedia.MediaType.IMAGE,
                    is_primary=False,
                    position=start + idx,
                )
                )

            # If user picked a cover among NEW uploads, make it primary
            primary_upload_idx = self.request.POST.get("primary_upload_idx") or ""
            primary_upload_override = self.request.POST.get("primary_upload_override") or ""
            if primary_upload_override == "1" and primary_upload_idx.isdigit():
                pick = int(primary_upload_idx)
                if 0 <= pick < len(created):
                    self.object.media.update(is_primary=False)
                    ItemMedia.objects.filter(id=created[pick].id).update(is_primary=True)

        # Ensure there is a primary image if any remain (after deletions/uploads)
        if self.object.media.exists() and not self.object.media.filter(is_primary=True).exists():
            first = self.object.media.order_by("position", "id").first()
            if first:
                first.is_primary = True
                first.save(update_fields=["is_primary"])

        return response

    def get_success_url(self):
        # Prefer "return back" behavior
        next_url = (self.request.POST.get("next") or self.request.GET.get("next") or "").strip()
        if next_url:
            from django.utils.http import url_has_allowed_host_and_scheme

            if url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={self.request.get_host()},
                require_https=self.request.is_secure(),
            ):
                return next_url

        # Fallback: go to the item's collection page (cards grid)
        from django.urls import reverse

        return reverse("library:collection_detail", args=[self.object.collection_id])


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
        response = super().form_valid(form)
        # ensure an internal collection exists
        if not self.object.collection_id:
            c = Collection.objects.create(
                owner=self.request.user,
                title=self.object.name,
                description=self.object.description or "",
                visibility=Collection.Visibility.PRIVATE,
                is_archived=False,
            )
            self.object.collection = c
            self.object.save(update_fields=["collection"])
        return response


class SectionDetailView(LoginRequiredMixin, DetailView):
    model = Section
    template_name = "library/section_detail.html"

    def get_queryset(self):
        return Section.objects.filter(owner=self.request.user).select_related("collection")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        section = self.object
        q = (self.request.GET.get("q") or "").strip()
        order = self.request.GET.get("order", "recent")
        items = (
            Item.objects.filter(collection=section.collection, collection__owner=self.request.user)
            .select_related("collection")
            .prefetch_related("media", "sections")
        )
        if q:
            items = items.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if order == "oldest":
            items = items.order_by("created_at", "id")
        elif order == "az":
            items = items.order_by("title", "id")
        elif order == "za":
            items = items.order_by("-title", "id")
        else:
            items = items.order_by("-created_at", "-id")
        ctx["items"] = items
        ctx["query"] = q
        ctx["current_order"] = order
        ctx["user_sections"] = Section.objects.filter(owner=self.request.user).select_related("collection").order_by("name", "id")
        return ctx


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


@method_decorator(csrf_protect, name="dispatch")
class BarcodeLookupView(LoginRequiredMixin, View):
    """
    Lookup basic metadata by barcode/ISBN.
    Intended for books/comics ISBN (978/979/EAN13 or ISBN10).
    Returns JSON: {ok, code, isbn, title, description, cover_url, authors}
    """

    def post(self, request):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            payload = {}

        raw = (payload.get("code") or "").strip()
        code = "".join([c for c in raw if c.isdigit() or c.upper() == "X"])
        if not code:
            return JsonResponse({"ok": False, "error": "empty_code"}, status=400)

        def is_isbn13(x: str) -> bool:
            return len(x) == 13 and x.isdigit() and (x.startswith("978") or x.startswith("979"))

        def is_isbn10(x: str) -> bool:
            if len(x) != 10:
                return False
            body, last = x[:9], x[9]
            return body.isdigit() and (last.isdigit() or last.upper() == "X")

        isbn = code if (is_isbn13(code) or is_isbn10(code)) else ""
        isbn13 = isbn if is_isbn13(isbn) else ""
        isbn10 = isbn if is_isbn10(isbn) else ""

        def isbn13_to_isbn10(x: str) -> str:
            # Only 978-prefix ISBN13 can be converted to ISBN10
            if not (x and len(x) == 13 and x.isdigit() and x.startswith("978")):
                return ""
            core = x[3:12]  # 9 digits
            s = 0
            for i, ch in enumerate(core):
                s += (10 - i) * int(ch)
            r = 11 - (s % 11)
            if r == 10:
                check = "X"
            elif r == 11:
                check = "0"
            else:
                check = str(r)
            return core + check

        if isbn13 and not isbn10:
            isbn10 = isbn13_to_isbn10(isbn13)

        def fetch_json(url: str):
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Geeker/1.0 (barcode lookup)",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = resp.read()
                return json.loads(data.decode("utf-8") or "{}")
            except Exception:
                return None

        title = ""
        description = ""
        cover_url = ""
        authors = []
        candidates = []

        def normalize_ident(x: str) -> str:
            return (x or "").replace("-", "").strip()

        def upgrade_google_cover(u: str) -> str:
            if not u:
                return ""
            u = u.replace("http://", "https://")
            # Make google thumbnails less pixelated
            if "books.google" in u and "zoom=" in u:
                u = u.replace("zoom=0", "zoom=3").replace("zoom=1", "zoom=3").replace("zoom=2", "zoom=3")
            u = u.replace("&edge=curl", "")
            return u

        def pick_google_image(imgs: dict) -> str:
            if not imgs:
                return ""
            for k in ("extraLarge", "large", "medium", "small", "thumbnail", "smallThumbnail"):
                if imgs.get(k):
                    return upgrade_google_cover(str(imgs.get(k)))
            return ""

        def commons_file_url(file_url: str, width: int = 900) -> str:
            # Wikidata P18 usually returns "http(s)://commons.wikimedia.org/wiki/Special:FilePath/FILENAME"
            if not file_url:
                return ""
            u = str(file_url).replace("http://", "https://")
            # Ask Wikimedia to return a resized image (good quality, fast)
            if "commons.wikimedia.org/wiki/Special:FilePath/" in u:
                return u + ("?width=%d" % width)
            return u

        def wikidata_lookup_by_barcode(barcode: str):
            # P3969 = product barcode (EAN/UPC/GTIN)
            q = f"""
SELECT ?item ?itemLabel ?itemDescription ?pic WHERE {{
  ?item wdt:P3969 "{barcode}" .
  OPTIONAL {{ ?item wdt:P18 ?pic. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ru,en". }}
}}
LIMIT 5
""".strip()
            url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"format": "json", "query": q})
            data = fetch_json(url) or {}
            rows = (((data.get("results") or {}).get("bindings")) or [])
            out = []
            for r in rows:
                label = ((r.get("itemLabel") or {}).get("value")) or ""
                desc = ((r.get("itemDescription") or {}).get("value")) or ""
                pic = ((r.get("pic") or {}).get("value")) or ""
                out.append(
                    {
                        "title": label,
                        "description": desc,
                        "authors": [],
                        "cover_url": commons_file_url(pic, 900),
                        "language": "",
                        "match": True,
                        "source": "Wikidata",
                    }
                )
            return out

        def wikidata_lookup_by_isbn(isbn13_: str, isbn10_: str):
            # P212 = ISBN-13, P957 = ISBN-10
            parts = []
            if isbn13_:
                parts.append(f'?item wdt:P212 "{isbn13_}" .')
            if isbn10_:
                parts.append(f'?item wdt:P957 "{isbn10_}" .')
            if not parts:
                return []
            # OR the patterns by UNION to catch either property.
            unions = " UNION ".join([f"{{ {p} }}" for p in parts])
            q = f"""
SELECT ?item ?itemLabel ?itemDescription ?pic WHERE {{
  {unions}
  OPTIONAL {{ ?item wdt:P18 ?pic. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ru,en". }}
}}
LIMIT 5
""".strip()
            url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"format": "json", "query": q})
            data = fetch_json(url) or {}
            rows = (((data.get("results") or {}).get("bindings")) or [])
            out = []
            for r in rows:
                label = ((r.get("itemLabel") or {}).get("value")) or ""
                desc = ((r.get("itemDescription") or {}).get("value")) or ""
                pic = ((r.get("pic") or {}).get("value")) or ""
                out.append(
                    {
                        "title": label,
                        "description": desc,
                        "authors": [],
                        "cover_url": commons_file_url(pic, 900),
                        "language": "",
                        "match": True,
                        "source": "Wikidata",
                    }
                )
            return out

        # 1) OpenLibrary (best free for ISBN)
        if isbn:
            for key_isbn in [isbn13, isbn10, isbn]:
                if not key_isbn:
                    continue
                ol_url = (
                    "https://openlibrary.org/api/books?"
                    + urllib.parse.urlencode(
                        {
                            "bibkeys": f"ISBN:{key_isbn}",
                            "format": "json",
                            "jscmd": "data",
                        }
                    )
                )
                ol = fetch_json(ol_url) or {}
                rec = ol.get(f"ISBN:{key_isbn}") or {}
                if rec:
                    title = rec.get("title") or ""
                    desc = rec.get("notes") or rec.get("subtitle") or ""
                    if isinstance(desc, dict):
                        desc = desc.get("value") or ""
                    description = str(desc or "")
                    if rec.get("authors"):
                        authors = [a.get("name") for a in rec.get("authors", []) if a and a.get("name")]
                    cover = rec.get("cover") or {}
                    cover_url = cover.get("large") or cover.get("medium") or cover.get("small") or ""
                    break

        # 1.5) Wikidata ISBN (helps for comics/books where Google/OpenLibrary are messy)
        if isbn and not title:
            wd = wikidata_lookup_by_isbn(isbn13, isbn10)
            if wd:
                candidates.extend(wd)
                best = wd[0]
                title = best.get("title") or ""
                description = best.get("description") or ""
                cover_url = best.get("cover_url") or ""

        # 2) Google Books fallback
        def google_lookup(lang: str | None):
            params = {
                "q": f"isbn:{isbn13 or isbn10 or isbn}",
                "maxResults": 10,
                "printType": "books",
            }
            if lang:
                params["langRestrict"] = lang
            gb_url = "https://www.googleapis.com/books/v1/volumes?" + urllib.parse.urlencode(params)
            gb = fetch_json(gb_url) or {}
            return gb.get("items") or []

        if not title and isbn:
            want = {normalize_ident(isbn), normalize_ident(isbn13), normalize_ident(isbn10)}
            want = {w for w in want if w}

            items = google_lookup("ru")
            if not items:
                items = google_lookup(None)

            all_cands = []
            for it in items:
                info = (it or {}).get("volumeInfo") or {}
                ids = info.get("industryIdentifiers") or []
                found_ids = {normalize_ident((ident or {}).get("identifier") or "") for ident in ids}
                found_ids = {x for x in found_ids if x}
                imgs = info.get("imageLinks") or {}
                match = bool(want and (found_ids & want))
                c = {
                    "title": info.get("title") or "",
                    "description": str(info.get("description") or ""),
                    "authors": list(info.get("authors") or []),
                    "cover_url": pick_google_image(imgs),
                    "language": info.get("language") or "",
                    "match": match,
                }
                if c["title"]:
                    all_cands.append(c)

            # Prefer exact ISBN matches; if none exist, still return top candidates so user can choose.
            google_cands = [c for c in all_cands if c.get("match")] or all_cands
            # Mark source
            for c in google_cands:
                c["source"] = "Google Books"
            candidates.extend(google_cands)

            # If multiple candidates exist (Google sometimes has duplicates/editions), pick best but also return list.
            if google_cands and not title:
                def rank(c):
                    lang_score = 1 if (c.get("language") or "").lower() == "ru" else 0
                    cover_score = 1 if c.get("cover_url") else 0
                    title_score = len(c.get("title") or "")
                    return (lang_score, cover_score, title_score)

                google_cands.sort(key=rank, reverse=True)
                best = google_cands[0]
                title = best.get("title") or ""
                description = best.get("description") or ""
                authors = best.get("authors") or []
                cover_url = best.get("cover_url") or ""

        # 3) Generic product lookup: Wikidata by barcode for non-ISBN items (miniatures, games, etc.)
        if not isbn:
            wd = wikidata_lookup_by_barcode(code)
            if wd:
                candidates.extend(wd)
                if not title:
                    best = wd[0]
                    title = best.get("title") or ""
                    description = best.get("description") or ""
                    cover_url = best.get("cover_url") or ""

        # Cover quality fallback: try OpenLibrary covers CDN (often higher res) if we have ISBN.
        if isbn and (not cover_url or "zoom=" in cover_url):
            cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"

        cover_urls = []
        # Prefer explicit cover_url first
        if cover_url:
            cover_urls.append(cover_url)
        # Add OpenLibrary size fallbacks for this ISBN (some sizes may 404; frontend will try next)
        if isbn:
            cover_urls.extend(
                [
                    f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false",
                    f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg?default=false",
                    f"https://covers.openlibrary.org/b/isbn/{isbn}-S.jpg?default=false",
                ]
            )
        # Add covers from candidates (Wikidata/Google) as additional fallbacks
        for c in (candidates or [])[:8]:
            u = (c or {}).get("cover_url") or ""
            if u:
                cover_urls.append(u)
        # De-dup while preserving order
        seen = set()
        cover_urls_dedup = []
        for u in cover_urls:
            if u in seen:
                continue
            seen.add(u)
            cover_urls_dedup.append(u)

        return JsonResponse(
            {
                "ok": True,
                "code": code,
                "isbn": isbn,
                "title": title,
                "description": description,
                "cover_url": cover_url,
                "cover_urls": cover_urls_dedup[:8],
                "authors": authors,
                "candidates": (candidates or [])[:5],
            }
        )


@method_decorator(csrf_protect, name="dispatch")
class FetchImageView(LoginRequiredMixin, View):
    """
    Proxy image fetch to avoid browser CORS issues when adding cover into uploads.
    Accepts JSON: {url}
    """

    ALLOWED_HOSTS = {
        "openlibrary.org",
        "covers.openlibrary.org",
        "books.google.com",
        "books.googleusercontent.com",
        "lh3.googleusercontent.com",
        "upload.wikimedia.org",
        "commons.wikimedia.org",
    }

    def post(self, request):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            payload = {}
        url = (payload.get("url") or "").strip()
        if not url:
            return JsonResponse({"ok": False, "error": "empty_url"}, status=400)

        try:
            parsed = urllib.parse.urlparse(url)
        except Exception:
            return JsonResponse({"ok": False, "error": "bad_url"}, status=400)

        if parsed.scheme not in ("http", "https"):
            return JsonResponse({"ok": False, "error": "bad_scheme"}, status=400)

        host = (parsed.hostname or "").lower()
        if host not in self.ALLOWED_HOSTS:
            return JsonResponse({"ok": False, "error": "host_not_allowed"}, status=400)

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Geeker/1.0 (image proxy)",
                    "Accept": "image/*,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
                ctype = resp.headers.get("Content-Type") or "application/octet-stream"
        except urllib.error.HTTPError:
            return JsonResponse({"ok": False, "error": "fetch_failed"}, status=400)
        except Exception:
            return JsonResponse({"ok": False, "error": "fetch_failed"}, status=400)

        return HttpResponse(data, content_type=ctype)







