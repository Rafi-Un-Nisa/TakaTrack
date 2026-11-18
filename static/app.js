// Owner: Hrishika.
// Live caution on the "Add expense" page: asks the server while the user types.
(function () {
  var form = document.getElementById("expense-form");
  if (!form) return;
  var box = document.getElementById("live-caution");
  var timer = null;

  async function check() {
    var category = form.category.value.trim();
    var amount = form.amount.value;
    if (!category || !amount) { box.hidden = true; return; }
    var params = new URLSearchParams({ category: category, amount: amount, date: form.spent_on.value });
    try {
      var response = await fetch("/api/check?" + params.toString());
      if (!response.ok) return;
      var data = await response.json();
      if (data.warnings.length) {
        box.textContent = "\u26A0 " + data.warnings.join(" ");
        box.hidden = false;
      } else {
        box.hidden = true;
      }
    } catch (e) { /* ignore network errors */ }
  }

  ["input", "change"].forEach(function (eventName) {
    form.addEventListener(eventName, function () {
      clearTimeout(timer);
      timer = setTimeout(check, 300);
    });
  });
})();
