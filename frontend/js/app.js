/* ===== API Client ===== */
const API = {
  async request(method, url, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    if (res.status === 204) return null;
    return res.json();
  },
  get: (url) => API.request('GET', url),
  post: (url, body) => API.request('POST', url, body),
  put: (url, body) => API.request('PUT', url, body),
  delete: (url) => API.request('DELETE', url),
};

/* ===== Toast ===== */
function toast(msg, type = 'info') {
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

/* ===== Router ===== */
const routes = {};
function register(hash, fn) { routes[hash] = fn; }
function navigate(hash) { window.location.hash = hash; }

window.addEventListener('hashchange', render);
window.addEventListener('load', render);

function render() {
  const hash = window.location.hash || '#/';
  const main = document.getElementById('main-content');

  // Update active nav
  document.querySelectorAll('.header-nav a').forEach(a => {
    a.classList.toggle('active', hash.startsWith(a.getAttribute('href')));
  });

  // Match route
  const matched = Object.keys(routes).find(r => hash === r || hash.startsWith(r + '/'));
  if (matched) {
    routes[matched](hash);
  } else {
    main.innerHTML = '<div class="empty-state"><p>页面未找到</p></div>';
  }
}

/* ===== Chips Input Component ===== */
function ChipsInput(containerId, initial = []) {
  const wrap = document.getElementById(containerId);
  let chips = [...initial];

  function removeChip(idx) { chips.splice(idx, 1); render(); }

  function render() {
    wrap.innerHTML = '';
    chips.forEach((c, i) => {
      const chip = document.createElement('span');
      chip.className = 'chip';
      const label = document.createTextNode(c);
      const btn = document.createElement('button');
      btn.textContent = '×';
      btn.setAttribute('type', 'button');
      btn.addEventListener('click', () => removeChip(i));
      chip.appendChild(label);
      chip.appendChild(btn);
      wrap.appendChild(chip);
    });
    const inp = document.createElement('input');
    inp.placeholder = '输入后按回车添加';
    inp.addEventListener('keydown', e => {
      if (e.key === 'Enter' && inp.value.trim()) {
        e.preventDefault();
        chips.push(inp.value.trim());
        render();
      } else if (e.key === 'Backspace' && !inp.value && chips.length) {
        chips.pop();
        render();
      }
    });
    wrap.appendChild(inp);
  }

  render();
  return { getValues: () => chips };
}

/* ===== Modal Helpers ===== */
function openModal(html) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `<div class="modal">${html}</div>`;
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  return overlay;
}

function closeModal() {
  document.querySelector('.modal-overlay')?.remove();
}

/* ===== Task type labels ===== */
const TASK_LABELS = {
  text_classification: '文本分类',
  ner: '命名实体识别',
  text_generation: '文本生成',
  qa: '问答',
  instruction_tuning: '指令微调',
};

const TASK_COLORS = {
  text_classification: 'badge-primary',
  ner: 'badge-warning',
  text_generation: 'badge-success',
  qa: 'badge-danger',
  instruction_tuning: 'badge-gray',
};

const STATUS_LABELS = {
  pending: '待标注',
  annotated: '已标注',
  reviewed: '已审核',
  rejected: '已拒绝',
};

const STATUS_BADGE = {
  pending: 'badge-gray',
  annotated: 'badge-primary',
  reviewed: 'badge-success',
  rejected: 'badge-danger',
};

/* =====================================================================
   PAGE: Projects (#/ or #/projects)
   ===================================================================== */
register('#/', renderProjectsPage);
register('#/projects', renderProjectsPage);

async function renderProjectsPage() {
  const main = document.getElementById('main-content');
  main.innerHTML = `<div class="spinner" style="margin:60px auto;display:block"></div>`;

  const projects = await API.get('/api/projects').catch(() => []);

  // Store projects for safe access from event handlers
  window._projectsCache = {};
  projects.forEach(p => { window._projectsCache[p.id] = p; });

  main.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px">
      <div>
        <h1 style="font-size:1.5rem;font-weight:700">我的项目</h1>
        <p style="color:var(--gray-500);font-size:.9rem;margin-top:4px">管理数据集生成与标注项目</p>
      </div>
      <button class="btn btn-primary" onclick="showCreateProjectModal()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新建项目
      </button>
    </div>

    ${projects.length === 0 ? `
      <div class="empty-state">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 12h6M12 9v6"/></svg>
        <p>还没有项目，点击右上角创建第一个项目</p>
      </div>
    ` : `
      <div class="grid grid-2" id="projects-grid">
        ${projects.map(p => renderProjectCard(p)).join('')}
      </div>
    `}
  `;

  // Attach event listeners after DOM is rendered (safe, no inline JSON)
  projects.forEach(p => {
    const editBtn = document.getElementById(`edit-btn-${p.id}`);
    const delBtn = document.getElementById(`del-btn-${p.id}`);
    if (editBtn) editBtn.addEventListener('click', (e) => { e.stopPropagation(); showEditProjectModal(p.id); });
    if (delBtn) delBtn.addEventListener('click', (e) => { e.stopPropagation(); deleteProject(p.id); });
    const card = document.getElementById(`proj-card-${p.id}`);
    if (card) card.addEventListener('click', () => navigate(`#/project/${p.id}`));
  });
}

