(() => {
  const dropZone = document.getElementById("dropZone");
  const resumeFile = document.getElementById("resumeFile");
  const fileInfo = document.getElementById("fileInfo");
  const jobDescription = document.getElementById("jobDescription");
  const charCount = document.getElementById("charCount");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const resultsPanel = document.getElementById("resultsPanel");
  const themeToggle = document.getElementById("themeToggle");
  const sunIcon = document.getElementById("sunIcon");
  const moonIcon = document.getElementById("moonIcon");
  const toast = document.getElementById("toast");

  let selectedFile = null;

  const savedTheme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeIcons(savedTheme);

  themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    updateThemeIcons(next);
  });

  function updateThemeIcons(theme) {
    if (theme === "dark") {
      sunIcon.style.display = "block";
      moonIcon.style.display = "none";
    } else {
      sunIcon.style.display = "none";
      moonIcon.style.display = "block";
    }
  }

  dropZone.addEventListener("click", () => resumeFile.click());
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
      handleFile(e.dataTransfer.files[0]);
    }
  });
  resumeFile.addEventListener("change", () => {
    if (resumeFile.files.length) handleFile(resumeFile.files[0]);
  });

  function handleFile(file) {
    const allowed = [".pdf", ".txt", ".docx"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!allowed.includes(ext)) {
      showToast("Unsupported file type. Use PDF, DOCX or TXT.", "error");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      showToast("File too large. Maximum 10 MB.", "error");
      return;
    }
    selectedFile = file;
    fileInfo.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
    fileInfo.classList.remove("hidden");
    updateButtonState();
  }

  jobDescription.addEventListener("input", () => {
    charCount.textContent = jobDescription.value.length;
    updateButtonState();
  });

  function updateButtonState() {
    const ready = selectedFile && jobDescription.value.trim().length >= 50;
    analyzeBtn.disabled = !ready;
  }

  analyzeBtn.addEventListener("click", async () => {
    if (!selectedFile || jobDescription.value.trim().length < 50) return;

    setLoading(true);
    resultsPanel.classList.add("hidden");

    const formData = new FormData();
    formData.append("resume", selectedFile);
    formData.append("job_description", jobDescription.value.trim());

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Analysis failed" }));
        throw new Error(err.detail || `Request failed (${res.status})`);
      }

      const data = await res.json();
      renderResults(data);
      resultsPanel.classList.remove("hidden");
      showToast("Analysis completed successfully", "success");
    } catch (err) {
      showToast(err.message || "Something went wrong", "error");
    } finally {
      setLoading(false);
    }
  });

  function setLoading(loading) {
    analyzeBtn.disabled = loading;
    const text = analyzeBtn.querySelector(".btn-text");
    const loader = analyzeBtn.querySelector(".btn-loader");
    if (loading) {
      text.classList.add("hidden");
      loader.classList.remove("hidden");
    } else {
      text.classList.remove("hidden");
      loader.classList.add("hidden");
      updateButtonState();
    }
  }

  function renderResults(data) {
    document.getElementById("processTime").textContent =
      `Processed in ${data.processing_time_ms} ms`;

    const overall = data.ats_score.overall_score;
    document.getElementById("overallScore").textContent = overall.toFixed(1);
    document.getElementById("scoreRing").setAttribute(
      "stroke-dasharray",
      `${overall}, 100`
    );
    document.getElementById("similarityScore").textContent =
      data.similarity_score.toFixed(1) + "%";
    document.getElementById("skillMatchScore").textContent =
      data.skill_gap.match_percentage.toFixed(1) + "%";
    document.getElementById("rankingScore").textContent =
      data.ranking_score.toFixed(1);

    const c = data.candidate;
    const profileHtml = [
      c.name ? row("Name", c.name) : "",
      c.email ? row("Email", c.email) : "",
      c.phone ? row("Phone", c.phone) : "",
      c.experience_years != null ? row("Experience", c.experience_years + " years") : "",
      c.education && c.education.length ? row("Education", c.education.join("; ")) : "",
      row("Skills found", c.extracted_skills.length),
      c.summary ? row("Summary", c.summary.slice(0, 180) + (c.summary.length > 180 ? "…" : "")) : ""
    ].filter(Boolean).join("");
    document.getElementById("candidateProfile").innerHTML = profileHtml || "<span class='text-muted'>No structured profile data extracted</span>";

    const breakdown = [
      ["Keyword Match", data.ats_score.keyword_match],
      ["Skills Coverage", data.ats_score.skills_coverage],
      ["Experience", data.ats_score.experience_relevance],
      ["Formatting", data.ats_score.formatting_score],
      ["Sections", data.ats_score.section_completeness]
    ];
    document.getElementById("atsBreakdown").innerHTML = breakdown
      .map(([label, val]) => `
        <div class="bar-row">
          <span>${label}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${val}%"></div></div>
          <span>${val.toFixed(0)}</span>
        </div>
      `).join("");

    const domainHtml = `
      <div class="domain-badge">${escapeHtml(data.domain.domain)}</div>
      <div class="domain-list">Confidence: ${data.domain.confidence.toFixed(1)}%</div>
      ${data.domain.top_domains && data.domain.top_domains.length ? `
        <div class="domain-list" style="margin-top:8px">
          ${data.domain.top_domains.slice(0, 3).map(d => `${escapeHtml(d.domain)}: ${d.confidence.toFixed(1)}%`).join(" · ")}
        </div>` : ""}
    `;
    document.getElementById("domainInfo").innerHTML = domainHtml;

    document.getElementById("matchedSkills").innerHTML =
      data.skill_gap.matched_skills.length
        ? data.skill_gap.matched_skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join("")
        : "<span style='color:var(--text-muted)'>No direct skill matches</span>";

    document.getElementById("missingSkills").innerHTML =
      data.skill_gap.missing_skills.length
        ? data.skill_gap.missing_skills.map(s => `<span class="skill-tag gap">${escapeHtml(s)}</span>`).join("")
        : "<span style='color:var(--success)'>No critical skill gaps detected</span>";

    document.getElementById("recommendations").innerHTML =
      data.recommendations.map(r => `<li>${escapeHtml(r)}</li>`).join("");

    document.getElementById("matchedKeywords").innerHTML =
      data.matched_keywords.length
        ? data.matched_keywords.slice(0, 18).map(k => `<span class="skill-tag keywords">${escapeHtml(k)}</span>`).join("")
        : "<span style='color:var(--text-muted)'>No strong keyword overlap</span>";
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    })[char]);
  }

  function row(label, value) {
    return `<div class="profile-row"><span class="label">${escapeHtml(label)}</span><span>${escapeHtml(value)}</span></div>`;
  }

  function showToast(message, type = "success") {
    toast.textContent = message;
    toast.className = `toast ${type}`;
    setTimeout(() => toast.classList.add("hidden"), 4200);
  }
})();