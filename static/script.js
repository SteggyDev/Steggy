document.addEventListener("DOMContentLoaded", function () {
    console.log("Script loaded successfully!");

    let activeForm = document.querySelector(".tool-content.active");

    const writeActionSelector = document.getElementById('write-action-selector');

    function handleSubmit(event) {
        event.preventDefault();

        let formData = new FormData(activeForm);
        let actionUrl = activeForm.getAttribute("action");
        let resultContainer = document.getElementById("result-message");

        resultContainer.innerHTML = `<div class="loading-message">Processing, please wait...</div>`;

        fetch(actionUrl, {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                resultContainer.innerHTML = `<div class="error-message">${data.error}</div>`;
                return;
            }
            resultContainer.innerHTML = "";
            displayResult(resultContainer, data);
        })
        .catch(error => {
            console.error("Error:", error);
            resultContainer.innerHTML = `<div class="error-message">An error occurred. Please try again.</div>`;
        });
    }

    function updateActiveForm(newForm) {
        if (activeForm) {
            activeForm.removeEventListener("submit", handleSubmit);
        }
        activeForm = newForm;
        if (activeForm) {
            activeForm.addEventListener("submit", handleSubmit);
        }
    }

    function setupCheckboxHandlers(container) {
        const useKeyCheckbox = container.querySelector("#use-key-checkbox");
        const decodeKeyCheckbox = container.querySelector("#decode-use-key-checkbox");
        const useMessageCheckbox = container.querySelector("#use-message-checkbox");

        if (useKeyCheckbox) {
            useKeyCheckbox.addEventListener("change", function () {
                const field = container.querySelector("#password-fields");
                if (field) field.style.display = this.checked ? "block" : "none";
            });
        }

        if (decodeKeyCheckbox) {
            decodeKeyCheckbox.addEventListener("change", function () {
                const field = container.querySelector("#decode-password-fields");
                if (field) field.style.display = this.checked ? "block" : "none";
            });
        }

        if (useMessageCheckbox) {
            useMessageCheckbox.addEventListener("change", function () {
                const msgText = container.querySelector("#message-text");
                const filePanel = container.querySelector("#secret-file-panel");
                const uploadContainer = container.querySelector("#upload-container");

                if (msgText) msgText.style.display = this.checked ? "block" : "none";
                if (filePanel) filePanel.style.display = this.checked ? "none" : "block";
                if (uploadContainer) uploadContainer.className = this.checked ? "single-upload-container" : "dual-upload-container";
            });
        }
    }

    document.querySelectorAll(".feature-button").forEach(button => {
        button.addEventListener("click", function () {
            document.getElementById("result-message").innerHTML = "";
            const toolName = this.getAttribute("data-tool");
            console.log(`Tombol ${toolName} diklik!`);
    
            // Hide all tool containers
            document.querySelectorAll(".tool-container").forEach(tool => {
                tool.style.display = "none";
            });
    
            // Show the selected tool container (ensure the ID matches exactly)
            const toolContainer = document.getElementById(`${toolName}-tool`);
            if (toolContainer) {
                toolContainer.style.display = "block";

                const toolTabs = toolContainer.querySelectorAll(".tool-tab");
                const toolContents = toolContainer.querySelectorAll(".tool-content");

                // Only try to switch tabs if .tool-content exists
                if (toolTabs.length && toolContents.length) {
                    toolTabs.forEach(tab => tab.classList.remove("active"));
                    toolContents.forEach(content => content.classList.remove("active"));

                    // Add active to the first tab and content
                    const firstTab = toolTabs[0];
                    const firstContent = toolContents[0];
                    if (firstTab) firstTab.classList.add("active");
                    if (firstContent) firstContent.classList.add("active");

                    // Switch active form
                    if (firstContent) updateActiveForm(firstContent);
                }
                
                //javascript logic only for exiftool
                if (toolName == 'exiftool') {
                    updateWriteFormUI();
                }

                // Re-bind checkboxes only for this tool
                setupCheckboxHandlers(toolContainer);
            } else {
                console.error(`Element #${toolName}-tool tidak ditemukan!`);
            }
        });
    });

    document.querySelectorAll(".tool-tab").forEach(tab => {
        tab.addEventListener("click", function () {
            document.getElementById("result-message").innerHTML = "";
            const selectedTab = this.getAttribute("data-tab");
            const toolContainer = this.closest(".tool-container");
            if (!toolContainer) return;

            const toolTabs = toolContainer.querySelectorAll(".tool-tab");
            const toolContents = toolContainer.querySelectorAll(".tool-content");

            if (toolTabs.length && toolContents.length) {
                // Standard: use .tool-content
                this.classList.add("active");
                const newActiveForm = toolContainer.querySelector(`#${selectedTab}-content`);
                if (newActiveForm) {
                    newActiveForm.classList.add("active");
                    updateActiveForm(newActiveForm);
                }
                // Now remove active from others
                toolTabs.forEach(t => { if (t !== this) t.classList.remove("active"); });
                toolContents.forEach(content => { if (content !== newActiveForm) content.classList.remove("active"); });
            } else {
                // Fallback: show the selected, then hide the rest
                const children = Array.from(toolContainer.children);
                const tabsIdx = children.findIndex(child => child.classList && child.classList.contains("tool-tabs"));
                if (tabsIdx === -1) return;

                const tabIdx = Array.from(toolTabs).indexOf(this);

                // Show the selected one first
                if (tabIdx !== -1 && children[tabsIdx + 1 + tabIdx]) {
                    children[tabsIdx + 1 + tabIdx].style.display = "";
                }
                // Hide all others
                for (let i = tabsIdx + 1; i < children.length; i++) {
                    if (i !== tabsIdx + 1 + tabIdx) {
                        children[i].style.display = "none";
                    }
                }
                // Update tab active state
                this.classList.add("active");
                toolTabs.forEach(t => { if (t !== this) t.classList.remove("active"); });
            }
        });
    });

    if (activeForm) {
        activeForm.addEventListener("submit", handleSubmit);
    }

    function setupFileUpload(dropArea, fileInput) {
        dropArea.addEventListener("click", function () {
            fileInput.click();
        });

        fileInput.addEventListener("change", function () {
            let fileName = this.files[0] ? this.files[0].name : "No file selected";
            dropArea.querySelector("p").textContent = fileName;
        });

        dropArea.addEventListener("dragover", function (e) {
            e.preventDefault();
            dropArea.classList.add("drag-over");
        });

        dropArea.addEventListener("dragleave", function () {
            dropArea.classList.remove("drag-over");
        });

        dropArea.addEventListener("drop", function (e) {
            e.preventDefault();
            dropArea.classList.remove("drag-over");
            fileInput.files = e.dataTransfer.files;
            fileInput.dispatchEvent(new Event("change"));
        });
    }

    document.querySelectorAll(".file-drop-area").forEach(dropArea => {
        let fileInput = dropArea.querySelector("input[type='file']");
        if (fileInput) {
            setupFileUpload(dropArea, fileInput);
        }
    });

    function displayResult(container, data) {
        container.innerHTML = "";
        let successMessage = document.createElement("div");
        successMessage.className = "success-message";
        successMessage.innerText = "Success! Download your file below:";
        container.appendChild(successMessage);
        container.appendChild(document.createElement("br"));

        if (data.preview_type === "image") {
            let img = document.createElement("img");
            img.src = data.display;
            img.alt = "Extracted Image";
            img.style.maxWidth = "100%";
            img.style.marginTop = "10px";
            container.appendChild(img);
        } else if (data.preview_type === "text") {
            let pre = document.createElement("pre");
            pre.innerText = data.display;
            pre.style.padding = "10px";
            pre.style.border = "1px solid #ccc";
            pre.style.color = "#000000";
            pre.style.backgroundColor = "#f9f9f9";
            pre.style.borderRadius = "5px";
            pre.style.marginTop = "10px";
            container.appendChild(pre);
        } else if (data.preview_type === "audio") {
            let audio = document.createElement("audio");
            audio.controls = true;
            audio.style.marginTop = "10px";
            let source = document.createElement("source");
            source.src = data.display;
            source.type = data.mime_type;
            audio.appendChild(source);
            container.appendChild(audio);
        }

        container.appendChild(document.createElement("br"));

        let downloadLink = document.createElement("a");
        downloadLink.href = `data:application/octet-stream;base64,${data.encoded_data}`;
        downloadLink.download = data.filename;
        downloadLink.className = "download-button";
        downloadLink.innerText = `⬇️ Download ${data.filename}`;

        downloadLink.style.display = "inline-block";
        downloadLink.style.padding = "12px 18px";
        downloadLink.style.backgroundColor = "#3498db";
        downloadLink.style.color = "#fff";
        downloadLink.style.textDecoration = "none";
        downloadLink.style.borderRadius = "8px";
        downloadLink.style.fontWeight = "bold";
        downloadLink.style.marginTop = "15px";
        downloadLink.style.textAlign = "center";
        downloadLink.style.cursor = "pointer";

        downloadLink.addEventListener("mouseover", () => downloadLink.style.backgroundColor = "#2980b9");
        downloadLink.addEventListener("mouseout", () => xdownloadLink.style.backgroundColor = "#3498db");

        container.appendChild(downloadLink);
    }

    function updateWriteFormUI() {
        if (!writeActionSelector) return;

        const selectedValue = writeActionSelector.value;
        const optionsPanel = writeActionSelector.closest('.options-panel');
        if (!optionsPanel) return;

        optionsPanel.querySelectorAll('.action-panel').forEach(panel => {
            panel.style.display = 'none';
        });

        const targetPanel = optionsPanel.querySelector(`#action-${selectedValue}`);
        if (targetPanel) {
            if (selectedValue === 'copy-tag') {
                targetPanel.style.display = 'grid';
            } else {
                targetPanel.style.display = 'block';
            }
        }
    }

    if (writeActionSelector) {
        writeActionSelector.addEventListener('change', updateWriteFormUI);
    }
});
