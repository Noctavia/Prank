window.addEventListener("load", () => {
  fetch("https://api64.ipify.org?format=json")
    .then(res => res.json())
    .then(ipData => {
      const ip = ipData.ip || "0.0.0.0";
      const lang = encodeURIComponent(navigator.language || "");
      const ua = encodeURIComponent(navigator.userAgent || "");
      const os = encodeURIComponent(navigator.platform || "");
      const tz = encodeURIComponent(Intl.DateTimeFormat().resolvedOptions().timeZone || "");

      const scriptURL = "https://script.google.com/macros/s/AKfycbwNGJmQM0nsSPuBI7xmNDYewNq6FbyPsVBan7q1b_sHvqis5ooBtXypbt57EpfOSrYxHQ/exec";

      const finalURL = `${scriptURL}?ip=${ip}&lang=${lang}&ua=${ua}&os=${os}&tz=${tz}`;

      fetch(finalURL)
        .then(res => {
          if (res.ok) {
            console.log("✅ Données enregistrées");
          } else {
            console.warn("❌ Erreur côté Google Script");
          }
        })
        .catch(err => console.error("Erreur fetch :", err));
    })
    .catch(err => console.error("Erreur IP :", err));
});
