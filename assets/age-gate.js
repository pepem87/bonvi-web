/* BON VI Mercat: confirmación declarativa de mayoría de edad (sitio público). */
(function () {
  "use strict";

  var KEY = "bonvi_edad_confirmada_v1";
  var THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000;
  var root = document.documentElement;
  var currentScript = document.currentScript;
  var logoUrl = currentScript && currentScript.src
    ? new URL("logo-horizontal.png", currentScript.src).href
    : "/assets/logo-horizontal.png";

  function wasConfirmed() {
    var now = Date.now();
    try {
      if (Number(window.localStorage.getItem(KEY)) > now) return true;
    } catch (err) {
      // El almacenamiento puede estar deshabilitado: verificar cookie.
    }
    var cookieMatch = document.cookie.match(/(?:^|;\s*)bonvi_edad_confirmada_v1=(\d+)/);
    return !!(cookieMatch && Number(cookieMatch[1]) > now);
  }

  if (wasConfirmed()) return;

  root.classList.add("bonvi-age-locked");

  var styles = document.createElement("style");
  styles.textContent = [
    "html.bonvi-age-locked, html.bonvi-age-locked body{overflow:hidden;}",
    "html.bonvi-age-locked .wrap{visibility:hidden;}",
    "html.bonvi-age-locked.bonvi-age-ready .wrap{visibility:visible;}",
    ".bonvi-age-overlay{position:fixed;inset:0;z-index:2147483647;background:rgba(11,32,25,.83);-webkit-backdrop-filter:blur(5px);backdrop-filter:blur(5px);padding:18px;display:grid;place-items:center;overflow-y:auto;font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;}",
    ".bonvi-age-card{box-sizing:border-box;position:relative;margin:auto;width:min(100%,460px);border:1px solid #d1b986;background:#fffaf1;color:#193e32;text-align:center;border-radius:22px;padding:clamp(26px,6vw,42px);box-shadow:0 22px 80px rgba(0,0,0,.33);}",
    ".bonvi-age-card:before{content:'';position:absolute;inset:10px;border:1px solid rgba(181,139,73,.36);border-radius:15px;pointer-events:none;}",
    ".bonvi-age-logo{display:block;width:min(240px,88%);max-height:100px;object-fit:contain;margin:0 auto 22px;}",
    ".bonvi-age-overline{font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;font-weight:800;color:#9a773a;margin:0 0 10px;}",
    ".bonvi-age-heading{font-family:Georgia,serif;font-size:clamp(1.65rem,5vw,2.1rem);line-height:1.18;font-weight:700;color:#173d31;margin:0 0 14px;}",
    ".bonvi-age-description{font-size:.97rem;line-height:1.65;color:#526157;margin:0 0 23px;}",
    ".bonvi-age-buttons{display:grid;gap:10px;}",
    ".bonvi-age-button{box-sizing:border-box;display:flex;align-items:center;justify-content:center;width:100%;min-height:48px;border-radius:12px;padding:12px 16px;font:700 .96rem Inter,system-ui,sans-serif;cursor:pointer;text-decoration:none;transition:background-color .15s;}",
    ".bonvi-age-button:focus-visible{outline:3px solid #b58b49;outline-offset:3px;}",
    ".bonvi-age-button.yes{background:#173d31;border:1px solid #173d31;color:#fff;}",
    ".bonvi-age-button.yes:hover{background:#2c5a49;}",
    ".bonvi-age-button.no{background:transparent;border:1px solid #b9bcae;color:#173d31;}",
    ".bonvi-age-button.no:hover{background:#f2ece0;}",
    ".bonvi-age-note{font-size:.74rem;line-height:1.5;color:#67726a;margin:18px 0 0;}",
    "@media(max-height:540px){.bonvi-age-card{padding:23px}.bonvi-age-logo{max-height:65px;margin-bottom:12px}.bonvi-age-description{margin-bottom:14px}}"
  ].join("\n");
  document.head.appendChild(styles);

  function showGate() {
    var overlay = document.createElement("div");
    overlay.className = "bonvi-age-overlay";
    overlay.innerHTML = [
      '<section class="bonvi-age-card" role="dialog" aria-modal="true" aria-labelledby="bonvi-age-title" aria-describedby="bonvi-age-description">',
      '<img class="bonvi-age-logo" src="' + logoUrl + '" alt="BON VI Mercat">',
      '<p class="bonvi-age-overline">Acceso exclusivo para mayores de edad</p>',
      '<h1 class="bonvi-age-heading" id="bonvi-age-title">¿Sos mayor de 18 años?</h1>',
      '<p class="bonvi-age-description" id="bonvi-age-description">Este sitio contiene información sobre bebidas alcohólicas. Para continuar, confirmá que tenés 18 años o más.</p>',
      '<div class="bonvi-age-buttons">',
      '<button type="button" class="bonvi-age-button yes" data-bonvi-age-yes>Sí, soy mayor de 18</button>',
      '<button type="button" class="bonvi-age-button no" data-bonvi-age-no>No, soy menor de 18</button>',
      '</div>',
      '<p class="bonvi-age-note">PROHIBIDA SU VENTA A MENORES DE 18 AÑOS</p>',
      '</section>'
    ].join("");

    document.body.appendChild(overlay);
    var content = document.querySelector(".wrap");
    if (content) content.inert = true;
    root.classList.add("bonvi-age-ready");

    var yes = overlay.querySelector("[data-bonvi-age-yes]");
    var no = overlay.querySelector("[data-bonvi-age-no]");

    function trapKeys(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
      }
      if (event.key !== "Tab") return;
      var focusables = Array.prototype.slice.call(
        overlay.querySelectorAll("button:not([disabled]),a[href]")
      );
      if (!focusables.length) return;
      var first = focusables[0];
      var last = focusables[focusables.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", trapKeys, true);
    yes.focus();

    yes.addEventListener("click", function () {
      var expiresAt = Date.now() + THIRTY_DAYS_MS;
      try {
        window.localStorage.setItem(KEY, String(expiresAt));
      } catch (err) {
        // Si localStorage no funciona, se intenta recordar con una cookie.
      }
      document.cookie = KEY + "=" + expiresAt + "; Max-Age=2592000; Path=/; SameSite=Lax; Secure";
      if (content) content.inert = false;
      document.removeEventListener("keydown", trapKeys, true);
      overlay.remove();
      root.classList.remove("bonvi-age-locked", "bonvi-age-ready");
    });

    no.addEventListener("click", function () {
      overlay.querySelector(".bonvi-age-card").innerHTML = [
        '<img class="bonvi-age-logo" src="' + logoUrl + '" alt="BON VI Mercat">',
        '<p class="bonvi-age-overline">Acceso restringido</p>',
        '<h1 class="bonvi-age-heading" id="bonvi-age-title">Este sitio es para mayores de 18 años</h1>',
        '<p class="bonvi-age-description" id="bonvi-age-description">No podés continuar navegando por BON VI Mercat si sos menor de edad.</p>',
        '<a class="bonvi-age-button yes" href="https://www.google.com/" rel="noreferrer">Salir del sitio</a>'
      ].join("");
      overlay.querySelector("a").focus();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", showGate, { once: true });
  } else {
    showGate();
  }
})();