function renderProjectCard(p) {
  return `
    <div class="card project-card" id="proj-card-${p.id}" style="cursor:pointer">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:8px">
        <div>
          <div style="font-size:1rem;font-weight:600;margin-bottom:6px">${escHtml(p.name)}</div>
          <span class="badge ${TASK_COLORS[p.task_type]}">${TASK_LABELS[p.task_type]}</span>
        </div>
        <div style="display:flex;gap:4px">
          <button class="btn btn-sm btn-secondary" id="edit-btn-${p.id}">编辑</button>
          <button class="btn btn-sm btn-danger-outline" id="del-btn-${p.id}">删除</button>
        </div>
      </div>
      ${p.description ? `<p style="font-size:.85rem;color:var(--gray-500);margin-top:10px">${escHtml(p.description)}</p>` : ''}
      <div class="stats-row">
        <span>🏷 ${p.labels.length} 个标签</span>
        <span>📅 ${fmtDate(p.created_at)}</span>
      </div>
    </div>
  `;
}

window.showCreateProjectModal = function () {
  const overlay = openModal(`
    <div class="modal-title">新建项目</div>
    <div class="form-group">
      <label>项目名称 *</label>
      <input type="text" id="cp-name" placeholder="输入项目名称">
    </div>
    <div class="form-group">
      <label>项目描述</label>
      <textarea id="cp-desc" placeholder="可选描述"></textarea>
    </div>
    <div class="form-group">
      <label>任务类型 *</label>
      <select id="cp-type">
        ${Object.entries(TASK_LABELS).map(([v,l]) => `<option value="${v}">${l}</option>`).join('')}
      </select>
    </div>
    <div class="form-group">
      <label>标签（按回车添加）</label>
      <div class="chips-input" id="cp-labels-chips"></div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" onclick="doCreateProject()">创建</button>
    </div>
  `);
  window._labelsChips = ChipsInput('cp-labels-chips');
};

window.doCreateProject = async function () {
  const name = document.getElementById('cp-name').value.trim();
  if (!name) { toast('请输入项目名称', 'error'); return; }
  const data = {
    name,
    description: document.getElementById('cp-desc').value.trim(),
    task_type: document.getElementById('cp-type').value,
    labels: window._labelsChips.getValues(),
  };
  try {
    await API.post('/api/projects', data);
    closeModal();
    toast('项目创建成功', 'success');
    renderProjectsPage();
  } catch (e) { toast(e.message, 'error'); }
};

window.showEditProjectModal = async function (id) {
  const project = await API.get(`/api/projects/${id}`).catch(() => null);
  if (!project) return;
  openModal(`
    <div class="modal-title">编辑项目</div>
    <div class="form-group">
      <label>项目名称</label>
      <input type="text" id="ep-name" value="${escHtml(project.name)}">
    </div>
    <div class="form-group">
      <label>项目描述</label>
      <textarea id="ep-desc">${escHtml(project.description)}</textarea>
    </div>
    <div class="form-group">
      <label>标签（按回车添加）</label>
      <div class="chips-input" id="ep-labels-chips"></div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" onclick="doEditProject(${id})">保存</button>
    </div>
  `);
  window._editLabelsChips = ChipsInput('ep-labels-chips', project.labels);
};

window.doEditProject = async function (id) {
  const name = document.getElementById('ep-name').value.trim();
  if (!name) { toast('请输入项目名称', 'error'); return; }
  try {
    await API.put(`/api/projects/${id}`, {
      name,
      description: document.getElementById('ep-desc').value.trim(),
      labels: window._editLabelsChips.getValues(),
    });
    closeModal();
    toast('保存成功', 'success');
    renderProjectsPage();
  } catch (e) { toast(e.message, 'error'); }
};

