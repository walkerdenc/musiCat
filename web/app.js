const DATA_PATHS = {
  plugins: "../catalog/plugins.json",
  samples: "../catalog/samples.json",
  notes: "../catalog/notes.json",
};

const state = {
  plugins: [],
  samples: [],
  notes: {
    plugins: {},
    samples: {},
  },
  selected: null,
};

const elements = {
  pluginList: document.getElementById("plugin-list"),
  pluginSearch: document.getElementById("plugin-search"),
  sampleSearch: document.getElementById("sample-search"),
  sampleTree: document.getElementById("sample-tree"),
  detailsForm: document.getElementById("details-form"),
  detailsEmpty: document.getElementById("details-empty"),
  itemName: document.getElementById("item-name"),
  itemType: document.getElementById("item-type"),
  itemDescription: document.getElementById("item-description"),
  itemTags: document.getElementById("item-tags"),
  itemMeta: document.getElementById("item-meta"),
  saveNotes: document.getElementById("save-notes"),
  exportNotes: document.getElementById("export-notes"),
  importNotes: document.getElementById("import-notes"),
  resetNotes: document.getElementById("reset-notes"),
};

const LOCAL_NOTES_KEY = "sound-catalog-notes";

const fetchJson = async (path) => {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return response.json();
};

const loadData = async () => {
  const [pluginsData, samplesData, notesData] = await Promise.all([
    fetchJson(DATA_PATHS.plugins),
    fetchJson(DATA_PATHS.samples),
    fetchJson(DATA_PATHS.notes),
  ]);

  const storedNotes = loadNotesFromStorage();
  state.plugins = pluginsData.plugins || [];
  state.samples = samplesData.nodes || [];
  state.notes = mergeNotes(notesData, storedNotes);
};

const mergeNotes = (baseNotes, storedNotes) => {
  return {
    plugins: { ...(baseNotes.plugins || {}), ...(storedNotes.plugins || {}) },
    samples: { ...(baseNotes.samples || {}), ...(storedNotes.samples || {}) },
  };
};

const loadNotesFromStorage = () => {
  const raw = localStorage.getItem(LOCAL_NOTES_KEY);
  if (!raw) {
    return { plugins: {}, samples: {} };
  }
  try {
    return JSON.parse(raw);
  } catch (error) {
    console.warn("Failed to parse stored notes", error);
    return { plugins: {}, samples: {} };
  }
};

const saveNotesToStorage = () => {
  localStorage.setItem(LOCAL_NOTES_KEY, JSON.stringify(state.notes, null, 2));
};

const normalizeText = (value) => value.toLowerCase();

const renderPlugins = () => {
  const query = normalizeText(elements.pluginSearch.value || "");
  elements.pluginList.innerHTML = "";
  const filtered = state.plugins.filter((plugin) =>
    normalizeText(plugin.name).includes(query),
  );

  filtered.forEach((plugin) => {
    const item = document.createElement("li");
    item.className = "list-item";
    item.dataset.key = plugin.name;
    item.innerHTML = `
      <strong>${plugin.name}</strong>
      <div><small>${plugin.vendor || "Unknown vendor"} · ${plugin.type.toUpperCase()}</small></div>
    `;
    item.addEventListener("click", () => selectItem("plugin", plugin));
    elements.pluginList.appendChild(item);
  });
};

const buildSampleTree = (nodes) => {
  const root = { name: "root", children: new Map(), path: "" };
  nodes.forEach((node) => {
    const segments = node.path.split("/").filter(Boolean);
    let current = root;
    let currentPath = "";
    segments.forEach((segment) => {
      currentPath = currentPath ? `${currentPath}/${segment}` : segment;
      if (!current.children.has(segment)) {
        current.children.set(segment, {
          name: segment,
          children: new Map(),
          path: currentPath,
        });
      }
      current = current.children.get(segment);
    });
  });
  return root;
};

const renderSampleTree = () => {
  const query = normalizeText(elements.sampleSearch.value || "");
  const filteredNodes = state.samples.filter((node) =>
    normalizeText(node.path).includes(query),
  );
  const tree = buildSampleTree(filteredNodes);
  elements.sampleTree.innerHTML = "";
  tree.children.forEach((child) => {
    elements.sampleTree.appendChild(renderTreeNode(child));
  });
};

