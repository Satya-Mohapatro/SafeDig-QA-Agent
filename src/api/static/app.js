// ============================================================
// SafeDig QA Console — Application Logic
// ============================================================

let currentJobId = null;
let currentDocumentId = null;
let currentWorkspacePayload = null;
let allLoadedJobs = [];

// Current maps view state
let allMapsForJob = [];           // full raw results for current job
let mapsFilterDecision = 'ALL';   // current decision filter
let workspacePreviousTab = 'maps'; // where to go back to from workspace

// ─── Interactive Map Zoom & Pan State ───────────────────────────────────────

let mapZoom = 1.0;
let mapPanX = 0;
let mapPanY = 0;
let isMapDragging = false;
let dragStartX = 0;
let dragStartY = 0;
let currentFullMapUrl = '';
let currentCropUrl = '';
let currentImageViewMode = 'map';

function updateMapTransform() {
  const stage = document.getElementById('ws-image-stage');
  const badge = document.getElementById('zoom-level-badge');
  if (stage) {
    stage.style.transform = `translate(${mapPanX}px, ${mapPanY}px) scale(${mapZoom})`;
  }
  if (badge) {
    badge.innerText = `${Math.round(mapZoom * 100)}%`;
  }
}

function zoomMap(delta) {
  const newZoom = Math.max(0.5, Math.min(6.0, mapZoom + delta));
  mapZoom = Math.round(newZoom * 100) / 100;
  updateMapTransform();
}

function resetMapZoom() {
  mapZoom = 1.0;
  mapPanX = 0;
  mapPanY = 0;
  updateMapTransform();
}

function handleMapWheel(e) {
  e.preventDefault();
  const delta = e.deltaY < 0 ? 0.2 : -0.2;
  zoomMap(delta);
}

function startMapPan(e) {
  if (e.button !== 0) return;
  isMapDragging = true;
  dragStartX = e.clientX - mapPanX;
  dragStartY = e.clientY - mapPanY;
  const vp = document.getElementById('ws-viewport-container');
  if (vp) vp.classList.add('cursor-grabbing');
}

function doMapPan(e) {
  if (!isMapDragging) return;
  mapPanX = e.clientX - dragStartX;
  mapPanY = e.clientY - dragStartY;
  updateMapTransform();
}

function endMapPan() {
  isMapDragging = false;
  const vp = document.getElementById('ws-viewport-container');
  if (vp) vp.classList.remove('cursor-grabbing');
}

function focusAOI() {
  if (!currentWorkspacePayload || !currentWorkspacePayload.aoi_bbox) {
    showToast('No AOI coordinates available for this plan.', 'info');
    return;
  }
  if (currentImageViewMode !== 'map') {
    setMapImageView('map');
  }
  const bbox = currentWorkspacePayload.aoi_bbox;
  mapZoom = 2.5;
  const vp = document.getElementById('ws-viewport-container');
  if (vp) {
    const aoiCenterX = ((bbox[0] + bbox[2]) / 2.0);
    const aoiCenterY = ((bbox[1] + bbox[3]) / 2.0);
    const vpW = vp.clientWidth || 600;
    const vpH = vp.clientHeight || 500;
    mapPanX = -Math.round((aoiCenterX * 1.5) - (vpW / 3.0));
    mapPanY = -Math.round((aoiCenterY * 1.5) - (vpH / 3.0));
  } else {
    mapPanX = -50;
    mapPanY = -50;
  }
  updateMapTransform();
  showToast('Focused onto Enquiry Site Boundary (AOI)', 'info');
}

function setMapImageView(mode) {
  currentImageViewMode = mode;
  const btnMap = document.getElementById('btn-view-map');
  const btnCrop = document.getElementById('btn-view-crop');
  const imgEl = document.getElementById('ws-evidence-image');

  if (mode === 'map') {
    if (btnMap) btnMap.className = 'px-2 py-0.5 rounded text-blue-400 font-semibold bg-slate-800 transition';
    if (btnCrop) btnCrop.className = 'px-2 py-0.5 rounded text-slate-400 hover:text-slate-200 transition';
    if (imgEl && currentFullMapUrl) imgEl.src = currentFullMapUrl;
  } else {
    if (btnCrop) btnCrop.className = 'px-2 py-0.5 rounded text-blue-400 font-semibold bg-slate-800 transition';
    if (btnMap) btnMap.className = 'px-2 py-0.5 rounded text-slate-400 hover:text-slate-200 transition';
    if (imgEl && currentCropUrl) {
      imgEl.src = currentCropUrl;
    } else {
      showToast('No detailed hazard crop available; displaying full sheet plan.', 'info');
      if (imgEl && currentFullMapUrl) imgEl.src = currentFullMapUrl;
    }
  }
  resetMapZoom();
}

// ─── Expanded Fullscreen Modal Controls ─────────────────────────────────────

let modalZoom = 1.0;
let modalPanX = 0;
let modalPanY = 0;
let isModalDragging = false;
let modalStartX = 0;
let modalStartY = 0;

