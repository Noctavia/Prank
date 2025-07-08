window.addEventListener("load", () => {
  // API pour récupérer l'IP publique
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

      // Ton lien Google Apps Script
      const scriptURL = "https://script.google.com/macros/s/AKfycbzVe5HXwCeDkO1aJbdLJx2PFZrhut_n9rnMn33LSjJB8irnMrjNurz-A-lH0-2doF_z1g/exec";

      // Envoi POST
      fetch(`${scriptURL}?ip=${encodeURIComponent(data.ip)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      }).then(response => {
        if (response.ok) {
          console.log("✅ Données envoyées à Google Sheets");
        } else {
          console.error("❌ Échec lors de l'envoi");
        }
      }).catch(err => console.error("Erreur : ", err));
    })
    .catch(err => {
      console.error("Erreur IP : ", err);
    });
});
