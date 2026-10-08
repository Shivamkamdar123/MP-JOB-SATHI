console.log("MP Job Saathi extension loaded");

const fieldMap = {
  candidate_name: ["candidate_name", "name", "full_name"],
  dob: ["dob", "date_of_birth", "dateofbirth"],
  category: ["category", "candidate_category"],
  gender: ["gender", "sex"],
};

const loadProfile = () => {
  try {
    const fromStorage = localStorage.getItem("mp-job-saathi-profile");
    if (!fromStorage) {
      return null;
    }
    return JSON.parse(fromStorage);
  } catch (error) {
    return null;
  }
};

const applyPreFill = () => {
  const profile = loadProfile();
  if (!profile) {
    return;
  }

  Object.entries(fieldMap).forEach(([key, selectors]) => {
    const fillValue = profile[key];
    if (!fillValue) {
      return;
    }

    const selector = selectors
      .map((name) => `input[name="${name}"]`)
      .concat(selectors.map((name) => `#${name}`))
      .find((candidateSelector) =>
        Boolean(document.querySelector(candidateSelector)),
      );

    if (!selector) {
      return;
    }

    const input = document.querySelector(selector);
    if (input && !input.value) {
      input.value = fillValue;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.setAttribute("data-mp-job-saathi-prefilled", "true");
    }
  });
};

if (document.readyState === "complete") {
  applyPreFill();
} else {
  window.addEventListener("load", applyPreFill);
}
