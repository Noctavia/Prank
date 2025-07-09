window.addEventListener("load", () => {
  // Obtenir l’IP publique
  fetch("https://api64.ipify.org?format=json")
    .then(res => res.json())
    .then(ipData => {
      const data = {
        language: navigator.language || "",
        userAgent: navigator.userAgent || "",
        platform: navigator.platform || "",
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
        date: new Date().toISOString(),
        ip: ipData.ip || "0.0.0.0"
      };

      const scriptURL = "https://script.google.com/macros/s/AKfycbymFZX4GOPUEVpNrtqxJ_Pl9zlrlAxBG2Un2xK6MyPX9zniorO_H71JZWAzcGOUcA5N7Q/exec"; // Remplace ci-dessous

      fetch(`${scriptURL}?ip=${encodeURIComponent(data.ip)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      }).then(res => {
        if (res.ok) {
          console.log("✅ Visiteur enregistré dans Google Sheets");
        } else {
          console.warn("❌ Échec de l’enregistrement");
        }
      }).catch(err => console.error("Erreur d’envoi :", err));
    })
    .catch(err => console.error("Erreur IP :", err));
});
