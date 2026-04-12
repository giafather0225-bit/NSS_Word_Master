(function() {
    "use strict";
    var $ = function(id) { return document.getElementById(id); };
    var currentTextbook = "Voca_8000";
    var currentLesson = null;
    var folderData = null;
    var editedWords = null;
    var isDirty = false;

    function esc(s) {
        var d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }

    // --- Sidebar ---
    async function loadTextbooks() {
        try {
            var res = await fetch("/api/textbooks/English");
            var data = await res.json();
            var sel = $("textbook-select");
            sel.innerHTML = "";
            (data.textbooks || []).filter(function(tb) { return tb !== "My_Words"; }).forEach(function(tb) {
                var opt = document.createElement("option");
                opt.value = tb;
                opt.textContent = tb;
                if (tb === currentTextbook) opt.selected = true;
                sel.appendChild(opt);
            });
            sel.onchange = function() {
                currentTextbook = this.value;
                currentLesson = null;
                isDirty = false;
                $("welcome-state").style.display = "";
                $("lesson-detail").classList.remove("visible");
                $("btn-delete-folder").style.display = "none";
                loadTextbooks();
    loadFolders();
            };
        } catch(e) { console.error("loadTextbooks:", e); }
    }

    async function loadFolders() {
        try {
            var res = await fetch("/api/voca/folders?textbook=" + encodeURIComponent(currentTextbook));
            var data = await res.json();
            renderFolderList(data.folders || []);
        } catch(e) { console.error("loadFolders:", e); }
    }

    function renderFolderList(folders) {
        var list = $("folder-list");
        list.innerHTML = "";
        if (!folders.length) {
            list.innerHTML = "<li style='padding:16px;color:#999;font-size:13px;'>No lessons yet.</li>";
            return;
        }
        folders.forEach(function(f) {
            var li = document.createElement("li");
            li.className = "folder-item" + (currentLesson === f.name ? " active" : "");
            var badges = "";
            if (f.image_count > 0) badges += "<span class='badge badge-img'>" + f.image_count + " img</span>";
            if (f.word_count > 0) badges += "<span class='badge badge-word'>" + f.word_count + " w</span>";
            if (f.image_count === 0 && f.word_count === 0) badges += "<span class='badge badge-empty'>empty</span>";
            li.innerHTML = "<div class='folder-name'>" + esc(f.name) + "</div>"
                + "<div class='folder-badges'>" + badges + "</div>";
            li.addEventListener("click", function() {
                if (isDirty && !confirm("Unsaved changes will be lost. Continue?")) return;
                selectLesson(f.name);
            });
            list.appendChild(li);
        });
    }

    // --- Select lesson ---
    async function selectLesson(name) {
        currentLesson = name;
        isDirty = false;
        $("welcome-state").style.display = "none";
        $("lesson-detail").classList.add("visible");
        document.querySelectorAll(".folder-item").forEach(function(el) {
            el.classList.toggle("active", el.querySelector(".folder-name").textContent === name);
        });
        await loadLessonDetail(name);
    }

    async function loadLessonDetail(lesson) {
        try {
            var res = await fetch("/api/voca/folder-detail/" + encodeURIComponent(lesson) + "?textbook=" + encodeURIComponent(currentTextbook));
            folderData = await res.json();
            editedWords = JSON.parse(JSON.stringify(folderData.words || []));
            isDirty = false;
            document.getElementById("btn-delete-folder").style.display = "inline-block";
            $("detail-title").textContent = folderData.lesson;
            $("detail-path").textContent = folderData.path;
            $("img-count").textContent = folderData.image_count + " images";
            $("btn-run-folder-ocr").disabled = folderData.image_count === 0;
            renderImages(folderData.images || []);
            renderWords();
            updateWordCount();
            hideStatus();
        } catch(e) { console.error("loadLessonDetail:", e); }
    }

    function updateWordCount() {
        $("word-count").textContent = editedWords.length + " words" + (isDirty ? " *" : "");
    }

    // --- Images ---
    function renderImages(images) {
        var grid = $("image-grid");
        grid.innerHTML = "";
        images.forEach(function(img) {
            var card = document.createElement("div");
            card.className = "image-card";
            var isHeic = img.ext === ".heic" || img.ext === ".heif";
            var inner = "";
            if (isHeic) {
                inner = "<div class='heic-placeholder'>HEIC</div>";
            } else {
                inner = "<img src='/api/voca/folder-image/" + encodeURIComponent(currentLesson) + "/" + encodeURIComponent(img.name)
                    + "' onerror=\"this.style.display='none';this.nextElementSibling.style.display='block';\">"
                    + "<div class='heic-placeholder' style='display:none;'>IMG</div>";
            }
            inner += "<div class='img-name'>" + esc(img.name) + "</div>";
            inner += "<button class='btn-del-img' title='Delete'>&times;</button>";
            card.innerHTML = inner;
            card.querySelector(".btn-del-img").addEventListener("click", function(e) {
                e.stopPropagation();
                if (isDirty) {
                    if (!confirm("You have unsaved word changes!\nSave first, or they will be lost.\n\nContinue deleting image anyway?")) return;
                }
                if (!confirm("Delete " + img.name + "?")) return;
                fetch("/api/voca/folder-image/" + encodeURIComponent(currentLesson) + "/" + encodeURIComponent(img.name) + "?textbook=" + encodeURIComponent(currentTextbook), {method:"DELETE"})
                    .then(function() { loadLessonDetail(currentLesson); loadFolders(); })
                    .catch(function(err) { alert("Delete failed: " + err.message); });
            });
            grid.appendChild(card);
        });
    }

    // --- Editable Word table ---
    function renderWords() {
        var tbody = $("word-tbody");
        var table = $("word-table");
        var empty = $("words-empty");
        var toolbar = $("word-toolbar");

        if (!editedWords.length) {
            table.style.display = "none";
            empty.style.display = "block";
            if (toolbar) toolbar.style.display = "none";
            return;
        }
        empty.style.display = "none";
        table.style.display = "table";
        if (toolbar) toolbar.style.display = "flex";
        tbody.innerHTML = "";

        editedWords.forEach(function(w, i) {
            var tr = document.createElement("tr");
            tr.innerHTML = "<td style='color:var(--text-secondary);text-align:center;'>" + (i+1) + "</td>"
                + "<td><input class='word-edit word-field' data-idx='" + i + "' data-key='word' value='" + esc(w.word || "") + "'></td>"
                + "<td><input class='word-edit pos-field' data-idx='" + i + "' data-key='pos' value='" + esc(w.pos || "") + "' style='width:70px;text-align:center;'></td>"
                + "<td><input class='word-edit def-field' data-idx='" + i + "' data-key='definition' value='" + esc(w.definition || "") + "'></td>"
                + "<td><input class='word-edit ex-field' data-idx='" + i + "' data-key='example' value='" + esc(w.example || "") + "'></td>"
                + "<td style='text-align:center;'><button class='btn-del-word' data-idx='" + i + "' title='Delete word'>&times;</button></td>";
            tbody.appendChild(tr);
        });

        // Bind edit events
        tbody.querySelectorAll(".word-edit").forEach(function(inp) {
            inp.addEventListener("input", function() {
                var idx = parseInt(this.dataset.idx);
                var key = this.dataset.key;
                editedWords[idx][key] = this.value;
                markDirty();
            });
        });

        // Bind delete events
        tbody.querySelectorAll(".btn-del-word").forEach(function(btn) {
            btn.addEventListener("click", function() {
                var idx = parseInt(this.dataset.idx);
                var word = editedWords[idx].word || "(empty)";
                if (!confirm("Delete \"" + word + "\"?")) return;
                editedWords.splice(idx, 1);
                markDirty();
                renderWords();
                updateWordCount();
            });
        });
    }

    function markDirty() {
        isDirty = true;
        updateWordCount();
        showSaveBar();
    }

    function showSaveBar() {
        $("status-text").textContent = "You have unsaved changes.";
        $("status-spinner").style.display = "none";
        $("btn-save-words").style.display = "inline-block";
        $("btn-discard").style.display = "inline-block";
        $("status-bar").classList.add("visible");
    }

    // --- Add word ---
    function initAddWord() {
        $("btn-delete-all-words").addEventListener("click", function() {
            if (!editedWords.length) { alert("No words to delete."); return; }
            if (!confirm("Delete all " + editedWords.length + " words?")) return;
            var autoSave = confirm("Save immediately?\n\nOK = Save now (clear data.json + DB)\nCancel = Edit more before saving");
            editedWords = [];
            if (autoSave) {
                // Auto save empty list
                var fd = new FormData();
                fd.append("lesson", currentLesson);
                fd.append("textbook", currentTextbook);
                fd.append("words_json", "[]");
                fetch("/api/voca/save-reviewed", {method:"POST", body:fd})
                    .then(function(r) { return r.json(); })
                    .then(function() {
                        isDirty = false;
                        loadLessonDetail(currentLesson);
                        loadFolders();
                        showStatus("All words deleted and saved.", false);
                        setTimeout(hideStatus, 2000);
                    })
                    .catch(function(e) { showStatus("Save failed: " + e.message, false); });
            } else {
                markDirty();
            }
            renderWords();
            updateWordCount();
        });
        $("btn-add-word").addEventListener("click", function() {
            editedWords.push({word:"", pos:"", definition:"", example:""});
            markDirty();
            renderWords();
            updateWordCount();
            // Scroll to bottom and focus new row
            var tbody = $("word-tbody");
            var lastInput = tbody.querySelector("tr:last-child .word-field");
            if (lastInput) {
                lastInput.scrollIntoView({behavior:"smooth"});
                setTimeout(function() { lastInput.focus(); }, 200);
            }
        });
    }

    // --- Drop zone ---
    function initDropZone() {
        var zone = $("image-drop-zone");
        var input = $("image-file-input");
        zone.addEventListener("click", function(e) {
            if (e.target === input) return;
            input.click();
        });
        zone.addEventListener("dragover", function(e) { e.preventDefault(); zone.classList.add("dragover"); });
        zone.addEventListener("dragleave", function() { zone.classList.remove("dragover"); });
        zone.addEventListener("drop", function(e) {
            e.preventDefault();
            zone.classList.remove("dragover");
            if (!currentLesson) { alert("Select a lesson first."); return; }
            uploadFiles(e.dataTransfer.files);
        });
        input.addEventListener("change", function() {
            if (!currentLesson) { alert("Select a lesson first."); return; }
            if (input.files.length) uploadFiles(input.files);
            input.value = "";
        });
    }

    async function uploadFiles(fileList) {
        if (!currentLesson) return;
        showStatus("Uploading " + fileList.length + " file(s)...");
        var fd = new FormData();
        for (var i = 0; i < fileList.length; i++) fd.append("files", fileList[i]);
        try {
            var res = await fetch("/api/voca/folder-upload/" + encodeURIComponent(currentLesson) + "?textbook=" + encodeURIComponent(currentTextbook), {method:"POST", body:fd});
            var data = await res.json();
            showStatus("Uploaded " + data.count + " file(s)", false);
            await loadLessonDetail(currentLesson);
            loadFolders();
            setTimeout(hideStatus, 2000);
        } catch(e) {
            showStatus("Upload failed: " + e.message, false);
        }
    }

    // --- OCR ---
    function initOCR() {
        $("btn-run-folder-ocr").addEventListener("click", async function() {
            if (!currentLesson || !folderData) return;
            var imgCount = folderData.image_count || 0;
            if (!imgCount) { alert("No images to process."); return; }
            if (!confirm("Run OCR on " + imgCount + " image(s) in " + currentLesson + "?\nEstimated: ~" + (imgCount*10) + "s")) return;
            var btn = $("btn-run-folder-ocr");
            btn.disabled = true;
            btn.textContent = "Running OCR...";
            showStatus("Running OCR on " + imgCount + " image(s)... (~" + (imgCount*10) + "s)");
            $("ocr-progress").style.display = "block";
            var progress = 0;
            var iv = setInterval(function() {
                progress = Math.min(progress + 100/(imgCount*10), 95);
                $("ocr-progress-fill").style.width = progress + "%";
            }, 1000);
            try {
                var res = await fetch("/api/voca/folder-ocr/" + encodeURIComponent(currentLesson) + "?textbook=" + encodeURIComponent(currentTextbook), {method:"POST"});
                clearInterval(iv);
                $("ocr-progress-fill").style.width = "100%";
                if (!res.ok) {
                    var err = await res.json();
                    throw new Error(err.detail || "OCR failed");
                }
                var data = await res.json();
                showStatus("Done! " + data.word_count + " words from " + data.images_processed + " image(s).", false, true);
                await loadLessonDetail(currentLesson);
                loadFolders();
                setTimeout(hideStatus, 3000);
            } catch(e) {
                clearInterval(iv);
                showStatus("OCR failed: " + e.message, false);
            } finally {
                btn.disabled = false;
                btn.textContent = "Run OCR on All Images";
                setTimeout(function() {
                    $("ocr-progress").style.display = "none";
                    $("ocr-progress-fill").style.width = "0%";
                }, 2000);
            }
        });
    }

    // --- New lesson ---
    
    // --- Delete Lesson Folder ---
    function initDeleteFolder() {
        var btn = document.getElementById("btn-delete-folder");
        if (!btn) return;
        btn.addEventListener("click", async function() {
            if (!currentLesson) return;
            if (!confirm("Delete folder '" + currentLesson + "' and all its data?\nThis cannot be undone!")) return;
            try {
                var res = await fetch("/api/voca/folder/" + encodeURIComponent(currentLesson) + "?textbook=" + encodeURIComponent(currentTextbook), {method:"DELETE"});
                if (!res.ok) throw new Error("Delete failed");
                currentLesson = null;
                await loadTextbooks();
        await loadFolders();
                document.getElementById("lesson-detail").innerHTML = "<p style='color:#888;text-align:center;margin-top:60px;'>Select a lesson</p>";
            } catch(e) {
                alert("Delete failed: " + e.message);
            }
        });
    }

    function initNewLesson() {
        $("btn-new-lesson").addEventListener("click", async function() {
            var name = prompt("Enter lesson name:", "Lesson_");
            if (!name) return;
            if (!/^Lesson_\d{1,3}$/.test(name.trim())) {
                alert("Format: Lesson_XX (e.g. Lesson_05)");
                return;
            }
            try {
                var res = await fetch("/api/voca/create-lesson/" + encodeURIComponent(name.trim()) + "?textbook=" + encodeURIComponent(currentTextbook), {method:"POST"});
                if (!res.ok) throw new Error("Failed");
                await loadTextbooks();
        await loadFolders();
                selectLesson(name.trim());
            } catch(e) { alert("Failed: " + e.message); }
        });
    }

    // --- Status bar ---
    function showStatus(text, showSpinner, showSave) {
        if (showSpinner === undefined) showSpinner = true;
        if (showSave === undefined) showSave = false;
        $("status-text").textContent = text;
        $("status-spinner").style.display = showSpinner ? "block" : "none";
        $("btn-save-words").style.display = showSave ? "inline-block" : "none";
        $("btn-discard").style.display = "none";
        $("status-bar").classList.add("visible");
    }
    function hideStatus() {
        $("status-bar").classList.remove("visible");
    }

    // --- Save ---
    function initSave() {
        $("btn-save-words").addEventListener("click", async function() {
            if (!currentLesson) return;
            // Filter out empty words
            var cleaned = editedWords.filter(function(w) { return w.word && w.word.trim(); });
            showStatus("Saving " + cleaned.length + " words...");
            try {
                var fd = new FormData();
                fd.append("lesson", currentLesson);
                fd.append("textbook", currentTextbook);
                fd.append("words_json", JSON.stringify(cleaned));
                var res = await fetch("/api/voca/save-reviewed", {method:"POST", body:fd});
                if (!res.ok) throw new Error("Save failed");
                var data = await res.json();
                isDirty = false;
                showStatus("Saved " + data.synced + " words to DB.", false);
                await loadLessonDetail(currentLesson);
                loadFolders();
                setTimeout(hideStatus, 2000);
            } catch(e) {
                showStatus("Save failed: " + e.message, false);
            }
        });

        $("btn-discard").addEventListener("click", function() {
            if (!confirm("Discard all changes?")) return;
            editedWords = JSON.parse(JSON.stringify(folderData.words || []));
            isDirty = false;
            renderWords();
            updateWordCount();
            hideStatus();
        });
    }

    // --- Init ---
    async function init() {
        await loadTextbooks();
        await loadFolders();
        initDropZone();
        initOCR();
        initNewLesson();
        initDeleteFolder();
        initAddWord();
        initSave();
    }
    init();
})();
