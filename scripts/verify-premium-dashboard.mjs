import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const dashboardPath = path.resolve(import.meta.dirname, '..', 'premium-dashboard.html');
const html = fs.readFileSync(dashboardPath, 'utf8');
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map(match => match[1]);
assert.equal(scripts.length, 1, 'dashboard must keep one inline script');

const storage = new Map();
const createElement = () => ({
  className: '', textContent: '', innerHTML: '', value: '', checked: false,
  style: {}, dataset: {}, classList: { add() {}, remove() {}, toggle() {} },
  addEventListener() {}, appendChild() {}, setAttribute() {}, removeAttribute() {}
});
const sandbox = {
  console,
  atob: value => Buffer.from(value, 'base64').toString('utf8'),
  crypto: { randomUUID: () => 'test-id' },
  localStorage: {
    failKey: '',
    get length() { return storage.size; },
    key(index) { return [...storage.keys()][index] ?? null; },
    getItem(key) { return storage.get(String(key)) ?? null; },
    setItem(key, value) { if (this.failKey === String(key)) throw new Error('quota'); storage.set(String(key), String(value)); },
    removeItem(key) { storage.delete(String(key)); }
  },
  navigator: { onLine: true },
  document: { querySelector: () => createElement(), querySelectorAll: () => [], createElement, body: createElement() },
  window: { scrollTo() {} },
  AbortController,
  setTimeout,
  clearTimeout
};
sandbox.globalThis = sandbox;

const exportApi = `
globalThis.__dashboardTestApi = {
  safeJsonParse,
  authSession: typeof authSession === 'object' ? authSession : undefined,
  parseJwtPayload: typeof parseJwtPayload === 'function' ? parseJwtPayload : undefined,
  scopedLocalKey: typeof scopedLocalKey === 'function' ? scopedLocalKey : undefined,
  dashboardResumePayload: typeof dashboardResumePayload === 'function' ? dashboardResumePayload : undefined,
  dashboardResumeFromApi: typeof dashboardResumeFromApi === 'function' ? dashboardResumeFromApi : undefined,
  saveLocal,
  saveLocalBatch,
  maskSensitiveText,
  filterJobs,
  reorderByIds: typeof reorderByIds === 'function' ? reorderByIds : undefined,
  maskTextExport: typeof maskTextExport === 'function' ? maskTextExport : undefined,
  cleanupOldDrafts: typeof cleanupOldDrafts === 'function' ? cleanupOldDrafts : undefined,
  cleanupExpiredDeliveries: typeof cleanupExpiredDeliveries === 'function' ? cleanupExpiredDeliveries : undefined,
  calendarMonthDays: typeof calendarMonthDays === 'function' ? calendarMonthDays : undefined,
  interviewNotesKey: typeof interviewNotesKey === 'function' ? interviewNotesKey : undefined,
  compareAssessments: typeof compareAssessments === 'function' ? compareAssessments : undefined,
  assessmentPlanningText: typeof assessmentPlanningText === 'function' ? assessmentPlanningText : undefined,
  validateShortcuts: typeof validateShortcuts === 'function' ? validateShortcuts : undefined,
  deliveryStats: typeof deliveryStats === 'function' ? deliveryStats : undefined,
  mergeRestoredExtension: typeof mergeRestoredExtension === 'function' ? mergeRestoredExtension : undefined,
  removeEvidenceAttachments: typeof removeEvidenceAttachments === 'function' ? removeEvidenceAttachments : undefined,
  refreshVipStatus: typeof refreshVipStatus === 'function' ? refreshVipStatus : undefined,
  refreshOrders: typeof refreshOrders === 'function' ? refreshOrders : undefined,
  defaultPromotionTracks: typeof defaultPromotionTracks === 'function' ? defaultPromotionTracks : undefined,
  normalizeCareerPlan: typeof normalizeCareerPlan === 'function' ? normalizeCareerPlan : undefined,
  projectCareerPlanForCurrentVip: typeof projectCareerPlanForCurrentVip === 'function' ? projectCareerPlanForCurrentVip : undefined,
  calculatePlanProgress: typeof calculatePlanProgress === 'function' ? calculatePlanProgress : undefined,
  careerPlanTaskGroups: typeof careerPlanTaskGroups === 'function' ? careerPlanTaskGroups : undefined,
  appendCareerPlanTask: typeof appendCareerPlanTask === 'function' ? appendCareerPlanTask : undefined,
  deleteCareerPlanTask: typeof deleteCareerPlanTask === 'function' ? deleteCareerPlanTask : undefined,
  buildGapEvidenceDraft: typeof buildGapEvidenceDraft === 'function' ? buildGapEvidenceDraft : undefined,
  careerPlanText: typeof careerPlanText === 'function' ? careerPlanText : undefined,
  requestCareerPlan: typeof requestCareerPlan === 'function' ? requestCareerPlan : undefined,
  buildResumeExport: typeof buildResumeExport === 'function' ? buildResumeExport : undefined,
  buildCareerReportMarkdown: typeof buildCareerReportMarkdown === 'function' ? buildCareerReportMarkdown : undefined,
  buildDeliveryMarkdown: typeof buildDeliveryMarkdown === 'function' ? buildDeliveryMarkdown : undefined,
  fuzzyIncludes: typeof fuzzyIncludes === 'function' ? fuzzyIncludes : undefined,
  collectCurrentUserBackup: typeof collectCurrentUserBackup === 'function' ? collectCurrentUserBackup : undefined,
  openDraft: typeof openDraft === 'function' ? openDraft : undefined,
  saveDraft: typeof saveDraft === 'function' ? saveDraft : undefined,
  loadUserScopedState: typeof loadUserScopedState === 'function' ? loadUserScopedState : undefined,
  state
};`;
const source = scripts[0].replace(/\n\s*initialize\(\);\s*$/, exportApi);
assert.doesNotThrow(() => new Function(source), 'inline script must compile');
vm.runInNewContext(source, sandbox, { filename: 'premium-dashboard.inline.js' });

