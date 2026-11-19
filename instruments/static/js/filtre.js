// Filters without reloading the page (lab 5 bonus).
//
// The filter form, the page links, the tag links and Reset are intercepted: instead of loading a
// whole new page, the script asks the server for only the part that changes (the header
// X-Partial: vitrina makes the view render only that part of the template), swaps it in, and puts
// the new address in the browser's history, so Back, reloading and sharing the address still work.
// Without JavaScript, all of these are ordinary links and an ordinary form, and work the same.
(function () {
  "use strict";

  async function incarca(adresa, inIstoric) {
    const vitrina = document.getElementById("vitrina");
    vitrina.setAttribute("aria-busy", "true");
    try {
      // fetch follows the server's redirects (it tidies addresses) and keeps the header on the way
      const raspuns = await fetch(adresa, { headers: { "X-Partial": "vitrina" } });
      const html = await raspuns.text();
      const noua = new DOMParser().parseFromString(html, "text/html").getElementById("vitrina");
      if (!noua) throw new Error("no #vitrina in the answer");
      vitrina.replaceWith(noua);
      if (inIstoric) history.pushState(null, "", raspuns.url); // the address after any redirect
      if (noua.getBoundingClientRect().top < 0) noua.scrollIntoView({ block: "start" });
    } catch (eroare) {
      window.location.href = adresa; // if anything goes wrong, load the page the normal way
    }
  }

  // The filter form: its fields become the address, exactly as the browser would build it.
  document.addEventListener("submit", function (e) {
    const form = e.target.closest("#vitrina form.filtre");
    if (!form) return;
    e.preventDefault();
    const parametri = new URLSearchParams(new FormData(form));
    incarca(form.action + "?" + parametri.toString(), true);
  });

  // Links marked data-filtru: pages, tags, removing a tag, Reset.
  document.addEventListener("click", function (e) {
    const link = e.target.closest("#vitrina a[data-filtru]");
    // a new tab (Ctrl or middle click) stays an ordinary link
    if (!link || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    e.preventDefault();

    if (link.dataset.confirma) {
      // Reset asks first: the filters would be lost
      const dialog = document.getElementById(link.dataset.confirma);
      dialog.returnValue = "";
      dialog.addEventListener("close", function () {
        if (dialog.returnValue === "da") incarca(link.href, true);
      }, { once: true });
      dialog.showModal();
      return;
    }
    incarca(link.href, true);
  });

  // Back and Forward: show the list for the address the browser went back to.
  window.addEventListener("popstate", function () {
    incarca(window.location.href, false);
  });
})();
