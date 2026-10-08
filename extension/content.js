console.log("MP Job Saathi extension loaded");

const fieldMap = {
  name: ["candidate_name", "name"],
  dob: ["dob", "date_of_birth"],
  category: ["category"],
};

const applyPreFill = () => {
  for (const [key, selectors] of Object.entries(fieldMap)) {
    const match = selectors.find((selector) => {
      const el = document.querySelector(`input[name="${selector}"]`);
      return Boolean(el);
    });
    if (match) {
      const input = document.querySelector(`input[name="${match}"]`);
      if (input) {
        input.setAttribute("data-mp-job-saathi-prefilled", "true");
      }
    }
  }
};

if (document.readyState === "complete") {
  applyPreFill();
} else {
  window.addEventListener("load", applyPreFill);
}
