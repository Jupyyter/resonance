# Lab 2: templates, menu and the visit log

## 1. Edit `resonance/settings.py` by hand

The zip doesn't include `settings.py`, so your `SECRET_KEY` stays yours. Make these three changes.

**MIDDLEWARE**: add the second line under the one from lab 1.

```python
    "instruments.middleware.IpMiddleware",
    "instruments.middleware.AccesariMiddleware",
]
```

**TEMPLATES**: add the last two lines to `context_processors`.

```python
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "instruments.context_processors.companie",
                "instruments.context_processors.meniu",
            ],
```

**After `STATIC_URL = "static/"`**: add the company details.

```python
# The shop's details, shown in every page's footer (see instruments/context_processors.py).
COMPANY_INFO = {
    "name": "Resonance",
    "founded": 2019,
    "phone": "+40 21 000 1234",
    "email": "contact@resonance.example",
    "address": "Strada Rezonanței 7, Sector 2, București",
    "opening_hours": "Monday to Saturday, 10:00 to 19:00",
}
```

## 2. Run it

```
python manage.py runserver
python manage.py test instruments
```

## 3. Where each requirement is

| Requirement | Where |
|---|---|
| /log with ultimele, accesari, iduri + dubluri, tabel | `views.log`, `templates/instruments/log.html` |
| "Exista doar k accesari fata de n accesari cerute" | at the end of the list on /log |
| accesari=detalii as an unordered list | `<ul class="date-accesari">` in `log.html` |
| "Parametri" section: how many parameters and their names | `log.html` |
| Least and most visited pages, under the list or table | `accesari.pagini_extreme()`, right under the list on /log |
| /despre, /istoric | `despre.html`, `istoric.html` |
| re_path /accesare&lt;id&gt; | `urls.py` (`/accesare12`), `views.accesare`, `accesare.html` |
| baza.html with header, main, footer; every page extends it | `templates/instruments/baza.html` |
| Menu with submenus, built with `{% url %}`, linking to every page in the documentation; one submenu links to sections | `meniu.html` (About links to `#poveste`, `#atelier`, `#vizita`) |
| nav.css: dropdown, background images, responsive | `static/css/nav.css` |
| Footer IP from middleware | `IpMiddleware` sets `request.ip_client` |
| Copyright and company details in the footer, from a custom context processor and a dict in settings | `context_processors.companie`, `COMPANY_INFO` |
| Images in static, shown with `{% static %}` on home and about | `static/imagini/`, `index.html`, `despre.html` |
| Static subfolders by type | `static/css`, `static/imagini`, `static/fonturi` |
| in_lucru.html titled "In lucru"; each unbuilt menu link has its own view that renders it | `views.produse`, `views.contact`, `views.cos_virtual` |
| Two pages of our choice | /services (setup and repairs), /faq (questions) |

## 4. Choices the lab leaves open

- **Counting parameters**: a name given several times (`?iduri=1&iduri=2`) counts as one parameter with several values.
- **iduri with ultimele**: the lab doesn't combine them. Here iduri picks the visits, then ultimele keeps the last n of those.
- **Least visited page**: pages nobody has opened yet count, with 0 visits. Ties show every page that shares the place.
- **Unknown or wrong values** (`ultimele=abc`, `accesari=xyz`, `tabel=nume`): an error message explains what the parameter accepts.

## 5. Text for the "Conținut" section of the document

Resonance is an online shop for musical instruments: electric and acoustic guitars, basses, keyboards and synthesizers, drums and studio gear. Every instrument is checked and set up in the shop's workshop before it ships.

Pages:

- **Home** (`/`): the shop's description and a Chladni figure (the pattern sand makes on a vibrating plate), then three sections: what the shop sells (six categories), the 3D models and recordings on product pages, and the four steps of an order.
- **About** (`/despre`): three sections. *Our story* covers how the shop started, *The workshop* covers what happens to an instrument before it ships (with three Chladni figures), and *Visit us* gives the address, opening hours and phone number.
- **Shop history** (`/istoric`): a timeline of the shop, year by year, from 2019 to 2026.
- **Setup and repairs** (`/services`, a page of our choice): a price table for setups, fret work, electronics repairs and rentals, and how to book.
- **Questions** (`/faq`, a page of our choice): answers to common questions about returns, setups, trying instruments, shipping and trade-ins. They open and close on click.
- **Products** (`/produse`), **Contact** (`/contact`) and **Cart** (`/cos_virtual`): these show the "In lucru" page until they're built.
- **Server info** (`/info`): the server's date and time, or only the date or time (`?data=zi`, `?data=timp`).
- **Visit log** (`/log`): every page visit since the server started, with options for choosing and showing them, plus the least and most visited pages. Each visit has its own page, `/accesare<id>`.

Every page shares the same header and footer. The header holds the menu: Home, Instrument categories (submenu: all instruments, then each category; added in lab 4), About (submenu: three links to sections of the About page, setup and repairs, shop history, questions), Contact, Site (submenu: server info, visit log) and Cart. On phones the menu folds behind a Menu button.

