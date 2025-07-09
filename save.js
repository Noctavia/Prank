window.addEventListener("load", () => {
  const data = {
    language: navigator.language || "",
    userAgent: navigator.userAgent || "",
    platform: navigator.platform || "",
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
    date: new Date().toISOString()
  };

  fetch("http://localhost:5000/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  })
    .then(res => res.json())
    .then(res => console.log("✅ Données enregistrées :", res))
    .catch(err => console.error("❌ Erreur d'envoi :", err));
});
