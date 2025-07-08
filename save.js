// save.js

window.addEventListener("load", () => {
  const data = {
    language: navigator.language || "",
    userAgent: navigator.userAgent || "",
    platform: navigator.platform || "",
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
    date: new Date().toISOString()
  };

  fetch("save.php", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });
});