window.deleteProject = async function (id) {
  if (!confirm('确定要删除这个项目及其所有数据吗？')) return;
  try {
    await API.delete(`/api/projects/${id}`);
    toast('项目已删除', 'success');
    renderProjectsPage();
  } catch (e) { toast(e.message, 'error'); }
};

/* =====================================================================
   PAGE: Project Detail (#/project/:id)
   ===================================================================== */
register('#/project', renderProjectPage);

async function renderProjectPage(hash) {
  const projectId = parseInt(hash.split('/')[2]);
  const main = document.getElementById('main-content');
  main.innerHTML = `<div class="spinner" style="margin:60px auto;display:block"></div>`;

  const [project, datasets, stats] = await Promise.all([
    API.get(`/api/projects/${projectId}`).catch(() => null),
    API.get(`/api/datasets/project/${projectId}`).catch(() => []),
    API.get(`/api/projects/${projectId}/stats`).catch(() => null),
  ]);

  if (!project) { main.innerHTML = '<div class="empty-state"><p>项目不存在</p></div>'; return; }

  main.innerHTML = `
    <div class="breadcrumb">
      <a href="#/projects">项目</a>
      <span>›</span>
      <span>${escHtml(project.name)}</span>
    </div>

    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
      <div>
        <h1 style="font-size:1.4rem;font-weight:700">${escHtml(project.name)}</h1>
        <div style="display:flex;gap:10px;align-items:center;margin-top:6px">
          <span class="badge ${TASK_COLORS[project.task_type]}">${TASK_LABELS[project.task_type]}</span>
          ${project.description ? `<span style="color:var(--gray-500);font-size:.85rem">${escHtml(project.description)}</span>` : ''}
        </div>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-secondary" onclick="showGenerateModal(${projectId},'${escHtml(project.task_type)}')">
          ⚡ 生成数据集
        </button>
        <button class="btn btn-primary" onclick="showCreateDatasetModal(${projectId})">
          + 新建数据集
        </button>
      </div>
    </div>

    ${stats ? `
    <div class="grid grid-4" style="margin-bottom:24px">
      <div class="stat-box">
        <div class="stat-num">${stats.total_items}</div>
        <div class="stat-label">总条目</div>
      </div>
      <div class="stat-box">
        <div class="stat-num" style="color:var(--gray-400)">${stats.pending}</div>
        <div class="stat-label">待标注</div>
      </div>
      <div class="stat-box">
        <div class="stat-num" style="color:var(--primary)">${stats.annotated}</div>
        <div class="stat-label">已标注</div>
      </div>
      <div class="stat-box">
        <div class="stat-num" style="color:var(--success)">${stats.reviewed}</div>
        <div class="stat-label">已审核</div>
      </div>
    </div>
    ${stats.total_items > 0 ? `
    <div class="card" style="margin-bottom:24px;padding:16px">
      <div style="display:flex;justify-content:space-between;font-size:.85rem;margin-bottom:6px">
        <span>标注进度</span><span>${stats.progress_pct}%</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" style="width:${stats.progress_pct}%"></div></div>
    </div>
    ` : ''}
    ` : ''}

    <div class="card">
      <div class="card-header">
        <span class="card-title">数据集列表</span>
        <span style="color:var(--gray-400);font-size:.85rem">${datasets.length} 个数据集</span>
      </div>
      ${datasets.length === 0 ? `
        <div class="empty-state" style="padding:40px">
          <p>还没有数据集，点击"生成数据集"或"新建数据集"</p>
        </div>
      ` : `
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>名称</th>
                <th>描述</th>
                <th>条目数</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              ${datasets.map(d => `
                <tr>
                  <td><a href="#/dataset/${d.id}" style="color:var(--primary);text-decoration:none;font-weight:500">${escHtml(d.name)}</a></td>
                  <td style="color:var(--gray-500)">${escHtml(d.description || '-')}</td>
                  <td><span class="badge badge-gray">${d.item_count}</span></td>
                  <td style="color:var(--gray-500)">${fmtDate(d.created_at)}</td>
                  <td>
                    <div style="display:flex;gap:6px">
                      <button class="btn btn-sm btn-primary" onclick="navigate('#/annotate/${d.id}')">标注</button>
                      <button class="btn btn-sm btn-secondary" onclick="exportDataset(${d.id},'${escHtml(d.name)}')">导出</button>
                      <button class="btn btn-sm btn-danger-outline" onclick="deleteDataset(${d.id},${projectId})">删除</button>
                    </div>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `}
    </div>

    ${project.labels.length > 0 ? `
    <div class="card" style="margin-top:20px">
      <div class="card-header"><span class="card-title">标签集</span></div>
      <div class="label-grid">
        ${project.labels.map(l => `<span class="badge badge-primary">${escHtml(l)}</span>`).join('')}
      </div>
    </div>
    ` : ''}
  `;
}

window.showCreateDatasetModal = function (projectId) {
  openModal(`
    <div class="modal-title">新建数据集</div>
    <div class="form-group">
      <label>数据集名称 *</label>
      <input type="text" id="ds-name" placeholder="例如：训练集-v1">
    </div>
    <div class="form-group">
      <label>描述</label>
      <textarea id="ds-desc" placeholder="可选描述"></textarea>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" onclick="doCreateDataset(${projectId})">创建</button>
    </div>
  `);
};

window.doCreateDataset = async function (projectId) {
  const name = document.getElementById('ds-name').value.trim();
  if (!name) { toast('请输入数据集名称', 'error'); return; }
  try {
    await API.post(`/api/datasets/project/${projectId}`, {
      name,
      description: document.getElementById('ds-desc').value.trim(),
    });
    closeModal();
    toast('数据集创建成功', 'success');
    renderProjectPage(`#/project/${projectId}`);
  } catch (e) { toast(e.message, 'error'); }
};

