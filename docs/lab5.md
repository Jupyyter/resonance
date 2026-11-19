# Lab 5: messages, the filter form, the contact page, adding instruments

## 1. Apply it

Extract the zip over the project, then:

```
python manage.py migrate
python manage.py test instruments
```

`migrate` runs three migrations:

- `0003_category_icon_choices.py`: the category icon becomes a choice from a fixed list, the icons drawn as inline SVG (the centring fix).
- `0004_contact_departments_message_types.py`: two new tables, `Department` and `MessageType`, and the link table between them.
- `0005_contact_data.py`: fills them with 6 departments and 5 kinds of message, and which departments handle which kind.

The tests should end with `OK` (57 tests).

`/mesaje` and `/produse/adauga` are for staff only. Log in with the admin account you already have; if you don't have one, run `python manage.py createsuperuser`.

The contact messages are saved in `instruments/Mesaje_nerezolvate/`. The folder is created by itself, and `.gitignore` leaves it out of git, because the messages hold personal data (names, emails, CNPs).

### Commit

```
git add .
git commit -m "Laborator 5: mesaje, formular de filtrare, pagina de contact, adaugare instrumente"
git push
```

## 2. Task 1: messages

Every page shows the messages framework's messages above its content (`mesaje_site.html`, included in `baza.html`). On `/produse` they sit above the results instead, inside the part that's replaced when you filter, so a filter's message appears without reloading the page.

Each level has its own look, in `site.css` under "The messages framework":

| Level | Look | Label |
|---|---|---|
| debug | dashed outline, small grey text | Debug |
| info | white, green edge on the left | Note |
| success | seafoam green background | Done |
| warning | sand background, brown icon | Heads up |
| error | red frame, red text | Problem |

Every message also has an icon and a first word that say the level, so the colour isn't the only clue.

Debug messages only show while developing: `settings.py` sets `MESSAGE_LEVEL` to `DEBUG` when `DEBUG=True` and to `INFO` otherwise, so on a real server they're dropped.

### Where each level is used, and why

| Level | Where (views.py) | Why this level |
|---|---|---|
| debug | the filters: "Filters applied: price from, to. 21 of 60 instruments match." | only a developer needs to know which filters the server applied |
| debug | contact: "Saved as Mesaje_nerezolvate/workshop/mesaj_….json" | the file's path is useful while testing, meaningless to a customer |
| info | Reset: "Filters cleared: showing every instrument." | confirms what you asked for; nothing went wrong and nothing to do |
| info | /mesaje: "3 messages for Workshop in November 2026." (or "No messages…") | a plain fact about the page |
| success | contact: "Thank you, Popescu. Your question went to Workshop…" | the message was sent: an action finished well |
| success | adding: "Fender Jazz Bass is in the shop, at 5,679 lei." | the instrument was saved |
| warning | "Now showing 12 instruments per page instead of 6. On page 2, you may have skipped some…" | it worked, but you may have missed something |
| warning | "No instruments match all these filters." | nothing is broken, but the page is empty and you'll want to change something |
| error | filters with invalid values (price from 5000 to 1000) | some of what you asked for couldn't be done |
| error | a category page asked to show another category | the address was changed by hand, and the request was refused |
| error | contact: "The message wasn't sent." | nothing was saved; you have to fix the form |
| error | adding: "The instrument wasn't added." | the same, for the instrument form |

Messages survive redirects: the framework stores them until a page shows them. That's why the contact form can redirect after sending (so reloading doesn't send it twice) and still show "Thank you" on the next page.

## 3. Task 2: the filter form

`FiltruInstrumenteForm` in `forms.py`, shown in the panel on `/produse` and on every category page. Every field is optional; left empty, it doesn't filter. The field names are the address's parameters (`?nume=strat&pret_max=5000`), so a filtered list can be bookmarked or shared.

| Field | Column | Widget |
|---|---|---|
| Name | name | search box |
| Description mentions | description | search box |
| Price from / to | price | two number inputs (an interval) |
| Category | category (foreign key) | list; on a category page, hidden and read-only |
| Brand | brand (foreign key) | list from the Brand table |
| Supplied by | distributor (foreign key) | list from the Distributor table |
| Offers the service | services (many-to-many) | list from the Service table |
| Condition | condition | list: new, used, refurbished |
| Stock | stock | list: in stock, only a few left, sold out |
| Left-handed | left_handed | list: either, left-handed only, right-handed only |
| Weighs at most | weight_kg | number input, steps of 0.5 |
| Made of | materials (array) | list of the materials the page's instruments have |
| Added from / to | date_added | two calendars |
| Only with a photo | image | checkbox |
| Tags | tags (array) | checkboxes, with counts (from lab 4) |
| Sort by, Order | | lists; the lab 4 `by` and `sort` parameters |
| Per page | | list: 6, 12, 18, 24 |
| Columns | | list: 1, 2, 3 |

