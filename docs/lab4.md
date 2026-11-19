# Lab 4: admin, product pages, category pages

## 1. Apply it

Extract the zip over the project, then:

```
python manage.py migrate
python manage.py incarca_date
```

`migrate` runs `0002_instrument_tags.py`, which adds the `tags` column to instruments. `incarca_date` reloads `date_exemplu/date.json`, which now has tags for the 10 instruments. It updates the rows you already have, it doesn't duplicate them.

### The bonus: 50 more instruments

```
python date_exemplu/genereaza_inserturi.py
docker compose cp date_exemplu/inserturi_instrumente.sql db:/tmp/inserturi.sql
docker compose exec db psql -U resonance_user -d resonance -f /tmp/inserturi.sql
```

1. The script writes `inserturi_instrumente.sql`: 50 `INSERT` statements with random but valid instruments. `-n 80` makes 80, and `--seed 5` makes a different random set.
2. `docker compose cp` copies the file into the PostgreSQL container.
3. `psql` runs it there. No password is needed inside the container.

It all runs in one transaction, so if any row broke a rule, none would be saved. Run it only once: running it again adds 50 more.

### Commit

```
git add .
git commit -m "Laborator 4: admin personalizat, pagini de produse si categorii, generator de inserturi"
git push
```

## 2. The new pages

`/produse` and the category pages have a **filter panel** on the left (on phones, behind a Filters button). It's one form with one "Apply filters" button:

- **Tags**: tick as many as you like. Instruments must have all of them. The list always shows every tag of the page's instruments (all of them, or one category's) in the same order, so ticking one never makes others disappear or move. Next to each tag is how many instruments would stay if you ticked it too; 0 means none would, and those tags get a dashed outline.
- **Sort**: newest first (the default), or by name, price, date added or stock, ascending or descending.

The form is sent to the page it's on, so on a category page the tags filter within that category. Categories are chosen from the menu: **Instrument categories** lists "All instruments", then every category that has instruments. Choosing "Newest first" sends an empty `by=`, which the view drops from the address with a redirect, so addresses stay short and can be shared.

| Address | What it shows |
|---|---|
| `/produse` | every instrument, 6 per page |
| `/produse?by=price&sort=d` | sorted: `by` is name, price, date or stock; `sort` is `a` (ascending) or `d` (descending) |
| `/produse?tag=beginner&tag=compact` | only instruments with all these tags |
| `/produse/12` | one instrument: all its details, recordings, and 3 random ones from its category |
| `/produse/99999` | the error page, with status 404 |
| `/categorii/Basses` | one category's instruments, with the same sorting, tags and pages |

Spaces in category names become `%20` in addresses: `/categorii/Electric%20guitars`. The menu's links do this by themselves.

## 3. Where each requirement is

### Admin task (`instruments/admin.py`)

| Requirement | Where |
|---|---|
| Different field order for a model | Brand: `fields` puts founded_year second (models.py has it last); Service: the description moves last |
| A field of a related entity (one-to-many) | Instruments list: "brand country", the country of the instrument's brand |
| `@admin.display` + `format_html` column | Instruments list: the category in bold, in its own colour; stock as bold italic "only 1 left" or red "sold out" |
| Search on two fields, with `search_help_text` | every model, for example instruments by name and description |
| Ordered by a column | Instruments: `ordering = ["-price"]`, most expensive first |
| Side filters | Instruments (category, brand, condition, left-handed, date added), Brands, Services, Recordings |
| 5 items per page | Instruments: `list_per_page = 5` |
| Form sections, one collapsible with only optional fields | Instruments: "Price and stock", and "Details" (`classes: ["collapse"]`) |
| Tab title, header, main page title, "View site" | `site_title`, `site_header`, `index_title`, `site_url` at the top of admin.py |
| Page and menu background, logo, selected row, breadcrumbs | `templates/admin/base_site.html` (the logo) and `instruments/static/css/admin.css` (the colours) |
| 2 actions | Instruments: export as CSV, export as JSON, mark as sold out |