const renderTreeNode = (node) => {
  const container = document.createElement("div");
  container.className = "tree-node";

  const label = document.createElement("div");
  label.className = "tree-label";

  const toggle = document.createElement("span");
  toggle.textContent = node.children.size ? "▸" : "•";

  const name = document.createElement("span");
  name.textContent = node.name;

  label.appendChild(toggle);
  label.appendChild(name);
  container.appendChild(label);

  label.addEventListener("click", () => {
    selectItem("sample", { path: node.path });
    if (!node.children.size) {
      return;
    }
    const isOpen = container.classList.toggle("open");
    toggle.textContent = isOpen ? "▾" : "▸";
    childrenContainer.hidden = !isOpen;
  });

  if (node.children.size) {
    const childrenContainer = document.createElement("div");
    childrenContainer.className = "tree-children";
    childrenContainer.hidden = true;
    node.children.forEach((child) => {
      childrenContainer.appendChild(renderTreeNode(child));
    });
    container.appendChild(childrenContainer);
  }

  return container;
};

const selectItem = (kind, data) => {
  state.selected = { kind, key: kind === "plugin" ? data.name : data.path };
  elements.detailsEmpty.hidden = true;
  elements.detailsForm.hidden = false;

  const notes = kind === "plugin" ? state.notes.plugins : state.notes.samples;
  const key = state.selected.key;
  const note = notes[key] || {};

  elements.itemName.value = key;
  elements.itemType.value = kind === "plugin" ? data.type || "plugin" : "sample";
  elements.itemDescription.value = note.description || "";
  elements.itemTags.value = (note.tags || []).join(", ");
  elements.itemMeta.value = JSON.stringify(data, null, 2);
  highlightSelection(kind, key);
};

const highlightSelection = (kind, key) => {
  document.querySelectorAll(".list-item").forEach((item) => {
    item.classList.toggle("active", kind === "plugin" && item.dataset.key === key);
  });
};

const updateSelectedNotes = () => {
  if (!state.selected) {
    return;
  }
  const tags = elements.itemTags.value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);

  const target = state.selected.kind === "plugin" ? state.notes.plugins : state.notes.samples;
  target[state.selected.key] = {
    description: elements.itemDescription.value.trim(),
    tags,
  };
  saveNotesToStorage();
};

const exportNotes = () => {
  const blob = new Blob([JSON.stringify(state.notes, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "notes.json";
  link.click();
  URL.revokeObjectURL(url);
};

const importNotes = (file) => {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const parsed = JSON.parse(reader.result);
      state.notes = mergeNotes(parsed, loadNotesFromStorage());
      saveNotesToStorage();
      if (state.selected) {
        selectItem(state.selected.kind, {
          name: state.selected.key,
          path: state.selected.key,
        });
      }
    } catch (error) {
      alert("Unable to read notes JSON.");
      console.error(error);
    }
  };
  reader.readAsText(file);
};

const resetNotes = () => {
  state.notes = { plugins: {}, samples: {} };
  saveNotesToStorage();
  if (state.selected) {
    selectItem(state.selected.kind, {
      name: state.selected.key,
      path: state.selected.key,
    });
  }
};

elements.pluginSearch.addEventListener("input", renderPlugins);
elements.sampleSearch.addEventListener("input", renderSampleTree);

elements.detailsForm.addEventListener("submit", (event) => {
  event.preventDefault();
  updateSelectedNotes();
});

elements.exportNotes.addEventListener("click", exportNotes);
elements.importNotes.addEventListener("change", (event) => {
  if (event.target.files.length) {
    importNotes(event.target.files[0]);
  }
});
elements.resetNotes.addEventListener("click", resetNotes);

const init = async () => {
  await loadData();
  renderPlugins();
  renderSampleTree();
};

init().catch((error) => {
  console.error(error);
  alert("Failed to load catalog data. Run a local web server to view the UI.");
});
