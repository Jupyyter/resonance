// The contact form's behaviour in the browser (lab 5). Every rule here is checked again by the
// server (forms.py): this only makes the form easier to fill in.
(function () {
  "use strict";

  const form = document.getElementById("formular-contact");
  if (!form) return;
  const NESELECTAT = "neselectat";

  // ---------- Departments follow the kind of message ----------
  // The pairs come from the database, through the page (json_script in contact.html).
  const departamentePeTip = JSON.parse(document.getElementById("departamente-pe-tip").textContent);
  const tip = form.elements["tip_mesaj"];
  const departament = form.elements["departament"];
  const toateDepartamentele = Array.from(departament.options).map((o) => [o.value, o.text]);

  function actualizeazaDepartamente() {
    const ales = departament.value;
    const permise = departamentePeTip[tip.value] || toateDepartamentele.filter(([v]) => v !== NESELECTAT);
    departament.replaceChildren(new Option("Not selected", NESELECTAT));
    for (const [slug, nume] of permise) departament.add(new Option(nume, slug));
    // keep the earlier choice if the new kind of message allows it
    departament.value = permise.some(([slug]) => slug === ales) ? ales : NESELECTAT;
  }
  tip.addEventListener("change", actualizeazaDepartamente);

  // ---------- How many CNP digits so far ----------
  const cnp = form.elements["cnp"];
  const contor = document.getElementById("contor-cnp");
  function actualizeazaContor() {
    const cifre = (cnp.value.match(/\d/g) || []).length;
    contor.textContent = `${cifre} of 13 digits`;
    contor.classList.toggle("complet", cifre === 13);
  }
  cnp.addEventListener("input", actualizeazaContor);

  // ---------- Images appear one at a time ----------
  const campuriImagini = Array.from(form.querySelectorAll(".camp-imagine"));
  const maxim = document.getElementById("imagini-maxim");
  function actualizeazaImagini() {
    let vizibile = 1;
    for (let i = 0; i < campuriImagini.length; i++) {
      const areFisier = campuriImagini[i].querySelector("input[type=file]").files.length > 0;
      if (areFisier && i + 1 < campuriImagini.length) vizibile = i + 2;
      if (!areFisier) break;
    }
    campuriImagini.forEach((camp, i) => {
      // a field with an error from the server stays visible, so its message can be read
      camp.hidden = i >= vizibile && !camp.classList.contains("camp-cu-eroare");
    });
    const ultimul = campuriImagini[campuriImagini.length - 1].querySelector("input[type=file]");
    maxim.hidden = ultimul.files.length === 0;
  }
  campuriImagini.forEach((camp) => camp.querySelector("input").addEventListener("change", actualizeazaImagini));

  // ---------- Sending needs the consent box ----------
  const gdpr = form.elements["gdpr"];
  const trimite = document.getElementById("trimite");
  function actualizeazaTrimite() {
    trimite.disabled = !gdpr.checked;
  }
  gdpr.addEventListener("change", actualizeazaTrimite);

  function actualizeazaTot() {
    actualizeazaDepartamente();
    actualizeazaContor();
    actualizeazaImagini();
    actualizeazaTrimite();
  }
  // "Clear the form" resets the values; the rest follows once the browser has done it
  form.addEventListener("reset", () => setTimeout(actualizeazaTot));
  actualizeazaTot();
})();