The footer shows the copyright line, the company's details and the visitor's IP address. The details come from a dictionary in `settings.py` with the name, founding year, phone number and address of the main shop, plus two characteristics of our choice: the **email address** and the **opening hours**.

Visual identity: the colours come from instruments. Rosewood (fretboards) is used for the menu and footer, nickel (hardware) for the background, mother-of-pearl (fret inlays) for surfaces, and a seafoam green (a classic guitar finish) for links. A pearl dot marks the current menu section, like the inlay that marks a fret. Headings use Big Shoulders Display and text uses Karla, both open-source fonts (SIL OFL) served from the site's own static folder. All images are SVGs. The Chladni figures were computed from the vibration equation of a square plate, which ties into the shop's name.

## 6. Text for the database diagram section (Task 3)

Put `docs/diagrama-bd.png` at the top of the section. The editable file is `docs/diagrama-bd.drawio`: open it at app.diagrams.net (File, Open from, Device), and after any change export a new PNG (File, Export as, PNG).

The database describes the shop and the instruments it sells. Users, orders and reviews come in later labs, so they aren't part of it yet. There are six entities, drawn in Chen notation: rectangles are entities, ellipses are attributes (each with its type), and diamonds are relationships. Double borders mark the weak entity, its identifying relationship and the multivalued attribute. A double line means total participation: every instance of that entity takes part in the relationship.

### Entities

**Instrument**: the product the shop sells.
- id: integer, primary key
- name: string
- description: text
- price: decimal (money needs exact values, so not float)
- stock: integer, the units in the shop
- condition: enum, one of new, used, refurbished
- left_handed: boolean
- weight_kg: float
- date_added: datetime, the moment it was added
- materials: list of strings, the multivalued attribute (for example alder, maple, rosewood)
- image: image file, a photo of the instrument
- tags: list of strings, a second multivalued attribute: keywords for filtering (for example vintage, beginner), added in lab 4

**Category**: how instruments are grouped (electric guitars, basses, keyboards and so on).
- id: integer, primary key
- name, description, color, icon: strings. These are the four required attributes (nume, descriere, culoare, sigla). color is the hex colour used to style the category's pages, and icon is the name of an icon from an icon library.
- display_order: integer, the category's position in menus and lists

**Brand**: the company that makes the instrument.
- id: integer, primary key
- name, country, website: strings
- founded_year: integer

**Distributor**: a partner company the shop buys new instruments from.
- id: integer, primary key
- name, email, phone: strings

**Service**: an extra service the shop offers with an instrument, such as a setup, fret work, electronics work or a rental.
- id: integer, primary key
- name: string
- description: text
- price: decimal
- duration_days: integer
- available: boolean

**Recording** (weak entity): a sound sample of an instrument, played on its product page.
- number: integer, partial key (dashed underline)
- title: string
- audio_file: file, the sound file
- duration_s: integer, the length in seconds
- sound: enum, one of clean, amplified, with effects

### Relationships

- **Category 1 to N Instrument** (belongs to): every instrument belongs to exactly one category (total participation), and a category holds many instruments.
- **Brand 1 to N Instrument** (makes): every instrument has exactly one brand, and a brand makes many instruments.
- **Distributor 1 to N Instrument** (supplies): a distributor supplies many instruments. Participation is partial on the instrument side, because used and trade-in instruments don't come from a distributor.
- **Service M to N Instrument** (applies to): a service can be offered for many instruments, and an instrument can get several services. In the database this becomes an associative table, which the diagram doesn't show.
- **Instrument 1 to N Recording** (has): the identifying relationship of the weak entity.

### Why Recording is a weak entity

A recording only exists as a recording of one particular instrument. It has no key of its own: its number (1, 2, 3, ...) counts the recordings of that instrument only, so recording 2 of a guitar and recording 2 of a bass are different recordings. A recording is identified by its instrument's id together with its number, and when an instrument is deleted, its recordings are deleted with it.

### Attribute types

Eleven types are used: integer, string, text, decimal, float, boolean, enum, datetime, list of strings, image file and file.

### Third normal form

- **First normal form**: every attribute holds a single value. The exceptions are materials and tags, the multivalued attributes the labs ask for.
- **Second normal form**: every entity has a single-attribute key, except Recording, whose key is the instrument's id plus the number. Recording's other attributes depend on that whole key, not on part of it: a title belongs to one recording of one instrument.
- **Third normal form**: no attribute depends on another attribute that isn't a key. Facts about a brand (country, website) are kept in Brand, not repeated in every instrument. A category's colour is kept in Category, and a distributor's email and phone in Distributor.
- **No derived attributes**: nothing can be computed from other data. For example, there's no number of recordings per instrument, no price with VAT, and no brand age (it follows from founded_year).
- **No one-to-one relationships.**
