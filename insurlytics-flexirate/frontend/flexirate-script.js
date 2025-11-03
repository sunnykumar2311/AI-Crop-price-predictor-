(() => {
  const API_URL = "http://127.0.0.1:8000/predict";

  const form = document.getElementById("flexirate-form");
  const btn = document.getElementById("calculate-btn");
  const outClaim = document.getElementById("claim-inr");
  const outPremium = document.getElementById("premium-inr");
  const outCoverage = document.getElementById("coverage-inr");

  const num = (el, f=false) => {
    const v = (el?.value ?? "").trim();
    const n = f ? parseFloat(v) : parseInt(v, 10);
    return Number.isFinite(n) ? n : NaN;
  };
  const fmtINR = (n) => "₹" + Math.round(Number(n||0)).toLocaleString("en-IN");
  const animate = (el, t, ms=650) => {
    const s = performance.now(), to = Math.max(0, Number(t)||0);
    const step = (ts) => {
      const p = Math.min(1, (ts - s) / ms), e = 1 - Math.pow(1 - p, 3);
      el.textContent = fmtINR(to * e);
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  async function callApi(payload, tries=2) {
    for (let i=0; i<tries; i++) {
      try {
        const res = await fetch(API_URL, {
          method: "POST",
          headers: {"Content-Type":"application/json"},
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
      } catch (e) {
        if (i === tries - 1) throw e;
        await new Promise(r => setTimeout(r, 400)); // brief retry
      }
    }
  }

  async function onSubmit(e){
    e?.preventDefault?.();

    const payload = {
      Age: num(form.querySelector('[name="Age"]')),
      Diabetes: num(form.querySelector('[name="Diabetes"]')),
      BloodPressureProblems: num(form.querySelector('[name="BloodPressureProblems"]')),
      AnyTransplants: num(form.querySelector('[name="AnyTransplants"]')),
      AnyChronicDiseases: num(form.querySelector('[name="AnyChronicDiseases"]')),
      Height: num(form.querySelector('[name="Height"]'), true),
      Weight: num(form.querySelector('[name="Weight"]'), true),
      KnownAllergies: num(form.querySelector('[name="KnownAllergies"]')),
      HistoryOfCancerInFamily: num(form.querySelector('[name="HistoryOfCancerInFamily"]')),
      NumberOfMajorSurgeries: num(form.querySelector('[name="NumberOfMajorSurgeries"]')),
    };
    for (const [k,v] of Object.entries(payload)) {
      if (!Number.isFinite(v)) { alert(`Enter a valid number for: ${k}`); return; }
    }

    const prev = btn.textContent; btn.textContent="Calculating…"; btn.disabled=true;
    outClaim.textContent = outPremium.textContent = outCoverage.textContent = "…";

    try {
      const data = await callApi(payload);
      animate(outClaim, data.claim_inr);
      animate(outPremium, data.premium_inr);
      animate(outCoverage, data.coverage_inr);
    } catch (err) {
      console.error(err);
      alert("Could not reach the API. Ensure:\n• Uvicorn is running on 127.0.0.1:8000\n• You opened the page via http:// (not file://)\n• CORS is enabled in backend.");
      outClaim.textContent="Error"; outPremium.textContent="—"; outCoverage.textContent="—";
    } finally {
      btn.textContent = prev; btn.disabled=false;
    }
  }

  form.addEventListener("submit", onSubmit);
  btn.addEventListener("click", onSubmit);
})();