window.addEventListener("load", () => {
  fetch("https://api64.ipify.org?format=json")
    .then(res => res.json())
    .then(ipData => {
      const data = {
        ip: ipData.ip || "0.0.0.0",
        language: navigator.language || "",
        userAgent: navigator.userAgent || "",
        platform: navigator.platform || "",
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
        date: new Date().toISOString()
      };

      fetch("http://localhost:5000/save", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
      })
      .then(res => {
        if (res.ok) console.log("✅ Visiteur enregistré !");
        else console.warn("❌ Échec de l’enregistrement");
      })
      .catch(err => console.error("Erreur d’envoi :", err));
    })
    .catch(err => console.error("Erreur IP :", err));
});