The admin's look lives in a project-level `templates/` folder, which `settings.py` now lists in `TEMPLATES["DIRS"]`. Django searches it before the apps' folders, so `templates/admin/base_site.html` replaces the admin's own file of that name.

### Bonus task

`date_exemplu/genereaza_inserturi.py`. Every generated row respects the rules in `models.py`:
- the price is over 0
- the weight is empty or between 0 and 200 kg
- the condition is new, used or refurbished
- used and refurbished instruments have stock 0 or 1
- new ones have a distributor

The category, brand and distributor are looked up by name with subqueries, so the file works whatever ids those rows have. It leaves "Studio and live gear" empty, as the lab's test category without products.

### QuerySets task

| Requirement | Where |
|---|---|
| Template namespacing | done since lab 2: `instruments/templates/instruments/`, rendered as `"instruments/produse.html"` |
| Products page: a box per product, name, some specifications, image, category | `produse.html`; `imagini/imagine-indisponibila.svg` for instruments without a photo |
| Name links to `get_absolute_url()`, full details, error page | `Instrument.get_absolute_url()` in models.py, `views.produs`, `produs.html`, `eroare.html` |
| "From the same category": K random products | `views.produs`: `order_by("?")`, K = `PRODUSE_ASEMANATOARE` = 3 in settings |
| Sort parameter (a/d) and column parameter | `?sort=a\|d&by=name\|price\|date\|stock`, in `views._listare` |
| stoc and tags (ArrayField), STOC_MIN, limited stock marked | `Instrument.tags`, `STOC_MIN = 3`; a red border and "Only N left" (`stoc.html`) |
| Tags as links that add a filter; several tags; active tags with × | the tags on each card are links that add them; the panel ticks several at once; `tags__contains` keeps instruments that have all of them; the active ones show above the results with × |
| Pagination, PROD_PER_PAG, "Page x of y" above and below, "Showing k to n of x", parameters kept | `Paginator` in `_listare`, `PROD_PER_PAG = 6`; the page bar is a template partial used twice, and `{% querystring %}` keeps the parameters |
| `/categorii/<name>` with the same template, its details, paginated within the category | `views.categorie` calls the same `_listare` with only that category's instruments |
| Categories menu built from the database, only categories with products | "Instrument categories" in the menu: `context_processors.meniu` uses `annotate(Count)` and `filter(numar__gt=0)`; the loop in `meniu.html`. "All instruments" comes first, as a fixed link to `/produse` |
| Category colour and icon, stored in the database, shown on products | `Category.color` and `icon` (Font Awesome); the card's top edge and the icon chip |
| The category on a product links to the category page | `Category.get_absolute_url()` |

**Reusing code**, which the lab asks about: `/produse` and `/categorii/<name>` differ only in their starting QuerySet, all instruments or one category's. So both views call `_listare(request, instrumente)`, which sorts, filters, paginates and renders the same template. That's why the category page gets sorting, tags and pages without any code of its own.

## 4. For the presentation

- **Sorting and pages together**: open `/produse?by=price&sort=d`, go to page 2. The address keeps `by` and `sort`, and the prices keep going down.
- **Tags**: tick two tags in the panel and apply. Both appear above the list with an ×; clicking × removes only that one. Clicking a tag on a card adds it too.
- **Tags within a category**: open a category from Instrument categories, then tick a tag. Only that category's instruments with the tag remain.
- **Error page**: `/produse/99999` and `/categorii/Nope`.
- **The menu updates itself**: add an instrument to "Studio and live gear" in the admin, and that category appears under Instrument categories. Delete it, and the category disappears again.
- **Admin actions**: tick a few instruments, choose "Export the selected instruments as CSV", click Run. The file downloads.
- **Collapsible section**: Change instrument, then click "Details".