function toggleMapFullscreen() {
  const modal = document.getElementById('map-fullscreen-modal');
  const fsImg = document.getElementById('fs-evidence-image');
  const wsImg = document.getElementById('ws-evidence-image');
  const title = document.getElementById('fs-modal-title');
  if (!modal) return;

  if (modal.classList.contains('hidden')) {
    if (wsImg && wsImg.src) fsImg.src = wsImg.src;
    if (currentWorkspacePayload) {
      title.innerText = `${currentWorkspacePayload.filename || 'Map Plan'} — 300 DPI Inspection`;
    }
    modal.classList.remove('hidden');
    resetModalZoom();
  } else {
    modal.classList.add('hidden');
  }
  if (window.lucide) lucide.createIcons();
}

function updateModalTransform() {
  const stage = document.getElementById('fs-image-stage');
  const badge = document.getElementById('fs-zoom-level');
  if (stage) stage.style.transform = `translate(${modalPanX}px, ${modalPanY}px) scale(${modalZoom})`;
  if (badge) badge.innerText = `${Math.round(modalZoom * 100)}%`;
}

function zoomModalMap(delta) {
  modalZoom = Math.max(0.5, Math.min(8.0, modalZoom + delta));
  updateModalTransform();
}

function resetModalZoom() {
  modalZoom = 1.0;
  modalPanX = 0;
  modalPanY = 0;
  updateModalTransform();
}

function handleModalWheel(e) {
  e.preventDefault();
  const delta = e.deltaY < 0 ? 0.25 : -0.25;
  zoomModalMap(delta);
}

function startModalPan(e) {
  if (e.button !== 0) return;
  isModalDragging = true;
  modalStartX = e.clientX - modalPanX;
  modalStartY = e.clientY - modalPanY;
  const vp = document.getElementById('fs-viewport');
  if (vp) vp.classList.add('cursor-grabbing');
}

function doModalPan(e) {
  if (!isModalDragging) return;
  modalPanX = e.clientX - modalStartX;
  modalPanY = e.clientY - modalStartY;
  updateModalTransform();
}

function endModalPan() {
  isModalDragging = false;
  const vp = document.getElementById('fs-viewport');
  if (vp) vp.classList.remove('cursor-grabbing');
}

// ─── Tab Switching ──────────────────────────────────────────────────────────

function switchTab(tabId) {
  const tabs = ['dashboard', 'maps', 'queue', 'workspace', 'catalogue'];
  if (!tabId || !tabs.includes(tabId)) {
    tabId = 'dashboard';
  }

  tabs.forEach(t => {
    const btn = document.getElementById(`tab-${t}`);
    const view = document.getElementById(`view-${t}`);
    if (!btn || !view) return;
    if (t === tabId) {
      btn.classList.add('active', 'bg-blue-600', 'text-white', 'shadow-sm');
      btn.classList.remove('text-slate-400');
      view.classList.remove('hidden');
    } else {
      btn.classList.remove('active', 'bg-blue-600', 'text-white', 'shadow-sm');
      btn.classList.add('text-slate-400');
      view.classList.add('hidden');
    }
  });

  if (tabId === 'queue') {
    loadQueue();
  } else if (tabId === 'dashboard') {
    loadRecentJobs();
  } else if (tabId === 'maps') {
    if (!currentJobId && allLoadedJobs.length > 0) {
      currentJobId = allLoadedJobs[0].job_id;
    }
    if (currentJobId && allMapsForJob.length === 0) {
      fetchAndRenderMaps(currentJobId);
    }
  }
}



// ─── Preset & Folder Input ──────────────────────────────────────────────────

function applyPreset() {
  const sel = document.getElementById('preset-select');
  if (sel && sel.value) {
    document.getElementById('root-dir-input').value = sel.value;
    onFolderInputChange();
  }
}

function onFolderInputChange() {
  const rootDir = document.getElementById('root-dir-input').value.trim();
  if (!rootDir) return;

  const normPath = rootDir.replace(/\\/g, '/').toLowerCase().replace(/\/+$/, '');
  const folderBase = normPath.split('/').pop();

  const match = allLoadedJobs.find(j => {
    const jPath = (j.root_dir || '').replace(/\\/g, '/').toLowerCase().replace(/\/+$/, '');
    return jPath === normPath || j.job_id.toLowerCase().includes(folderBase);
  });

  const cardName = document.getElementById('target-folder-name');
  const cardStatus = document.getElementById('target-folder-status');
  const cardDesc = document.getElementById('target-folder-desc');
  const cardActions = document.getElementById('target-folder-actions');

  if (match) {
    cardName.innerText = `Folder: ${folderBase} (${match.job_id})`;
    cardStatus.innerText = match.decision;
    cardStatus.className = `px-2 py-0.5 text-[10px] font-bold rounded-full ${decisionBadgeClass(match.decision)}`;
    cardDesc.innerText = `Processed: ${match.records} maps | Auto-Clear: ${match.auto_clear} | Review: ${match.human_review} | Blocked: ${match.blocked}`;
    cardActions.innerHTML = `
      <button onclick="viewJobMaps('${match.job_id}')" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-sm transition-all flex items-center space-x-1.5">
        <i data-lucide="table" class="w-3.5 h-3.5"></i>
        <span>View All Maps (${match.records})</span>
      </button>
      <button onclick="inspectJobInQueue('${match.job_id}')" class="px-3 py-1.5 bg-amber-600/20 hover:bg-amber-600/40 text-amber-300 rounded-lg text-xs font-semibold border border-amber-500/30 transition-all flex items-center space-x-1.5">
        <i data-lucide="inbox" class="w-3.5 h-3.5"></i>
        <span>QA Queue (${match.human_review})</span>
      </button>
    `;
    renderJobsTable(allLoadedJobs, match.job_id);
  } else {
    cardName.innerText = `Folder: ${folderBase}`;
    cardStatus.innerText = 'Ready to Run';
    cardStatus.className = 'px-2 py-0.5 text-[10px] font-semibold rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30';
    cardDesc.innerText = "Click 'Run QA Pipeline' to execute deterministic verification on this folder.";
    cardActions.innerHTML = '';
    renderJobsTable(allLoadedJobs);
  }
  lucide.createIcons();
}

