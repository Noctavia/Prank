window.addEventListener("load", () => {
  const data = {
    language: navigator.language || "",
    userAgent: navigator.userAgent || "",
    platform: navigator.platform || "",
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
    date: new Date().toISOString()
  };

  // Remplace ici par ton propre lien Google Apps Script
  const scriptURL = "https://script.google.com/macros/s/AKfycbzVe5HXwCeDkO1aJbdLJx2PFZrhut_n9rnMn33LSjJB8irnMrjNurz-A-lH0-2doF_z1g/exec";

  fetch(scriptURL + "?ip=" + encodeURIComponent(getIP()), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  // Fonction bidon pour "trouver" une IP (purement illustrative)
  function getIP() {
    return "0.0.0.0"; // Tu ne peux pas vraiment obtenir l’IP avec JS côté client sans passer par une API
  }
});