| Requirement | Where |
|---|---|
| Validations with our own messages | `clean_nume` (at least 2 letters), `clean_descriere` (a word, not only punctuation), `clean_adaugat_de_la` (not in the future); `clean()` checks two fields together: the highest price isn't below the lowest, and the dates aren't swapped. Every built-in check (not a number, not in the list, too long) has its message in `error_messages` |
| A wrong filter doesn't break the page | the view applies only the valid fields, shows the errors next to the wrong ones, and an error message above the results |
| Per page, with a warning when paging changes | the form sends two hidden fields, the previous per-page and the current page. If the number changed while on page 2 or later, `_curata_adresa` keeps the page number and adds the warning |
| Columns, and per-page values that divide by them | 6, 12, 18 and 24 all divide by 1, 2 and 3, so every row of the grid is full. One column shows each instrument as a wide card, photo on the left. On narrow screens 3 columns become 2, then 1 |
| On a category page, the category is hidden and can't be changed | the field becomes `HiddenInput(attrs={"readonly": True})` with the page's category. The server checks it anyway: if the address asks for another category, an error message says so and the page keeps its own |
| Reset, asking first | the Reset link opens a `<dialog>` ("Clear every filter?"); only "Clear filters" goes on. Without JavaScript the link works straight away |
| A message when nothing matches | the warning above, and "No instruments match all these filters" in place of the list |
| The old addresses keep working | `?tag=…`, `?by=…&sort=…` and `?page=…` are fields of the same form, so lab 4's links still filter the same way |

**Bonus: filtering without reloading.** `static/js/filtre.js` intercepts the form, Reset, the page links and the tag links. It asks the server for the same address with the header `X-Partial: vitrina`, and the view renders only the `vitrina` part of the template (the panel and the results, `{% partialdef vitrina %}`). The script swaps that part in and puts the new address in the browser's history, so Back, reloading and sharing still work. Without JavaScript everything is an ordinary link or form and works the same, just with a full page load.

## 4. Task 3: the contact page

`/contact`, with `ContactForm` in `forms.py`. A valid message isn't saved in the database: `contact.py` writes it as a JSON file.

### Fields and checks

| Field | Checks |
|---|---|
| Family name | required, 10 characters at most, starts with a capital, only letters, spaces and hyphens |
| Given names | optional; the same, and every part after a space or hyphen starts with a capital (Ana-Maria) |
| CNP | optional; 13 digits, starts with 1, 2, 5 or 6, digits 2–7 are a real date, and that date is the date of birth |
| Date of birth | required, a calendar; at least 18 years old |
| Email, Email again | both required, both the same; temporary addresses (yopmail, guerillamail) refused |
| Phone | optional; 0721 000 000, or + and the country code |
| Kind of message | complaint, question, review, request or appointment, from the `MessageType` table; "Not selected" is refused |
| Send it to | a department from the `Department` table, and one that handles this kind of message (the link table); "Not selected" is refused |
| Subject | required; starts with a capital, only letters, spaces and hyphens; no links and no `a.b.c` addresses |
| Days you can wait | 1 to 30, and at least the kind's minimum (the label lists them, built from the table) |
| Message | 5 to 100 words, each at most 15 characters; no links; must end with the family name (the signature) |
| Images | up to 3, optional, must be real images |
| Consent | required; the Send button stays disabled until it's ticked, and the server checks again |
| Request code (hidden) | made by the server when the page opens, signed with `SECRET_KEY` and the time. An invented or 3-hour-old code is refused |

The validators used by several fields live in `validatori.py`: `majuscula_si_litere`, `majuscula_dupa_separator`, `fara_linkuri`, `fara_email_temporar`, `major`, `cnp_valid`.

On the page, `static/js/contact.js` (none of it is needed for the form to work):
- the department list shows only the departments of the chosen kind
- the CNP field counts its digits
- the second image field appears after the first is chosen, the third after the second; after 3, a note says that's the most
- the Send button waits for the consent box