window.showGenerateModal = function (projectId, taskType) {
  openModal(`
    <div class="modal-title">⚡ 生成数据集</div>
    <div class="form-group">
      <label>数据集名称 *</label>
      <input type="text" id="gen-name">
    </div>
    <div class="form-group">
      <label>生成数量</label>
      <input type="number" id="gen-count" value="20" min="1" max="500">
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="gen-btn" onclick="doGenerate(${projectId})">开始生成</button>
    </div>
  `);
  // Set default name safely via DOM (avoid embedding dynamic content in HTML string)
  const genNameInput = document.getElementById('gen-name');
  if (genNameInput) genNameInput.value = `自动生成-${new Date().toLocaleDateString('zh-CN')}`;
};

window.doGenerate = async function (projectId) {
  const name = document.getElementById('gen-name').value.trim();
  const count = parseInt(document.getElementById('gen-count').value) || 10;
  if (!name) { toast('请输入数据集名称', 'error'); return; }
  const btn = document.getElementById('gen-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 生成中...';
  try {
    const res = await API.post('/api/generate', { project_id: projectId, dataset_name: name, count });
    closeModal();
    toast(`成功生成 ${res.generated} 条数据`, 'success');
    renderProjectPage(`#/project/${projectId}`);
  } catch (e) { toast(e.message, 'error'); btn.disabled = false; btn.textContent = '开始生成'; }
};

window.deleteDataset = async function (datasetId, projectId) {
  if (!confirm('确定要删除该数据集及所有标注数据吗？')) return;
  try {
    await API.delete(`/api/datasets/${datasetId}`);
    toast('数据集已删除', 'success');
    renderProjectPage(`#/project/${projectId}`);
  } catch (e) { toast(e.message, 'error'); }
};

window.exportDataset = async function (datasetId, name) {
  try {
    const res = await API.get(`/api/datasets/${datasetId}/export?fmt=json`);
    const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = res.filename || `${name}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast('导出成功', 'success');
  } catch (e) { toast(e.message, 'error'); }
};

/* =====================================================================
   PAGE: Dataset Detail / Item List (#/dataset/:id)
   ===================================================================== */
register('#/dataset', renderDatasetPage);

async function renderDatasetPage(hash) {
  const datasetId = parseInt(hash.split('/')[2]);
  const main = document.getElementById('main-content');
  main.innerHTML = `<div class="spinner" style="margin:60px auto;display:block"></div>`;

  const [ds, items] = await Promise.all([
    API.get(`/api/datasets/${datasetId}`).catch(() => null),
    API.get(`/api/datasets/${datasetId}/items?page=1&page_size=50`).catch(() => []),
  ]);

  if (!ds) { main.innerHTML = '<div class="empty-state"><p>数据集不存在</p></div>'; return; }

  main.innerHTML = `
    <div class="breadcrumb">
      <a href="#/projects">项目</a>
      <span>›</span>
      <a href="#/project/${ds.project_id}">项目详情</a>
      <span>›</span>
      <span>${escHtml(ds.name)}</span>
    </div>

    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
      <h1 style="font-size:1.3rem;font-weight:700">${escHtml(ds.name)}</h1>
      <div style="display:flex;gap:8px">
        <button class="btn btn-primary" onclick="navigate('#/annotate/${datasetId}')">开始标注</button>
        <button class="btn btn-secondary" onclick="exportDataset(${datasetId},'${escHtml(ds.name)}')">导出</button>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-title">数据条目 (${items.length})</span>
      </div>
      ${items.length === 0 ? `<div class="empty-state" style="padding:40px"><p>暂无数据</p></div>` : `
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>内容摘要</th>
                <th>状态</th>
                <th>标注人</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              ${items.map((item, i) => `
                <tr>
                  <td style="color:var(--gray-400)">${item.id}</td>
                  <td style="max-width:360px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                    ${escHtml(itemSummary(item.content))}
                  </td>
                  <td><span class="badge ${STATUS_BADGE[item.status]}">${STATUS_LABELS[item.status]}</span></td>
                  <td style="color:var(--gray-500)">${item.annotator || '-'}</td>
                  <td>
                    <button class="btn btn-sm btn-primary" onclick="navigate('#/annotate/${datasetId}/${item.id}')">标注</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `}
    </div>
  `;
}

/* =====================================================================
   PAGE: Annotation (#/annotate/:datasetId or #/annotate/:datasetId/:itemId)
   ===================================================================== */
register('#/annotate', renderAnnotatePage);

let _annotateState = {
  datasetId: null,
  items: [],
  currentIndex: 0,
  project: null,
};

async function renderAnnotatePage(hash) {
  const parts = hash.split('/');
  const datasetId = parseInt(parts[2]);
  const itemId = parts[3] ? parseInt(parts[3]) : null;
  const main = document.getElementById('main-content');
  main.innerHTML = `<div class="spinner" style="margin:60px auto;display:block"></div>`;

  const [ds, items] = await Promise.all([
    API.get(`/api/datasets/${datasetId}`).catch(() => null),
    API.get(`/api/datasets/${datasetId}/items?page_size=200`).catch(() => []),
  ]);

  if (!ds) { main.innerHTML = '<div class="empty-state"><p>数据集不存在</p></div>'; return; }

  const project = await API.get(`/api/projects/${ds.project_id}`).catch(() => null);
  if (!project) { main.innerHTML = '<div class="empty-state"><p>项目不存在</p></div>'; return; }

  _annotateState = {
    datasetId,
    items,
    currentIndex: itemId ? items.findIndex(i => i.id === itemId) : 0,
    project,
    dataset: ds,
  };
  if (_annotateState.currentIndex < 0) _annotateState.currentIndex = 0;

  renderAnnotateUI(main);
}

function renderAnnotateUI(main) {
  const { items, currentIndex, project, dataset, datasetId } = _annotateState;

  if (items.length === 0) {
    main.innerHTML = `
      <div class="breadcrumb">
        <a href="#/projects">项目</a><span>›</span>
        <a href="#/project/${project.id}">${escHtml(project.name)}</a><span>›</span>
        <a href="#/dataset/${datasetId}">${escHtml(dataset.name)}</a><span>›</span>
        <span>标注</span>
      </div>
      <div class="empty-state"><p>数据集为空，请先生成或导入数据</p></div>
    `;
    return;
  }

  const item = items[currentIndex];
  const pending = items.filter(i => i.status === 'pending').length;

  main.innerHTML = `
    <div class="breadcrumb">
      <a href="#/projects">项目</a><span>›</span>
      <a href="#/project/${project.id}">${escHtml(project.name)}</a><span>›</span>
      <a href="#/dataset/${datasetId}">${escHtml(dataset.name)}</a><span>›</span>
      <span>标注</span>
    </div>

    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
      <div>
        <h2 style="font-size:1.1rem;font-weight:600">${escHtml(dataset.name)} — 标注</h2>
        <p style="font-size:.85rem;color:var(--gray-500);margin-top:2px">
          ${currentIndex+1} / ${items.length} &nbsp;|&nbsp; 待标注: ${pending}
        </p>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-secondary btn-sm" onclick="annotateNav(-1)" ${currentIndex===0?'disabled':''}>◀ 上一条</button>
        <button class="btn btn-secondary btn-sm" onclick="annotateNav(1)" ${currentIndex===items.length-1?'disabled':''}>下一条 ▶</button>
      </div>
    </div>

    <div style="margin-bottom:12px">
      <div class="progress-bar">
        <div class="progress-fill" style="width:${Math.round((items.filter(i=>i.status!=='pending').length/items.length)*100)}%"></div>
      </div>
    </div>

    <div id="annotate-body"></div>
  `;

  renderAnnotateBody(item, project);
}

function renderAnnotateBody(item, project) {
  const body = document.getElementById('annotate-body');
  const taskType = project.task_type;

  if (taskType === 'text_classification') {
    renderClassificationAnnotation(body, item, project.labels);
  } else if (taskType === 'ner') {
    renderNERAnnotation(body, item, project.labels);
  } else if (taskType === 'qa') {
    renderQAAnnotation(body, item);
  } else if (taskType === 'instruction_tuning') {
    renderInstructionAnnotation(body, item);
  } else {
    renderTextGenerationAnnotation(body, item);
  }
}

/* ----- Text Classification ----- */
function renderClassificationAnnotation(body, item, labels) {
  const current = item.annotation?.label || null;
  body.innerHTML = `
    <div class="annotation-layout">
      <div>
        <div class="card" style="margin-bottom:16px">
          <div style="font-size:.8rem;color:var(--gray-500);margin-bottom:8px;font-weight:600">文本内容</div>
          <div class="annotation-content-card">${escHtml(item.content.text || JSON.stringify(item.content))}</div>
          ${item.content.hint ? `<div style="font-size:.8rem;color:var(--gray-400);margin-top:8px">提示：${escHtml(item.content.hint)}</div>` : ''}
        </div>
        <div class="card">
          <div style="font-size:.85rem;font-weight:600;margin-bottom:12px">选择标签</div>
          <div class="label-grid" id="label-grid">
            ${labels.map(l => `
              <button class="label-btn ${current===l?'selected':''}" onclick="selectLabel('${escHtml(l)}')">${escHtml(l)}</button>
            `).join('')}
          </div>
        </div>
      </div>
      <div>
        <div class="card" style="margin-bottom:16px">
          <div style="font-size:.85rem;font-weight:600;margin-bottom:12px">标注信息</div>
          <div class="form-group">
            <label>当前状态</label>
            <span class="badge ${STATUS_BADGE[item.status]}">${STATUS_LABELS[item.status]}</span>
          </div>
          <div class="form-group">
            <label>选中标签</label>
            <div id="selected-label" style="font-size:1rem;font-weight:600;color:var(--primary);min-height:24px">
              ${current || '未选择'}
            </div>
          </div>
          <div class="form-group">
            <label>标注人</label>
            <input type="text" id="annotator" placeholder="你的名字" value="${item.annotator || ''}">
          </div>
          <div class="form-group">
            <label>备注（可选）</label>
            <textarea id="annotation-note" placeholder="可选备注">${item.annotation?.note || ''}</textarea>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:8px">
          <button class="btn btn-primary" onclick="submitAnnotation('classification')">✓ 保存标注</button>
          ${item.status==='annotated'||item.status==='reviewed'?`
          <div style="display:flex;gap:8px">
            <button class="btn btn-success" style="flex:1" onclick="reviewItem(true)">✓ 通过</button>
            <button class="btn btn-danger" style="flex:1" onclick="reviewItem(false)">✗ 拒绝</button>
          </div>
          `:``}
        </div>
      </div>
    </div>
  `;
  window._selectedLabel = current;
}

window.selectLabel = function (label) {
  window._selectedLabel = label;
  document.getElementById('selected-label').textContent = label;
  document.querySelectorAll('.label-btn').forEach(btn => {
    btn.classList.toggle('selected', btn.textContent === label);
  });
};

/* ----- QA Annotation ----- */
function renderQAAnnotation(body, item) {
  const ans = item.annotation?.answer || '';
  body.innerHTML = `
    <div class="annotation-layout">
      <div>
        <div class="card" style="margin-bottom:16px">
          <div style="font-size:.8rem;color:var(--gray-500);margin-bottom:8px;font-weight:600">上下文</div>
          <div class="annotation-content-card">${escHtml(item.content.context || '')}</div>
        </div>
        <div class="card">
          <div style="font-size:.8rem;color:var(--gray-500);margin-bottom:8px;font-weight:600">问题</div>
          <div class="annotation-content-card" style="background:var(--warning-light)">${escHtml(item.content.question || '')}</div>
        </div>
      </div>
      <div>
        <div class="card" style="margin-bottom:16px">
          <div style="font-size:.85rem;font-weight:600;margin-bottom:12px">填写答案</div>
          <div class="form-group">
            <label>答案</label>
            <textarea id="qa-answer" rows="4" placeholder="请根据上下文填写答案">${ans}</textarea>
          </div>
          <div class="form-group">
            <label>标注人</label>
            <input type="text" id="annotator" placeholder="你的名字" value="${item.annotator || ''}">
          </div>
        </div>
        <button class="btn btn-primary" onclick="submitAnnotation('qa')">✓ 保存标注</button>
      </div>
    </div>
  `;
}

/* ----- Instruction Tuning ----- */
function renderInstructionAnnotation(body, item) {
  const output = item.annotation?.output || '';
  body.innerHTML = `
    <div class="annotation-layout">
      <div>
        <div class="card" style="margin-bottom:12px">
          <div style="font-size:.8rem;color:var(--gray-500);margin-bottom:6px;font-weight:600">指令 (Instruction)</div>
          <div class="annotation-content-card">${escHtml(item.content.instruction || '')}</div>
        </div>
        ${item.content.input ? `
        <div class="card">
          <div style="font-size:.8rem;color:var(--gray-500);margin-bottom:6px;font-weight:600">输入 (Input)</div>
          <div class="annotation-content-card">${escHtml(item.content.input)}</div>
        </div>
        ` : ''}
      </div>
      <div>
        <div class="card" style="margin-bottom:16px">
          <div style="font-size:.85rem;font-weight:600;margin-bottom:12px">填写输出</div>
          <div class="form-group">
            <label>Output（预期输出）</label>
            <textarea id="inst-output" rows="6" placeholder="请填写期望的模型输出">${output}</textarea>
          </div>
          <div class="form-group">
            <label>标注人</label>
            <input type="text" id="annotator" placeholder="你的名字" value="${item.annotator || ''}">
          </div>
        </div>
        <button class="btn btn-primary" onclick="submitAnnotation('instruction')">✓ 保存标注</button>
      </div>
    </div>
  `;
}

/* ----- Text Generation ----- */
function renderTextGenerationAnnotation(body, item) {
  const output = item.annotation?.output || '';
  body.innerHTML = `
    <div class="annotation-layout">
      <div>
        <div class="card">
          <div style="font-size:.8rem;color:var(--gray-500);margin-bottom:8px;font-weight:600">提示词 (Prompt)</div>
          <div class="annotation-content-card">${escHtml(item.content.prompt || JSON.stringify(item.content))}</div>
        </div>
      </div>
      <div>
        <div class="card" style="margin-bottom:16px">
          <div style="font-size:.85rem;font-weight:600;margin-bottom:12px">填写生成内容</div>
          <div class="form-group">
            <label>生成文本</label>
            <textarea id="gen-output" rows="8" placeholder="请填写期望的生成文本">${output}</textarea>
          </div>
          <div class="form-group">
            <label>标注人</label>
            <input type="text" id="annotator" placeholder="你的名字" value="${item.annotator || ''}">
          </div>
        </div>
        <button class="btn btn-primary" onclick="submitAnnotation('generation')">✓ 保存标注</button>
      </div>
    </div>
  `;
}

/* ----- NER Annotation ----- */
function renderNERAnnotation(body, item, labels) {
  const existing = item.annotation?.entities || [];
  window._nerEntities = [...existing];
  window._nerLabels = labels.length ? labels : ['人名', '地名', '机构名', '时间'];

  body.innerHTML = `
    <div class="annotation-layout">
      <div>
        <div class="card" style="margin-bottom:16px">
          <div style="font-size:.8rem;color:var(--gray-500);margin-bottom:8px;font-weight:600">文本（选中文字后选择标签）</div>
          <div class="annotation-content-card ner-text" id="ner-text-area" onmouseup="handleNERSelection()">${escHtml(item.content.text || '')}</div>
        </div>
        <div class="card">
          <div style="font-size:.85rem;font-weight:600;margin-bottom:8px">已标注实体</div>
          <div id="ner-entities-list"></div>
        </div>
      </div>
      <div>
        <div class="card" style="margin-bottom:16px">
          <div style="font-size:.85rem;font-weight:600;margin-bottom:8px">实体类型</div>
          <div class="label-grid">
            ${window._nerLabels.map(l => `
              <button class="label-btn" id="ner-label-${l}" onclick="selectNERLabel('${escHtml(l)}')">${escHtml(l)}</button>
            `).join('')}
          </div>
          <div style="font-size:.8rem;color:var(--gray-400);margin-top:8px">选中文字后点击标签</div>
        </div>
        <div class="card" style="margin-bottom:16px">
          <div class="form-group">
            <label>标注人</label>
            <input type="text" id="annotator" placeholder="你的名字" value="${item.annotator || ''}">
          </div>
        </div>
        <button class="btn btn-primary" onclick="submitAnnotation('ner')">✓ 保存标注</button>
      </div>
    </div>
  `;
  renderNEREntities();
}

window._nerSelection = null;
window._nerSelectedLabel = null;

window.handleNERSelection = function () {
  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0 || sel.isCollapsed) return;
  const text = sel.toString().trim();
  if (!text) return;
  window._nerSelection = { text, start: 0, end: 0 };
  const range = sel.getRangeAt(0);
  window._nerSelectionRange = range;
};

window.selectNERLabel = function (label) {
  window._nerSelectedLabel = label;
  document.querySelectorAll('.label-btn').forEach(b => b.classList.remove('selected'));
  document.getElementById(`ner-label-${label}`)?.classList.add('selected');

  if (window._nerSelection) {
    const sel = window.getSelection();
    if (sel && !sel.isCollapsed) {
      const text = sel.toString().trim();
      if (text) {
        window._nerEntities.push({ text, label });
        window._nerSelection = null;
        sel.removeAllRanges();
        renderNEREntities();
      }
    }
  }
};

function renderNEREntities() {
  const list = document.getElementById('ner-entities-list');
  if (!list) return;
  if (!window._nerEntities.length) {
    list.innerHTML = '<p style="color:var(--gray-400);font-size:.85rem">暂无已标注实体</p>';
    return;
  }
  list.innerHTML = window._nerEntities.map((e, i) => `
    <div style="display:flex;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--gray-100)">
      <div>
        <span style="font-size:.9rem">${escHtml(e.text)}</span>
        <span class="badge badge-primary" style="margin-left:6px;font-size:.7rem">${escHtml(e.label)}</span>
      </div>
      <button class="btn btn-sm btn-danger-outline" onclick="removeNEREntity(${i})">×</button>
    </div>
  `).join('');
}

window.removeNEREntity = function (idx) {
  window._nerEntities.splice(idx, 1);
  renderNEREntities();
};

/* ----- Submit Annotation ----- */
window.submitAnnotation = async function (type) {
  const item = _annotateState.items[_annotateState.currentIndex];
  const annotator = document.getElementById('annotator')?.value.trim() || 'anonymous';
  let annotation = {};

  if (type === 'classification') {
    if (!window._selectedLabel) { toast('请选择一个标签', 'error'); return; }
    annotation = { label: window._selectedLabel, note: document.getElementById('annotation-note')?.value || '' };
  } else if (type === 'qa') {
    const ans = document.getElementById('qa-answer')?.value.trim();
    if (!ans) { toast('请填写答案', 'error'); return; }
    annotation = { answer: ans };
  } else if (type === 'instruction') {
    const out = document.getElementById('inst-output')?.value.trim();
    if (!out) { toast('请填写输出', 'error'); return; }
    annotation = { output: out };
  } else if (type === 'generation') {
    const out = document.getElementById('gen-output')?.value.trim();
    if (!out) { toast('请填写生成内容', 'error'); return; }
    annotation = { output: out };
  } else if (type === 'ner') {
    annotation = { entities: window._nerEntities };
  }

  try {
    const updated = await API.post(
      `/api/datasets/${_annotateState.datasetId}/items/${item.id}/annotate`,
      { annotation, annotator }
    );
    _annotateState.items[_annotateState.currentIndex] = updated;
    toast('标注已保存', 'success');
    // Auto-advance to next pending
    const nextPending = _annotateState.items.findIndex((it, i) => i > _annotateState.currentIndex && it.status === 'pending');
    if (nextPending !== -1) {
      _annotateState.currentIndex = nextPending;
    } else if (_annotateState.currentIndex < _annotateState.items.length - 1) {
      _annotateState.currentIndex++;
    }
    renderAnnotateUI(document.getElementById('main-content'));
  } catch (e) { toast(e.message, 'error'); }
};

window.annotateNav = function (dir) {
  _annotateState.currentIndex = Math.max(0, Math.min(_annotateState.items.length - 1, _annotateState.currentIndex + dir));
  renderAnnotateUI(document.getElementById('main-content'));
};

window.reviewItem = async function (approved) {
  const item = _annotateState.items[_annotateState.currentIndex];
  try {
    await API.post(`/api/datasets/${_annotateState.datasetId}/items/${item.id}/review?approved=${approved}`);
    item.status = approved ? 'reviewed' : 'rejected';
    toast(approved ? '已通过审核' : '已拒绝', approved ? 'success' : 'error');
    renderAnnotateUI(document.getElementById('main-content'));
  } catch (e) { toast(e.message, 'error'); }
};

/* ===== Utilities ===== */
function escHtml(str) {
  if (typeof str !== 'string') str = String(str ?? '');
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function fmtDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
}

function itemSummary(content) {
  if (!content) return '';
  if (typeof content === 'string') return content.slice(0, 60);
  return (content.text || content.prompt || content.instruction || content.question || JSON.stringify(content)).slice(0, 60);
}