const api = sandbox.__dashboardTestApi;
assert.equal(api.safeJsonParse('{"ok":true}', null).ok, true);
assert.equal(api.safeJsonParse('{', 'fallback'), 'fallback');
assert.equal(typeof api.parseJwtPayload, 'function', 'JWT payload parser must exist');
assert.equal(typeof api.scopedLocalKey, 'function', 'user cache-key resolver must exist');
assert.equal(typeof api.authSession, 'object', 'auth session manager must exist');
assert.equal(typeof api.dashboardResumePayload, 'function', 'dashboard draft payload adapter must exist');
assert.equal(typeof api.dashboardResumeFromApi, 'function', 'dashboard draft response adapter must exist');
const dashboardResume = { name: 'Alice Chen', phone: '13800000000', email: 'alice@example.com', city: 'Shanghai', role: 'Data Analyst', skills: 'SQL, Python', summary: 'Evidence-led analyst', project: 'Retail metrics project', version: 'Campus', filename: 'alice-resume' };
const backendResume = api.dashboardResumePayload(dashboardResume);
assert.equal(backendResume.basic.name, 'Alice Chen');
assert.equal(backendResume.job.target_role, 'Data Analyst');
assert.deepEqual(Array.from(backendResume.skills.skills), ['SQL', 'Python']);
assert.equal(api.dashboardResumeFromApi(backendResume).project, 'Retail metrics project');
const testJwt = `header.${Buffer.from(JSON.stringify({ sub: 'user-42', token_version: 1, exp: 9999999999 })).toString('base64url')}.signature`;
api.authSession.set(testJwt);
assert.equal(api.authSession.userId(), 'user-42');
assert.equal(api.scopedLocalKey('resume-dashboard-evidence'), 'resume-dashboard:user-42:evidence');
api.saveLocal('resume-dashboard-evidence', [{ id: 42 }]);
assert.equal(sandbox.localStorage.getItem('resume-dashboard:user-42:evidence'), JSON.stringify([{ id: 42 }]));
api.authSession.clear();
assert.equal(api.scopedLocalKey('resume-dashboard-evidence'), null);
assert.equal(api.saveLocalBatch([['batch-one', { ok: true }], ['batch-two', { ok: true }]]), true);
sandbox.localStorage.failKey = 'batch-fail';
assert.equal(api.saveLocalBatch([['batch-restore', { changed: true }], ['batch-fail', { changed: true }]]), false);
assert.equal(sandbox.localStorage.getItem('batch-restore'), null);
sandbox.localStorage.failKey = '';
assert.equal(api.maskSensitiveText('13800000000', true), '138****0000');
assert.equal(api.maskSensitiveText('name@example.com', true), 'n***@example.com');
assert.deepEqual(
  api.filterJobs([
    { roleName: 'A', family: 'data', score: 80, salary: '10k-15k', city: 'Shanghai' },
    { roleName: 'B', family: 'product', score: 70, salary: '6k-8k', city: 'Hangzhou' }
  ], { salaryMin: '12', salaryMax: '', family: 'data', city: 'shang', difficulty: 'medium' }).map(item => item.roleName),
  ['A']
);
assert.equal(typeof api.reorderByIds, 'function', 'reorderByIds must exist for durable drag priorities');
assert.deepEqual(
  api.reorderByIds([{ id: 'a' }, { id: 'b' }, { id: 'c' }], ['c', 'a'], item => item.id).map(item => item.id),
  ['c', 'a', 'b']
);