### What's saved

`instruments/Mesaje_nerezolvate/<department>/mesaj_<timestamp>.json`, with `_urgent` before `.json` when the sender chose exactly the minimum days for that kind of message. Images are saved next to it as `mesaj_<timestamp>_imagine1.png` and so on.

Before saving:
- the date of birth is replaced by the age: "36 years and 6 months"
- the email is lowercased
- the message gets a capital letter after each sentence end (`.` `?` `!` `...`), runs of spaces become one space, and each line becomes a `<p>` paragraph. Every paragraph is escaped first, so a `<` typed in a message can't become a tag on the /mesaje page
- the email confirmation isn't saved; the IP and the arrival time are added

The department folders are created when needed, checked with `Path.stat()` (it raises `FileNotFoundError` when the folder isn't there).

### /mesaje

| Address | What it shows |
|---|---|
| `/mesaje` | every department, how many messages it has, links to this year, month and day |
| `/mesaje/workshop/2026` | the Workshop's messages from 2026, newest first |
| `/mesaje/workshop/2026/11` | from November 2026 |
| `/mesaje/workshop/2026/11/19` | from 19 November 2026 |

Each message has a left edge in its kind's colour, with its icon and name (both from the `MessageType` table). Urgent ones are framed in red with an "Urgent" label. "All 16 fields" opens every field of the file, whatever they are: the page loops over the file's keys instead of naming them. A wrong date (`/2026/13`) or department gives the error page.

## 5. Task 4: adding an instrument

`/produse/adauga` (staff only; on `/produse` staff see an "Add an instrument" link). `InstrumentForm` in `forms.py` is a `ModelForm` for `Instrument`.

| Requirement | Where |
|---|---|
| Two inputs that aren't columns, used to compute one that's missing | Purchase price and Markup (%). The form has no price field: the view computes it as purchase price + markup, rounded to end in 9 (`la_9`): 3,500 + 30% = 4,550 → 4,559 lei |
| `commit=False` | `views.adauga_instrument`: `form.save(commit=False)`, then the price is set, then `save()` and `save_m2m()` |
| Our own labels | `Meta.labels` (Instrument name, Description for the product page, Units in the shop), and the two extra fields' labels |
| 3 field validations | `clean_pret_achizitie` (10 to 100,000 lei), `clean_adaos` (5% to 150%), `clean_stock` (200 at most) |
| A validation of several fields | `clean()`: used and refurbished instruments get a markup of 60% at most (condition + markup) |
| Two validators defined outside the form, applied in order, one also on another field | name: `[fara_linkuri, fara_strigat]` (no links, then not all in capitals); `fara_linkuri` is also on the description |
| Every error message our own | `error_messages` on the extra fields and in `Meta.error_messages`; tags: "Tag 2: a tag fits in 30 characters." |
| help_text on at least 2 fields | Purchase price, Markup, Tags |

The model's own rules still apply, through `full_clean()`: a new instrument needs a distributor, a used one has stock 0 or 1. They appear above the form.

## 6. For the presentation

- **Messages**: on `/produse`, set Price from 5000 and to 1000, apply. The "to" field is marked in red, a red Problem message appears, and the grey dashed Debug message shows the filters that did apply.
- **No reload**: apply a filter and watch the address change while the page stays put. Press Back: the previous list returns.
- **Reset**: click Reset, then "Keep my filters" (nothing changes), then Reset and "Clear filters" (a Note message).
- **Paging warning**: go to page 2, choose 12 per page, apply. The sand-coloured Heads up message appears.
- **Columns**: choose 1 column: wide cards with the photo on the left.
- **Hidden category**: on a category page, open the browser's inspector and change the hidden `categorie` input's value to another category, then apply. The page refuses and keeps its own category.
- **Contact**: choose "Review": only Administration and Quality assurance stay in the list. Type part of a CNP and watch the counter. Send with mistakes to show the messages, then a valid one: the Done message appears, and the file is in `instruments/Mesaje_nerezolvate/<department>/`.
- **Urgent**: send a question with 2 days (its minimum). On `/mesaje` it's framed in red, with the Urgent label.
- **Adding**: on `/produse/adauga`, type the name in capitals, or a used instrument with an 80% markup, to show the errors. Then add a valid one: you land on its page, with its computed price.
