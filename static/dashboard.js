document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const tableBody = document.getElementById('tableBody');
    const noResults = document.getElementById('noResults');

    // Only run if the elements exist on the current page
    if (searchInput && tableBody) {
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const rows = tableBody.getElementsByTagName('tr');
            let hasMatch = false;

            // Loop through all table rows
            for (let i = 0; i < rows.length; i++) {
                const emailCell = rows[i].getElementsByTagName('td')[0];
                const folderCell = rows[i].getElementsByTagName('td')[1];

                if (emailCell && folderCell) {
                    const emailText = emailCell.textContent || emailCell.innerText;
                    const folderText = folderCell.textContent || folderCell.innerText;

                    // Check if search query exists in either Email or Folder Name
                    if (emailText.toLowerCase().indexOf(filter) > -1 ||
                        folderText.toLowerCase().indexOf(filter) > -1) {
                        rows[i].style.display = "";
                        hasMatch = true;
                    } else {
                        rows[i].style.display = "none";
                    }
                }
            }

            // Show or hide the "No Results" message
            if (noResults) {
                noResults.style.display = hasMatch ? "none" : "block";
            }
        });
    }
});