// ─── Modern Badge Helpers ───────────────────────────────────────────────────

function decisionBadgeClass(dec) {
  if (dec === 'AUTO_CLEAR') return 'badge-auto-clear';
  if (dec === 'HUMAN_REVIEW') return 'badge-human-review';
  return 'badge-blocked';
}

function utilityBadge(util) {
  const u = (util || '').toLowerCase();
  if (u.includes('gas')) return '<span class="badge-utility badge-gas">Gas</span>';
  if (u.includes('elec') || u.includes('power') || u.includes('ukpn') || u.includes('nged')) return '<span class="badge-utility badge-elec">Electricity</span>';
  if (u.includes('water') || u.includes('sewer') || u.includes('thames') || u.includes('anglian')) return '<span class="badge-utility badge-water">Water</span>';
  if (u.includes('telecom') || u.includes('bt') || u.includes('virgin') || u.includes('openreach')) return '<span class="badge-utility badge-telecom">Telecom</span>';
  return `<span class="badge-utility badge-default">${util || '--'}</span>`;
}

function decisionIcon(dec) {
  if (dec === 'AUTO_CLEAR') return 'check-circle';
  if (dec === 'HUMAN_REVIEW') return 'alert-triangle';
  return 'ban';
}

// ─── Toast Notifications ─────────────────────────────────────────────────────

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  while (container.children.length >= 3) {
    container.removeChild(container.firstChild);
  }
  const toast = document.createElement('div');
  const colors = { success: 'bg-emerald-600', error: 'bg-rose-600', info: 'bg-blue-600', warning: 'bg-amber-600' };
  toast.className = `p-3 rounded-xl shadow-lg text-xs font-medium text-white flex items-center space-x-2 ${colors[type] || colors.info}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}


// ─── Submit Job ──────────────────────────────────────────────────────────────

async function submitJob() {
  const rootDir = document.getElementById('root-dir-input').value.trim();
  const btn = document.getElementById('btn-submit-job');
  if (!rootDir) { showToast('Please specify an enquiry root directory.', 'error'); return; }

  btn.disabled = true;
  btn.innerHTML = `<svg class="animate-spin h-4 w-4 text-white inline mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>Processing...`;

  try {
    const resp = await fetch('/api/v1/jobs/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ root_dir: rootDir })
    });
    if (!resp.ok) { const e = await resp.json(); throw new Error(e.detail || 'Job execution failed'); }
    const data = await resp.json();
    currentJobId = data.job_id;
    showToast(`Pipeline complete: ${data.total_documents_processed} maps processed for ${data.job_id}.`, 'success');
    await loadRecentJobs();
    onFolderInputChange();
    // Auto-jump to Map Results for the processed job
    await viewJobMaps(data.job_id);
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="play" class="w-4 h-4 inline mr-1"></i> Run QA Pipeline`;
    lucide.createIcons();
  }
}

// ─── Load Recent Jobs ────────────────────────────────────────────────────────

async function loadRecentJobs() {
  try {
    const resp = await fetch('/api/v1/jobs');
    if (!resp.ok) throw new Error('Failed to load jobs overview');
    const data = await resp.json();
    allLoadedJobs = data.jobs || [];

    document.getElementById('stat-total').innerText = data.total_processed || 0;
    document.getElementById('stat-autoclear').innerText = `${data.auto_clear_rate || 0}%`;
    document.getElementById('stat-autoclear-count').innerText = data.auto_clear_count || 0;
    document.getElementById('stat-review').innerText = `${data.human_review_rate || 0}%`;
    document.getElementById('stat-review-count').innerText = data.human_review_count || 0;
    document.getElementById('stat-blocked').innerText = `${data.blocked_rate || 0}%`;
    document.getElementById('stat-blocked-count').innerText = data.blocked_count || 0;

    if (data.available_presets && data.available_presets.length > 0) {
      const sel = document.getElementById('preset-select');
      if (sel) {
        const currentVal = sel.value;
        sel.innerHTML = data.available_presets.map(p => `<option value="${p.path}">${p.label}</option>`).join('');
        if (currentVal && data.available_presets.some(p => p.path === currentVal)) {
          sel.value = currentVal;
        } else {
          document.getElementById('root-dir-input').value = data.available_presets[0].path;
        }
      }
    }

    renderJobsTable(allLoadedJobs);
    onFolderInputChange();
  } catch (err) {
    console.error('Failed to load recent jobs:', err);
  }
}

function filterJobsTable() {
  const query = (document.getElementById('job-search-input')?.value || '').toLowerCase().trim();
  if (!query) { renderJobsTable(allLoadedJobs); return; }
  const filtered = allLoadedJobs.filter(j =>
    j.job_id.toLowerCase().includes(query) ||
    (j.root_dir || '').toLowerCase().includes(query) ||
    (j.decision || '').toLowerCase().includes(query)
  );
  renderJobsTable(filtered);
}

function renderJobsTable(jobs, highlightJobId = null) {
  const tbody = document.getElementById('jobs-table-body');
  if (!tbody) return;
  if (!jobs || jobs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-500 text-xs">No jobs found. Run a QA Pipeline to get started.</td></tr>`;
    return;
  }

  tbody.innerHTML = jobs.map(j => {
    const isHighlight = highlightJobId && j.job_id === highlightJobId;
    const ts = j.generated_at ? new Date(j.generated_at).toLocaleString() : '--';
    return `
      <tr class="transition-colors ${isHighlight ? 'bg-blue-950/40 border-l-4 border-blue-500' : 'hover:bg-slate-800/50'}">
        <td class="py-3 px-4">
          <div class="flex items-center gap-2">
            <span class="font-mono font-bold text-slate-200">${j.job_id}</span>
            ${isHighlight ? '<span class="px-1.5 py-0.2 text-[9px] bg-blue-500 text-white font-bold rounded">SELECTED</span>' : ''}
          </div>
          <div class="text-[10px] text-slate-500 truncate max-w-xs">${j.root_dir || ''}</div>
          <div class="text-[10px] text-slate-600">${ts}</div>
        </td>
        <td class="py-3 px-4 text-center font-bold text-slate-200">${j.records}</td>
        <td class="py-3 px-4 text-center font-bold text-emerald-400">${j.auto_clear}</td>
        <td class="py-3 px-4 text-center font-bold text-amber-400">${j.human_review}</td>
        <td class="py-3 px-4 text-center font-bold text-rose-400">${j.blocked}</td>
        <td class="py-3 px-4">
          <span class="px-2 py-0.5 text-[10px] font-bold rounded-full ${decisionBadgeClass(j.decision)}">${j.decision}</span>
        </td>
        <td class="py-3 px-4 text-right">
          <div class="flex items-center justify-end gap-1.5">
            <button onclick="viewJobMaps('${j.job_id}')" class="px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/50 text-blue-300 rounded-lg text-[10px] font-bold border border-blue-500/30 transition-all flex items-center gap-1">
              <i data-lucide="table" class="w-3 h-3"></i> View All Maps
            </button>
            <button onclick="inspectJobInQueue('${j.job_id}')" class="px-2.5 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 rounded-lg text-[10px] font-bold border border-amber-500/30 transition-all flex items-center gap-1">
              <i data-lucide="inbox" class="w-3 h-3"></i> Queue
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  lucide.createIcons();
}

// ─── Map Results (Individual Map Level) ─────────────────────────────────────

let isFetchingMaps = false;

async function fetchAndRenderMaps(jobId) {
  if (isFetchingMaps || !jobId) return;
  isFetchingMaps = true;
  currentJobId = jobId;
  mapsFilterDecision = 'ALL';

  const jobBadge = document.getElementById('maps-job-badge');
  if (jobBadge) jobBadge.innerText = jobId;
  const tbody = document.getElementById('maps-table-body');
  if (tbody) {
    tbody.innerHTML = `<tr><td colspan="12" class="py-10 text-center text-slate-500 text-xs"><svg class="animate-spin h-5 w-5 mx-auto mb-2 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>Loading ${jobId} map results...</td></tr>`;
  }

  try {
    const resp = await fetch(`/api/v1/jobs/${jobId}/results`);
    if (!resp.ok) throw new Error(`Failed to fetch map results (HTTP ${resp.status})`);
    const maps = await resp.json();

    allMapsForJob = Array.isArray(maps) ? maps : (maps.results || maps.documents || []);

    const ac = allMapsForJob.filter(m => m.decision === 'AUTO_CLEAR').length;
    const hr = allMapsForJob.filter(m => m.decision === 'HUMAN_REVIEW').length;
    const bl = allMapsForJob.filter(m => m.decision === 'BLOCKED').length;
    const total = allMapsForJob.length;

    const statTot = document.getElementById('maps-stat-total');
    if (statTot) statTot.innerText = total;
    const statAc = document.getElementById('maps-stat-ac');
    if (statAc) statAc.innerText = ac;
    const statHr = document.getElementById('maps-stat-hr');
    if (statHr) statHr.innerText = hr;
    const statBl = document.getElementById('maps-stat-bl');
    if (statBl) statBl.innerText = bl;

    const aggDec = bl > 0 ? 'BLOCKED' : hr > 0 ? 'HUMAN_REVIEW' : 'AUTO_CLEAR';
    const decBadge = document.getElementById('maps-decision-badge');
    if (decBadge) {
      decBadge.innerText = `${aggDec} (${total} maps)`;
      decBadge.className = `px-2 py-0.5 text-[10px] font-bold rounded-full ${decisionBadgeClass(aggDec)}`;
    }

    const navBadge = document.getElementById('maps-badge');
    if (navBadge) {
      navBadge.innerText = total;
      navBadge.classList.remove('hidden');
    }

    applyMapFilters();
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="13" class="py-8 text-center text-rose-400 text-xs">Error loading map results: ${err.message}</td></tr>`;
    }
    showToast(`Failed to load maps: ${err.message}`, 'error');
  } finally {
    isFetchingMaps = false;
  }
}

async function viewJobMaps(jobId) {
  workspacePreviousTab = 'maps';
  switchTab('maps');
  await fetchAndRenderMaps(jobId);
}


// Decision filter button click
function filterMaps(decision) {
  mapsFilterDecision = decision;
  ['ALL', 'AUTO_CLEAR', 'HUMAN_REVIEW', 'BLOCKED'].forEach(d => {
    const btnId = d === 'ALL' ? 'filter-btn-all' : `filter-btn-${d}`;
    const btn = document.getElementById(btnId);
    if (!btn) return;
    if (d === decision) {
      btn.className = 'map-filter-btn px-2.5 sm:px-3 py-1 rounded-lg text-[10px] sm:text-xs font-bold bg-blue-600 text-white border border-blue-500 shadow-sm';
    } else {
      let textColor = 'text-slate-400 hover:text-slate-200';
      if (d === 'AUTO_CLEAR') textColor = 'text-emerald-400 hover:bg-emerald-500/10';
      else if (d === 'HUMAN_REVIEW') textColor = 'text-amber-400 hover:bg-amber-500/10';
      else if (d === 'BLOCKED') textColor = 'text-rose-400 hover:bg-rose-500/10';
      btn.className = `map-filter-btn px-2.5 sm:px-3 py-1 rounded-lg text-[10px] sm:text-xs font-bold bg-slate-700 ${textColor} border border-slate-600 transition`;
    }
  });
  applyMapFilters();
}

// Apply all filters + sort and re-render
function applyMapFilters() {
  const query = (document.getElementById('maps-search-input')?.value || '').toLowerCase().trim();
  const sortVal = document.getElementById('maps-sort-select')?.value || 'decision-desc';

  let filtered = [...allMapsForJob];

  // Decision filter
  if (mapsFilterDecision !== 'ALL') {
    filtered = filtered.filter(m => m.decision === mapsFilterDecision);
  }

  // Text search across key fields
  if (query) {
    filtered = filtered.filter(m => {
      const fields = [
        m.filename, m.document_id, m.index_record_id,
        m.utility_name, m.utility_type, m.decision,
        m.reconciliation_outcome, m.reason, m.reason_detail
      ].map(f => (f || '').toLowerCase());
      return fields.some(f => f.includes(query));
    });
  }

  // Sort
  const decOrder = { BLOCKED: 0, HUMAN_REVIEW: 1, AUTO_CLEAR: 2 };
  filtered.sort((a, b) => {
    switch (sortVal) {
      case 'decision-desc': return (decOrder[a.decision] ?? 3) - (decOrder[b.decision] ?? 3);
      case 'decision-asc':  return (decOrder[b.decision] ?? 3) - (decOrder[a.decision] ?? 3);
      case 'provider-asc':  return (a.utility_name || '').localeCompare(b.utility_name || '');
      case 'filename-asc':  return (a.filename || '').localeCompare(b.filename || '');
      case 'warnings-desc': return (b.warning_count || 0) - (a.warning_count || 0);
      default: return 0;
    }
  });

  document.getElementById('maps-count-label').innerText = `${filtered.length} of ${allMapsForJob.length} maps`;
  renderMapsTable(filtered);
}

function renderMapsTable(maps) {
  const tbody = document.getElementById('maps-table-body');
  if (!tbody) return;

  if (!maps || maps.length === 0) {
    tbody.innerHTML = `<tr><td colspan="12" class="py-12 text-center text-slate-500 text-xs sm:text-sm font-medium">No maps match the current filter criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = maps.map(m => {
    const dec = m.decision || 'UNKNOWN';
    const outcome = m.reconciliation_outcome || '--';
    const reason = (m.reason || m.reason_detail || m.policy_reason || '--');
    const reasonShort = reason.length > 70 ? reason.slice(0, 70) + '...' : reason;

    // Upstream formatting
    const upstreamClaim = (m.upstream_warnings_count && m.upstream_warnings_count > 0) || (m.upstream_claim && !m.upstream_claim.toLowerCase().includes('clean'))
      ? `<span class="inline-flex items-center gap-1 font-semibold text-amber-400"><i data-lucide="alert-triangle" class="w-3.5 h-3.5 text-amber-400"></i> ${m.upstream_warnings_count || 1} Warning(s)</span>`
      : `<span class="inline-flex items-center gap-1 text-slate-400"><i data-lucide="check" class="w-3.5 h-3.5 text-emerald-400"></i> Clean</span>`;

    // Independent QA formatting
    const indepResult = (m.independent_findings_count && m.independent_findings_count > 0)
      ? `<span class="inline-flex items-center gap-1 font-semibold text-blue-400"><i data-lucide="crosshair" class="w-3.5 h-3.5 text-blue-400"></i> ${m.independent_findings_count} Hazard(s)</span>`
      : `<span class="inline-flex items-center gap-1 text-slate-400"><i data-lucide="check" class="w-3.5 h-3.5 text-emerald-400"></i> No hazards</span>`;

    const warnCount = m.warning_count || m.upstream_warnings_count || 0;
    const evidCount = m.evidence_count || 0;
    const reviewStatus = m.human_disposition_action
      ? `<span class="px-2 py-0.5 text-[10px] sm:text-xs font-bold rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">${m.human_disposition_action}</span>`
      : `<span class="text-slate-500 text-[10px] sm:text-xs">Pending</span>`;

    const docId = m.document_id || m.index_record_id || '';
    const indexRef = m.index_record_id || m.row_id || '--';

    return `
      <tr class="hover:bg-slate-800/60 transition-colors border-b border-slate-700/30 ${dec === 'BLOCKED' ? 'border-l-4 border-rose-500' : dec === 'HUMAN_REVIEW' ? 'border-l-4 border-amber-500' : ''}">
        <td class="py-2.5 sm:py-3 px-3 sm:px-4">
          <div class="font-mono text-xs sm:text-sm font-bold text-slate-100 truncate max-w-[220px] 2xl:max-w-[340px]" title="${m.filename || ''}">${m.filename || '--'}</div>
          <div class="text-[10px] sm:text-xs text-slate-400 font-mono mt-0.5 truncate max-w-[220px] 2xl:max-w-[340px]" title="${indexRef} • ${docId}">${indexRef}${docId && docId !== indexRef ? ` • ${docId}` : ''}</div>
        </td>
        <td class="py-2.5 sm:py-3 px-3">
          <div class="font-semibold text-slate-200 text-xs sm:text-sm whitespace-nowrap">${m.utility_name || '--'}</div>
        </td>
        <td class="py-2.5 sm:py-3 px-2.5 whitespace-nowrap">
          ${utilityBadge(m.utility_type || m.utility_name)}
        </td>
        <td class="py-2.5 sm:py-3 px-2 text-center whitespace-nowrap">
          <span class="px-2 py-0.5 text-[10px] sm:text-xs font-bold rounded-full ${
            m.status === 'Affects' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
            m.status === 'No' ? 'bg-slate-800 text-slate-400 border border-slate-700' :
            'bg-blue-500/10 text-blue-300 border border-blue-500/20'
          }">${m.status || '--'}</span>
        </td>
        <td class="py-2.5 sm:py-3 px-3 whitespace-nowrap">
          <span class="badge-decision ${decisionBadgeClass(dec)}">
            <i data-lucide="${decisionIcon(dec)}" class="w-3.5 h-3.5"></i>
            <span>${dec}</span>
          </span>
        </td>
        <td class="py-2.5 sm:py-3 px-3 text-xs sm:text-sm whitespace-nowrap">${upstreamClaim}</td>
        <td class="py-2.5 sm:py-3 px-3 text-xs sm:text-sm whitespace-nowrap">${indepResult}</td>
        <td class="py-2.5 sm:py-3 px-2 text-center font-bold ${warnCount > 0 ? 'text-amber-400' : 'text-slate-400'}">${warnCount}</td>
        <td class="py-2.5 sm:py-3 px-2 text-center font-bold ${evidCount > 0 ? 'text-blue-400' : 'text-slate-500'}">${evidCount}</td>
        <td class="py-2.5 sm:py-3 px-3">
          <div class="text-[11px] sm:text-xs text-slate-400 max-w-[180px] 2xl:max-w-[320px] truncate" title="${reason}">${reasonShort}</div>
          ${outcome !== '--' ? `<div class="text-[10px] text-slate-500 font-mono mt-0.5">${outcome}</div>` : ''}
        </td>
        <td class="py-2.5 sm:py-3 px-2.5 whitespace-nowrap">${reviewStatus}</td>
        <td class="py-2.5 sm:py-3 px-3 text-right whitespace-nowrap">
          <button onclick="openWorkspace('${currentJobId}', '${docId}')"
            class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-all inline-flex items-center gap-1 shadow-sm whitespace-nowrap">
            <span>Inspect</span>
            <i data-lucide="chevron-right" class="w-3.5 h-3.5"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
}

// ─── Inspect Job in Queue ────────────────────────────────────────────────────

function inspectJobInQueue(jobId) {
  currentJobId = jobId;
  workspacePreviousTab = 'queue';
  switchTab('queue');
}

// ─── QA Queue ────────────────────────────────────────────────────────────────

async function loadQueue() {
  const tbody = document.getElementById('queue-table-body');
  const badge = document.getElementById('queue-badge');

  try {
    const url = currentJobId ? `/api/v1/qa/queue?job_id=${currentJobId}` : '/api/v1/qa/queue';
    const resp = await fetch(url);
    if (!resp.ok) throw new Error('Failed to fetch queue');
    const data = await resp.json();
    badge.innerText = data.total_items;

    if (data.total_items === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-500 text-xs">No items awaiting human review${currentJobId ? ` for ${currentJobId}` : ''}.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.items.map(it => `
      <tr class="hover:bg-slate-800/50 transition-colors">
        <td class="py-3 px-4 font-mono font-medium text-slate-200">
          <div>${it.document_id}</div>
          <div class="text-[10px] text-slate-400">${it.filename}</div>
          <div class="text-[9px] text-slate-500">${it.job_id}</div>
        </td>
        <td class="py-3 px-4">
          <span class="font-medium text-slate-200">${it.utility_name}</span>
          <span class="text-[10px] text-slate-400 block">${it.utility_type}</span>
        </td>
        <td class="py-3 px-4 text-slate-300 italic text-[11px] max-w-xs truncate">${it.upstream_claim || 'None (Clean)'}</td>
        <td class="py-3 px-4 font-bold text-amber-400">${it.independent_findings_count} Finding(s)</td>
        <td class="py-3 px-4">
          <span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">${it.reconciliation_outcome}</span>
        </td>
        <td class="py-3 px-4 text-slate-300 text-[11px] max-w-sm truncate">${it.reason}</td>
        <td class="py-3 px-4 text-right">
          <button onclick="openWorkspaceFromQueue('${it.job_id}', '${it.document_id || it.index_record_id}')"
            class="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-sm transition-all flex items-center space-x-1 float-right">
            <span>Inspect</span><i data-lucide="chevron-right" class="w-3 h-3"></i>
          </button>
        </td>
      </tr>
    `).join('');

    lucide.createIcons();
  } catch (err) {
    console.error('Queue load error:', err);
    if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-rose-400 text-xs">Failed to load queue: ${err.message}</td></tr>`;
  }
}

function openWorkspaceFromQueue(jobId, docId) {
  workspacePreviousTab = 'queue';
  openWorkspace(jobId, docId);
}

function goBackFromWorkspace() {
  switchTab(workspacePreviousTab || 'maps');
}

// ─── Open QA Workspace ───────────────────────────────────────────────────────

async function openWorkspace(jobId, docId) {
  currentJobId = jobId;
  currentDocumentId = docId;
  switchTab('workspace');

  try {
    const resp = await fetch(`/api/v1/qa/workspace/${jobId}/${docId}`);
    if (!resp.ok) throw new Error(`Workspace load failed (HTTP ${resp.status})`);
    const data = await resp.json();
    currentWorkspacePayload = data;

    document.getElementById('ws-filename').innerText = data.filename || 'Unknown Document';
    document.getElementById('ws-provider').innerText = data.utility_name || '--';
    document.getElementById('ws-utility').innerText = data.utility_type || '--';
    document.getElementById('ws-job-id').innerText = data.job_id || jobId;

    const outcomeBadge = document.getElementById('ws-badge-outcome');
    outcomeBadge.innerText = data.reconciliation_outcome;
    outcomeBadge.className = `px-2 py-0.5 text-[10px] font-semibold rounded-full ${
      data.reconciliation_outcome === 'MATCH' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
      data.reconciliation_outcome === 'MISSED_WARNING' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
      'bg-amber-500/20 text-amber-300 border border-amber-500/30'}`;

    const decisionBadge = document.getElementById('ws-badge-decision');
    decisionBadge.innerText = data.decision;
    decisionBadge.className = `px-2 py-0.5 text-[10px] font-semibold rounded-full ${decisionBadgeClass(data.decision)}`;

    document.getElementById('ws-aoi-method').innerText = data.aoi_method || 'FALLBACK';
    document.getElementById('ws-aoi-conf').innerText = `${((data.aoi_confidence || 0.8) * 100).toFixed(0)}%`;
    document.getElementById('ws-modality').innerText = data.modality || 'VECTOR';
    document.getElementById('ws-pages').innerText = data.page_count || 1;
    document.getElementById('ws-aoi-bbox').innerText = `BBox: ${JSON.stringify(data.aoi_bbox || 'N/A')}`;

    document.getElementById('ws-upstream-claim').innerText = data.upstream_claim || 'None (Clean)';

    const indepContainer = document.getElementById('ws-indep-findings');
    if (!data.independent_findings || data.independent_findings.length === 0) {
      indepContainer.innerHTML = '<span class="text-slate-400 italic">No hazard assets detected inside AOI.</span>';
    } else {
      indepContainer.innerHTML = data.independent_findings.map(f => `
        <div class="flex items-center justify-between bg-slate-950/80 px-2 py-1 rounded-lg border border-slate-800">
          <span class="font-medium text-slate-200">${f.business_warning_text}</span>
          <span class="px-1.5 py-0.2 text-[10px] bg-rose-500/20 text-rose-300 rounded font-semibold">${f.severity}</span>
        </div>
      `).join('');
    }

    // Evidence image & Map Viewport setup
    const imgEl = document.getElementById('ws-evidence-image');
    const placeholder = document.getElementById('ws-image-placeholder');
    let primaryCropUrl = null;
    if (data.evidence_items && data.evidence_items.length > 0) {
      const itemWithCrop = data.evidence_items.find(it => it.crop_url);
      if (itemWithCrop) primaryCropUrl = itemWithCrop.crop_url;
    }
    const fallbackMapUrl = `/api/v1/evidence/${jobId}/${data.document_id || docId}/map-image`;
    
    currentCropUrl = primaryCropUrl || '';
    currentFullMapUrl = fallbackMapUrl;

    imgEl.onload = () => { imgEl.classList.remove('hidden'); placeholder.classList.add('hidden'); updateMapTransform(); };
    imgEl.onerror = () => {
      if (!imgEl.src.endsWith('/map-image')) { 
        imgEl.src = fallbackMapUrl; 
      } else { 
        imgEl.classList.add('hidden'); 
        placeholder.classList.remove('hidden'); 
      }
    };
    
    // Default to Full Map Plan with AOI Site Boundary tag
    setMapImageView('map');
    resetMapZoom();

    // Advisory Copilot
    if (data.advisory) {
      document.getElementById('ws-adv-summary').innerText = data.advisory.summary;
      document.getElementById('ws-adv-model').innerText = data.advisory.is_fallback ? 'Rule Assistant' : (data.advisory.model_name || 'Copilot');
      const contDiv = document.getElementById('ws-adv-contradictions');
      if (data.advisory.contradictions_detected && data.advisory.contradictions_detected.length > 0) {
        contDiv.innerHTML = data.advisory.contradictions_detected.map(c => `<div>⚠️ ${c}</div>`).join('');
        contDiv.classList.remove('hidden');
      } else { contDiv.classList.add('hidden'); }
    }

    // 17 Policy Gates
    const gatesContainer = document.getElementById('ws-gates-container');
    if (data.gates) {
      gatesContainer.innerHTML = Object.entries(data.gates).map(([gKey, gVal]) => `
        <div class="flex items-center justify-between text-[11px] py-1 border-b border-slate-700/30">
          <span class="text-slate-300">${gVal.gate_name || gKey}</span>
          <span class="font-bold ${gVal.passed ? 'text-emerald-400' : 'text-rose-400'}">${gVal.passed ? 'PASS' : 'FAIL'}</span>
        </div>
      `).join('');
    }

    lucide.createIcons();
  } catch (err) {
    showToast(`Failed to load workspace: ${err.message}`, 'error');
  }
}

function toggleGatesMatrix() {
  document.getElementById('ws-gates-container')?.classList.toggle('hidden');
  document.getElementById('gates-chevron')?.classList.toggle('rotate-180');
}

// ─── Human Disposition ───────────────────────────────────────────────────────

async function applyDisposition(action) {
  if (!currentWorkspacePayload) { showToast('No active document loaded.', 'error'); return; }

  const comment = document.getElementById('disposition-comment').value.trim();
  const reviewerId = document.getElementById('reviewer-id-input').value.trim() || 'QA_LEAD';

  if (!comment && (action === 'REJECT_WARNING' || action === 'BLOCK')) {
    showToast('Please provide a justification comment.', 'warning');
    return;
  }

  try {
    const payload = {
      job_id: currentWorkspacePayload.job_id,
      document_id: currentWorkspacePayload.document_id,
      index_record_id: currentWorkspacePayload.index_record_id,
      action,
      reviewer_id: reviewerId,
      reviewer_comment: comment || 'Verified by reviewer in SafeDig QA Workspace.'
    };

    const resp = await fetch('/api/v1/qa/disposition', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!resp.ok) throw new Error('Failed to record disposition');

    const result = await resp.json();
    showToast(`Disposition saved: ${action} → ${result.new_decision}`, 'success');

    await openWorkspace(currentWorkspacePayload.job_id, currentWorkspacePayload.document_id);
    await loadQueue();
    await loadRecentJobs();
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

// ─── Startup ─────────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
  switchTab('dashboard');
  loadRecentJobs();
  loadQueue();
});

window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const modal = document.getElementById('map-fullscreen-modal');
    if (modal && !modal.classList.contains('hidden')) {
      toggleMapFullscreen();
    }
  }
});