assert.equal(typeof api.maskTextExport, 'function');
api.state.extension.maskSensitive = true;
api.state.resume = { name: 'Alice Chen', phone: '13800000000', email: 'alice@example.com' };
assert.equal(api.maskTextExport('Alice Chen 13800000000 alice@example.com'), 'A********n 138****0000 a***@example.com');
assert.equal(typeof api.cleanupOldDrafts, 'function');
assert.equal(typeof api.cleanupExpiredDeliveries, 'function');
api.state.drafts = [{ id: 'draft-1' }, { id: 'draft-2' }, { id: 'draft-3' }];
assert.equal(api.cleanupOldDrafts(2), 1);
assert.deepEqual(Array.from(api.state.drafts, item => item.id), ['draft-1', 'draft-2']);
api.state.deliveries = [{ id: 1, status: 'applied', nextActionAt: '2026-01-01' }, { id: 2, status: 'closed', nextActionAt: '2026-01-01' }, { id: 3, status: 'closed', nextActionAt: '2026-03-01' }];
assert.equal(api.cleanupExpiredDeliveries('2026-02-01'), 1);
assert.deepEqual(Array.from(api.state.deliveries, item => item.id), [1, 3]);
api.state.deliveries = [{ status: 'interview', appliedDate: '2026-02-01' }, { status: 'offer', appliedDate: '2026-02-02' }, { status: 'applied', appliedDate: '2026-02-03' }];
assert.equal(api.deliveryStats?.().interviewRate, 50);
assert.equal(api.deliveryStats?.().offerRate, 33);
assert.equal(typeof api.mergeRestoredExtension, 'function');
const mergedExtension = api.mergeRestoredExtension({ favoriteJobs: [{ roleName: 'Imported' }] }, { snapshots: [{ id: 'protect' }], backups: [{ id: 'export' }], favoriteJobs: [] });
assert.deepEqual(Array.from(mergedExtension.favoriteJobs, item => item.roleName), ['Imported']);
assert.deepEqual(JSON.parse(JSON.stringify(mergedExtension.snapshots)), [{ id: 'protect' }]);
assert.deepEqual(JSON.parse(JSON.stringify(mergedExtension.backups)), [{ id: 'export' }]);
assert.equal(typeof api.removeEvidenceAttachments, 'function');
api.state.extension.evidenceAttachments = { 1: [{ id: 'file' }], 2: [{ id: 'keep' }] };
api.removeEvidenceAttachments([1]);
assert.deepEqual(JSON.parse(JSON.stringify(api.state.extension.evidenceAttachments)), { 2: [{ id: 'keep' }] });
assert.deepEqual(Array.from(api.calendarMonthDays?.(2026, 1).slice(0, 3) || []), [1, 2, 3]);
assert.equal(api.interviewNotesKey?.('delivery-1', 2), 'delivery-1:2');
assert.equal(JSON.stringify(api.compareAssessments?.({ score: 80 }, { score: 70 })), JSON.stringify({ scoreDelta: 10, roles: [[], []] }));
assert.match(api.assessmentPlanningText?.({ action_plan: {} }) || '', /职业规划/);
assert.equal(api.validateShortcuts?.({ save: 's', export: 's' }), '快捷键不能重复');
assert.equal(typeof api.normalizeCareerPlan, 'function', 'career plan normalizer must exist');
assert.equal(typeof api.defaultPromotionTracks, 'function', 'career plan fallback tracks must exist');
assert.equal(typeof api.projectCareerPlanForCurrentVip, 'function', 'career plan must project cached detail to the current membership entitlement');
assert.equal(typeof api.calculatePlanProgress, 'function', 'career plan progress helper must exist');
assert.equal(typeof api.careerPlanTaskGroups, 'function', 'career plan task groups must exist');
assert.equal(typeof api.appendCareerPlanTask, 'function', 'roadmap task append helper must exist');
assert.equal(typeof api.buildGapEvidenceDraft, 'function', 'evidence draft helper must exist');
assert.equal(typeof api.careerPlanText, 'function', 'career plan copy helper must exist');
assert.equal(typeof api.requestCareerPlan, 'function', 'career plan API wrapper must exist');
const normalizedCareerPlan = api.normalizeCareerPlan({
  role_name: 'Data Engineer',
  action_plan: { seven_day: ['Review skills'], thirty_day: [], ninety_day: [] }
});
assert.equal(normalizedCareerPlan.sections.length, 6, 'career plan must always normalize six report sections');
assert.deepEqual(Array.from(normalizedCareerPlan.promotion_tracks, track => track.key), ['technical', 'management']);
assert.deepEqual(
  Array.from(api.defaultPromotionTracks('Data Engineer')[0].nodes, node => node.level),
  ['entry', 'junior', 'mid', 'senior'],
  'the technical fallback must render all four roadmap stages'
);
assert.equal(api.defaultPromotionTracks('Data Engineer')[1].nodes.length, 4, 'the management fallback must render all four roadmap stages');
assert.equal(api.calculatePlanProgress([{ done: true }, { done: false }]), 50);
assert.equal(api.calculatePlanProgress([]), 0);
api.state.vip = { vip_level: 'free' };
const downgradedPlan = api.projectCareerPlanForCurrentVip({
  role_name: 'Data Engineer', report_scope: 'detailed',
  sections: [{ key: 'market_overview', title: 'Market', summary: 'Paid detail', items: ['Paid-only item'] }],
  comparison_items: [{ competency: 'SQL', category: 'hard', status: 'high', evidence: ['Private detail'], gap: 'Paid gap', recommendation: 'Paid recommendation' }],
  promotion_tracks: [{ key: 'technical', title: 'Technical', nodes: [{ title: 'Engineer', level: 'junior', description: 'Paid detail', salary_band: '20k', standard_years: '3 years', competencies: ['SQL'], case_detail: 'Paid case' }] }],
  action_plan: { seven_day: ['Keep seven-day action'], thirty_day: ['Paid 30-day action'], ninety_day: ['Paid 90-day action'] }
});
assert.equal(downgradedPlan.report_scope, 'brief');
assert.equal(downgradedPlan.sections[0].items.length, 0, 'downgraded cached plans must not retain detailed section items');
assert.equal(downgradedPlan.comparison_items[0].evidence.length, 0, 'downgraded cached plans must not retain detailed comparison evidence');
assert.equal(downgradedPlan.promotion_tracks.length, 1, 'downgraded cached plans must only expose the brief technical track');
assert.deepEqual(Array.from(downgradedPlan.promotion_tracks[0].nodes[0].competencies), [], 'downgraded cached plans must not retain paid roadmap competencies');
assert.deepEqual(Array.from(downgradedPlan.action_plan.thirty_day), [], 'downgraded cached plans must not retain 30-day actions');
api.state.vip = { vip_level: 'basic' };
const taskGroups = api.careerPlanTaskGroups({ role_name: 'Data Engineer', action_plan: { seven_day: ['Review skills'], thirty_day: ['Build portfolio'], ninety_day: ['Run interview retrospective'] } });
assert.deepEqual(Array.from(taskGroups, group => group.key), ['seven_day', 'thirty_day', 'ninety_day']);
assert.equal(taskGroups.flatMap(group => group.tasks).length, 3, '7/30/90 tasks must render as individual progress items');
assert.equal(taskGroups[0].tasks[0].done, false);
const appendedCareerTask = api.appendCareerPlanTask({ role_name: 'Data Engineer', action_plan: { seven_day: [], thirty_day: [], ninety_day: [] } }, 'thirty_day', 'Complete a portfolio case study');
assert.deepEqual(Array.from(appendedCareerTask.action_plan.thirty_day), ['Complete a portfolio case study']);
assert.equal(api.appendCareerPlanTask(appendedCareerTask, 'thirty_day', 'Complete a portfolio case study').action_plan.thirty_day.length, 1, 'roadmap tasks must not duplicate');
assert.equal(typeof api.deleteCareerPlanTask, 'function', 'career plan tasks must support deletion');
const retainedProgressPlan = api.normalizeCareerPlan({ role_name: 'Progress Role', action_plan: { seven_day: ['Finish brief', 'Review evidence'], thirty_day: [], ninety_day: [] } });
api.state.careerPlans = { 'Progress Role': retainedProgressPlan };
api.state.careerPlanProgress = { 'Progress Role': { 'seven_day:0:Finish brief': { done: true }, 'seven_day:1:Review evidence': { done: false } } };
assert.equal(api.deleteCareerPlanTask('Progress Role', { id: 'seven_day:0:Finish brief', phase: 'seven_day', index: 0 }), true);
assert.deepEqual(Array.from(api.state.careerPlans['Progress Role'].action_plan.seven_day), ['Review evidence']);
assert.equal(api.state.careerPlanProgress['Progress Role']['seven_day:0:Review evidence'].done, false, 'deleting a task must preserve the remaining task progress');
const gapEvidence = api.buildGapEvidenceDraft('SQL');
assert.match(gapEvidence.title, /待确认/);
assert.deepEqual(Array.from(gapEvidence.tags), ['SQL']);
assert.equal(gapEvidence.status, 'pending');
assert.equal(typeof api.buildResumeExport, 'function', 'native resume export content builder must exist');
assert.equal(typeof api.buildCareerReportMarkdown, 'function', 'career report export builder must exist');
assert.equal(typeof api.buildDeliveryMarkdown, 'function', 'delivery markdown export builder must exist');
assert.equal(typeof api.fuzzyIncludes, 'function', 'global search must support fuzzy matching');
assert.equal(typeof api.collectCurrentUserBackup, 'function', 'current user local backup collector must exist');
api.state.extension.maskSensitive = false;
const exportedResume = api.buildResumeExport({ name: 'Alice Chen', role: 'Data Analyst', email: '', skills: 'SQL, Python', project: 'Retail reporting' }, 'markdown');
assert.match(exportedResume, /# Alice Chen/);
assert.match(exportedResume, /SQL, Python/);
assert.doesNotMatch(exportedResume, /邮箱：/);
const exportedCareerReport = api.buildCareerReportMarkdown({ role_name: 'Data Engineer', sections: [{ title: '行业概览', summary: '需求稳定', items: ['看重数据质量'] }], promotion_tracks: [], comparison_items: [], action_plan: { seven_day: ['完善项目'], thirty_day: [], ninety_day: [] } });
assert.match(exportedCareerReport, /# Data Engineer 职业规划报告/);
assert.match(exportedCareerReport, /行业概览/);
assert.match(exportedCareerReport, /7 天行动/);
const exportedDeliveries = api.buildDeliveryMarkdown([{ company: 'Acme', roleName: 'Analyst', appliedDate: '2026-08-01', status: 'applied', notes: 'Follow up' }]);
assert.match(exportedDeliveries, /\| 公司 \| 岗位/);
assert.match(exportedDeliveries, /Acme/);
assert.equal(api.fuzzyIncludes('Data Engineer', 'dt eng'), true);
api.authSession.set(testJwt);
const collectedBackup = api.collectCurrentUserBackup();
assert.equal(collectedBackup.cacheOwner, 'user-42');
assert.equal(collectedBackup.format, 'resume-dashboard-local-backup');
assert.match(html, /function attachSortable\b/);
assert.match(html, /data-draft-sort/);
assert.match(html, /data-favorite-sort/);
assert.match(html, /data-template-section/);
assert.match(html, /data-evidence-batch-check/);
assert.match(html, /function renderMonthlyDeliveryCalendar\b/);
assert.match(html, /function openChangelog\b/);
assert.match(html, /footer\.id\s*=\s*"releaseFooter"/);
assert.match(html, /面试通过率/);
assert.match(html, /openEvidenceOrganizerToolbarBtn/);
assert.match(html, /items\.length && isExpiredDate\(date\)/);
assert.match(html, /图片附件未保存，请释放本地空间后重试/);
assert.match(html, /function saveLocalBatch\b/);
assert.match(html, /id="loginBtn"/);
assert.match(html, /Authorization\s*=\s*`Bearer \$\{authSession\.token\}`/);
assert.match(html, /resume-dashboard:\$\{userId\}:\$\{String\(key\)/);
assert.match(html, /id="vipStatusBtn"/, 'top navigation must display the current membership tier');
assert.match(html, /data-page="membership"/, 'membership purchase page must be reachable from navigation');
assert.match(html, /data-page="orders"/, 'order history page must be reachable from navigation');
assert.match(html, /\/api\/user\/vip-info/, 'dashboard must load the server membership status');
assert.match(html, /\/api\/pay\/package-list/, 'dashboard must load server packages');
assert.match(html, /\/api\/pay\/create-order/, 'dashboard must create an order before checkout');
assert.match(html, /\/api\/pay\/callback/, 'dashboard must complete demo payment through the API');
assert.match(html, /\/api\/user\/order-list/, 'dashboard must load current-user order history');
assert.match(html, /resume-dashboard-vip-status/, 'membership cache must be JWT-user scoped');
assert.match(html, /function requireVipFeature\b/, 'restricted actions must have a shared membership interceptor');
assert.match(html, /function openMembershipModal\b/, 'privilege errors must open a membership guide');
assert.match(html, /vip_required/, 'API privilege responses must be handled without clearing a valid login');
assert.match(html, /\/api\/job\/plan/, 'dashboard must request the authenticated structured career plan');
assert.match(html, /resume-dashboard-career-plan-cache/, 'career-plan cache must be JWT-user scoped');
assert.match(html, /resume-dashboard-career-plan-progress/, 'career-plan task progress must be JWT-user scoped');
assert.match(html, /resume-dashboard-career-plan-history/, 'career-plan comparison history must be JWT-user scoped');
assert.match(html, /function renderCareerPlanCard\b/, 'each Sprint/Safe/Backup card must render the detailed plan');
assert.match(html, /data-career-plan-refresh/, 'plan cards must allow an explicit detailed generation request');
assert.match(html, /data-career-track/, 'plan cards must switch between technical and management tracks');
assert.match(html, /data-roadmap-node/, 'promotion roadmap nodes must be interactive');
assert.match(html, /data-career-plan-task/, '7/30/90 tasks must persist completion interactions');
assert.match(html, /data-open-career-comparison/, 'each plan card must open the personal competency comparison');
assert.match(html, /data-add-gap-evidence/, 'missing competencies must create a pending evidence draft');
assert.match(html, /career-comparison-grid/, 'comparison modal must use a responsive two-column layout');
assert.match(html, /career-plan-task-groups/, '7/30/90 tasks must use dedicated progress blocks');
assert.match(html, /id="resumeExportMenu"/, 'resume editor must expose native local export choices');
assert.match(html, /id="exportCareerReportBtn"/, 'career planning must expose a full report export action');
assert.match(html, /id="exportDeliveryMarkdownBtn"/, 'delivery list must support filtered Markdown export');
assert.match(html, /data-user-menu="data-manager"/, 'top user menu must reach local data management');
assert.match(html, /id="quickAssistBtn"/, 'resume and career planning must expose a quick prompt assistant');
assert.match(html, /data-career-task-action/, 'career plan tasks must support edit and delete actions');
assert.match(html, /#page-jobs > \.card:has\(\.job-suggestions:not\(\.hidden\)\)/, 'open job suggestions must elevate above candidate cards');
assert.match(html, /insight-signal-grid/, 'annual employment insights must expose structured market signals');
assert.match(html, /insight-action-panel/, 'annual employment insights must include actionable planning guidance');
assert.match(html, /aria-labelledby="modalTitle"/, 'modal dialog must expose its accessible title');
assert.match(html, /id="toast" role="status" aria-live="polite"/, 'toast messages must announce non-blocking status changes');
assert.doesNotMatch(html, /location\.protocol\s*===\s*["']file:/, 'file:// Mock export branch must be removed');
assert.match(html, /id="sidebarMask"/, 'mobile navigation must provide an immediate close mask');
assert.match(html, /function setSidebarOpen\b/, 'mobile navigation must use one state transition helper');
assert.match(html, /\.sidebar-mask\.open/, 'mobile navigation mask must receive the visible state');
assert.match(html, /isOpen && window\.matchMedia\("\(max-width: 900px\)"\)\.matches/, 'desktop sidebar shortcuts must not lock document scrolling');
assert.match(html, /\.topbar \{ align-items: flex-start; flex-wrap: wrap; padding: 14px (?:28px|var\(--content-gutter-compact\)); \}/, 'tablet topbar must wrap before its action controls overflow');
assert.match(html, /function installOverflowTooltips\b/, 'truncated interactive text must expose an on-demand tooltip');
assert.match(html, /target\.scrollWidth <= target\.clientWidth/, 'tooltip detection must only run for actual text overflow');
for (const visualHook of [
  '--radius-sm:', '--radius-md:', '--radius-lg:', '--shadow-card:', '--shadow-hover:', '--shadow-modal:',
  '--type-page:', '--type-module:', '--type-card:', '--type-body:', '--type-hint:', '--type-tag:',
  '.btn:active', ':focus-visible', 'prefers-reduced-motion: reduce', 'backdrop-filter: blur(1px)',
  'tbody tr:hover', 'scrollbar-color:', '::selection'
]) {
  assert.ok(html.includes(visualHook), `dashboard must keep the shared visual hook: ${visualHook}`);
}

const firstAccountJwt = `header.${Buffer.from(JSON.stringify({ sub: 'owner-a', token_version: 1, exp: 9999999999 })).toString('base64url')}.signature`;
const secondAccountJwt = `header.${Buffer.from(JSON.stringify({ sub: 'owner-b', token_version: 1, exp: 9999999999 })).toString('base64url')}.signature`;
api.authSession.set(firstAccountJwt);
api.state.vip = { vip_level: 'free', expire_time: null, auto_renew: false, max_drafts: 3, max_compare_jobs: 2 };
let resolveVipRequest;
sandbox.fetch = () => new Promise(resolve => { resolveVipRequest = () => resolve({ ok: true, status: 200, json: async () => ({ code: 'ok', data: { vip_level: 'premium', expire_time: '2030-01-01T00:00:00+00:00', auto_renew: false, max_drafts: null, max_compare_jobs: 4 } }) }); });
const pendingVip = api.refreshVipStatus();
api.authSession.set(secondAccountJwt);
await Promise.resolve();
resolveVipRequest();
await pendingVip;
assert.equal(api.state.vip.vip_level, 'free', 'a delayed VIP response must not overwrite a different account');
assert.equal(sandbox.localStorage.getItem('resume-dashboard:owner-b:vip-status'), null, 'a delayed VIP response must not be cached for a different account');

api.state.orders = [];
let resolveOrdersRequest;
sandbox.fetch = () => new Promise(resolve => { resolveOrdersRequest = () => resolve({ ok: true, status: 200, json: async () => ({ code: 'ok', data: { items: [{ order_id: 'owner-b-order', payment_status: 'paid' }] } }) }); });
const pendingOrders = api.refreshOrders();
api.authSession.set(firstAccountJwt);
await Promise.resolve();
resolveOrdersRequest();
await pendingOrders;
assert.deepEqual(Array.from(api.state.orders), [], 'a delayed order response must not appear for a different account');

api.authSession.set(firstAccountJwt);
api.state.careerPlans = {};
let resolveCareerPlanRequest;
sandbox.fetch = () => new Promise(resolve => { resolveCareerPlanRequest = () => resolve({ ok: true, status: 200, json: async () => ({ code: 'ok', data: { role_name: 'Data Engineer', report_scope: 'detailed', action_plan: { seven_day: ['A-only action'], thirty_day: [], ninety_day: [] } } }) }); });
const pendingCareerPlan = api.requestCareerPlan('Data Engineer', true);
api.authSession.set(secondAccountJwt);
await Promise.resolve();
resolveCareerPlanRequest();
await pendingCareerPlan;
assert.deepEqual(Object.keys(api.state.careerPlans), [], 'a delayed career plan must not enter another account state');
assert.equal(sandbox.localStorage.getItem('resume-dashboard:owner-b:career-plan-cache'), null, 'a delayed career plan must not enter another account cache');

api.state.drafts = [{ id: 'existing-draft', title: 'Existing', template: 'business', resume: { ...dashboardResume } }];
api.state.resumeDirty = false;
api.openDraft('existing-draft');
assert.equal(api.state.activeDraftId, 'existing-draft', 'opening a draft must retain its ID for the next save');
let savedDraftId;
sandbox.fetch = (_url, options) => {
  savedDraftId = JSON.parse(options.body).id;
  return Promise.resolve({ ok: true, status: 200, json: async () => ({ code: 'ok', data: { id: 'existing-draft' } }) });
};
await api.saveDraft();
assert.equal(savedDraftId, 'existing-draft', 'saving an opened draft must update it rather than create a new draft');
api.state.activeDraftId = 'existing-draft';
api.loadUserScopedState();
assert.equal(api.state.activeDraftId, null, 'switching account storage must clear the active draft ID');

console.log('premium dashboard contract checks passed');
