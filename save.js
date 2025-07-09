window.addEventListener("load", () => {
  fetch("https://api64.ipify.org?format=json")
    .then(res => res.json())
    .then(ipData => {
      const ip = ipData.ip || "0.0.0.0";
      const lang = encodeURIComponent(navigator.language || "");
      const ua = encodeURIComponent(navigator.userAgent || "");
      const os = encodeURIComponent(navigator.platform || "");
      const tz = encodeURIComponent(Intl.DateTimeFormat().resolvedOptions().timeZone || "");

      const scriptURL = "https://script.google.com/macros/s/AKfycbw4popLkTvojw-YhjJCmfXYDt17RLXj2Ijl1lCcaKYHcN8snBndksNNKUz1L0xDumpDYQ/exec";

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
