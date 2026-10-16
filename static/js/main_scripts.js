// Live search: filters the book cards on the current page while you type.
// Press Enter to search the whole library (the form sends ?q=... to the book list).
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("book-search");
    if (!searchInput) return;

    const cards = document.querySelectorAll(".book-card");
    if (!cards.length) return;                    // nothing to filter on this page

    const shelves = document.querySelectorAll(".shelf");
    const noResults = document.getElementById("no-results");

    searchInput.addEventListener("input", function () {
        const query = searchInput.value.trim().toLowerCase();
        let visibleCount = 0;

        cards.forEach(function (card) {
            const matches = card.textContent.toLowerCase().includes(query);
            card.classList.toggle("is-hidden", !matches);
            if (matches) visibleCount++;
        });

        // hide a category heading when all of its books are filtered out
        shelves.forEach(function (shelf) {
            const anyVisible = shelf.querySelector(".book-card:not(.is-hidden)");
            shelf.classList.toggle("is-hidden", !anyVisible);
        });

        if (noResults) noResults.hidden = visibleCount > 0;
    });
});


// Share menu on the book page: copy the link, close the menu when you click elsewhere.
document.addEventListener("DOMContentLoaded", function () {
    const share = document.querySelector("details.share");
    if (!share) return;                            // not a book page

    // Close on outside click or Escape
    document.addEventListener("click", function (event) {
        if (share.open && !share.contains(event.target)) share.open = false;
    });
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && share.open) {
            share.open = false;
            share.querySelector("summary").focus();
        }
    });

    // "Copy link" button
    const copyButton = share.querySelector("[data-copy-link]");
    if (!copyButton) return;
    const label = copyButton.querySelector("[data-copy-label]");

    copyButton.addEventListener("click", async function () {
        const link = copyButton.dataset.copyLink;
        let copied = false;

        try {
            await navigator.clipboard.writeText(link);
            copied = true;
        } catch (error) {
            // Older browsers / non-secure pages: use a hidden text box instead
            const box = document.createElement("textarea");
            box.value = link;
            box.style.position = "fixed";
            box.style.opacity = "0";
            document.body.appendChild(box);
            box.select();
            try { copied = document.execCommand("copy"); } catch (e) { copied = false; }
            box.remove();
        }

        label.textContent = copied ? "Link copied!" : "Copy failed";
        setTimeout(function () { label.textContent = "Copy link"; }, 2000);
    });
});
